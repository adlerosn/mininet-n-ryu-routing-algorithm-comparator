#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os
import sys
import json
import pulp
import numpy
import random
import datetime
import threading
from sortundirectednodepair import _sort_pair
from graphtools import Dijkstra, find_all_paths, graph_from_topo
from time import sleep
from io import StringIO
from id2ip import id2ip, ip2id
from typing import Any
from typing import Union
from typing import Tuple
from typing import List
from typing import Dict
from typing import Optional
from configparser import ConfigParser
from ryu.lib import hub
from ryu.base import app_manager
from ryu.lib import ofctl_v1_3
from ryu.lib.packet import ether_types
from ryu.lib.packet import ethernet
from ryu.ofproto import ofproto_v1_3
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller import ofp_event
from ryu.lib.packet import packet
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor

NEG_INF = float('-inf')
MIN_POSITIVE_FLOAT = numpy.nextafter(0, 1)

EMPTY_ITER = iter(list())

SPEED_KILOBIT = 0.001
SPEED_MEGABIT = 1
SPEED_GIGABIT = 1000
SPEED_TERABIT = 1000000

UNLIMITED_BANDWIDTH = 70*SPEED_TERABIT

NoneType = type(None)

print(f"loading network {sys.argv[2]}", file=sys.stderr)
network_topo = ''
with open(sys.argv[2]) as f:
    network_topo = json.loads(f.read())
# ryu uses eventlet, which, on some versions, breaks pathlib's read_text

base_net_name = '.'.join(sys.argv[2].split('.')[:-1])

with open('~current.state', 'w') as f:
    f.write(base_net_name)

with open('~current.sws.state', 'w') as f:
    f.write("")

if os.path.exists(f'{base_net_name}.state'):
    os.unlink(f'{base_net_name}.state')

print(f"reading network configuration variables.ini", file=sys.stderr)
network_config = ConfigParser()
with open('variables.ini') as f:
    network_config.read_string(f.read())

m1 = float(network_config['linearalgconst']['m1'])
m2 = float(network_config['linearalgconst']['m2'])
hop_delay = float(network_config['linearalgconst']['hop_delay'])
apa_path_stretch = float(network_config['APA']['path_stretch'])
routing_algo = network_config['GENERAL']['algo']

network_graph = graph_from_topo(network_topo)


def jsonload_list2tuple(x):
    if isinstance(x, type(None)) or isinstance(x, int) or isinstance(x, float) or isinstance(x, str):
        return x
    elif isinstance(x, list) or isinstance(x, tuple):
        return tuple([jsonload_list2tuple(k) for k in x])
    elif isinstance(x, dict):
        return {jsonload_list2tuple(k): jsonload_list2tuple(v) for k, v in x.items()}
    else:
        raise ValueError("Input didn't come from a standard JSON")


def prepare_pop_pair_alternative_paths_for_availability(graph, hosts):
    pop_apa = [[None for x in hosts] for y in hosts]
    for i, h1 in enumerate(hosts):
        for j, h2 in enumerate(hosts):
            if pop_apa[i][j] is None:
                apa = tuple(list(find_all_paths(graph, h1, h2)))
                pop_apa[i][j] = apa
                pop_apa[j][i] = apa
    return pop_apa


apacachefile = f"{base_net_name}.apa.json"
print(
    f"checking if APA for {sys.argv[2]} is cached at {apacachefile}", file=sys.stderr)

pop_apa_candidates = None
if os.path.isfile(apacachefile):
    print(f"loading APA from {apacachefile}", file=sys.stderr)
    with open(apacachefile) as f:
        pop_apa_candidates = jsonload_list2tuple(json.loads(f.read()))
else:
    print(f"calculating APA for {sys.argv[2]}", file=sys.stderr)
    pop_apa_candidates = prepare_pop_pair_alternative_paths_for_availability(
        network_graph,
        network_topo[0]
    )
    print(f"caching APA at {apacachefile}", file=sys.stderr)
    with open(apacachefile, 'w') as f:
        f.write(json.dumps(pop_apa_candidates))


def filter_out_invalid_paths_from_multiple_paths(h1, h2, candidates, sw=None):
    valid_paths = list()
    valid_paths_bits_rev = set()
    for path in sorted(
        candidates,
        key=lambda a: (len(a), a)
    ):
        if sw is not None and sw not in path:
            continue
        if path[0] == h2 and path[-1] == h1:
            path = list(reversed(path))
        path_bits = set([
            tuple(path[i:i+2])
            for i in range(len(path)-1)
        ])
        if len(path_bits.intersection(valid_paths_bits_rev)) <= 0:
            valid_paths.append(path)
            valid_paths_bits_rev = valid_paths_bits_rev.union(set([
                tuple(reversed(i))
                for i in path_bits
            ]))
    return valid_paths


class LatencyController:
    def __init__(self, datapath):
        super().__init__()
        self._datapath = datapath
        self._sw = f"s{self._datapath.id}"
        l = [
            (i, x) for i, x in enumerate(network_topo[2])
            if x[0] == self._sw or x[1] == self._sw
        ]
        self._l = l
        self._links = portno_from_list(l)
        self._flow_xfer = dict()
        self._flow_speed = dict()
        self._link_speed = UsageStoreProxyFromFlowDict(self._flow_speed)
        self._link_rules = usage_store_from_list(l)
        self._bandwidth = bandwidth_from_list(l)
        self._ospf = None

    def connected(self, la: 'LatencyApp'):
        print(f"Switch connected: {self._sw}")
        print(f"Switch OSPF-fallback loading: {self._sw}")
        parser = self._datapath.ofproto_parser
        self._ospf = la.ospf_dijkstra(self._sw)
        for h in network_topo[0]:
            ipv4_dst = id2ip(int(h[1:])-1)
            match_ipv4 = parser.OFPMatch(
                eth_type=0x0800,
                ipv4_dst=ipv4_dst
            )
            match_arp = parser.OFPMatch(
                eth_type=0x0806,
                arp_tpa=ipv4_dst
            )
            next_hop = self._ospf(h)[0][1]
            out_port = self._links[(self._sw, next_hop)]
            actions = [parser.OFPActionOutput(out_port)]
            print(f"{self._sw} --[{out_port}]--> {next_hop} ({ipv4_dst})")
            self.add_flow(1, match_ipv4, actions)
            self.add_flow(1, match_arp, actions)
        print(f"Switch OSPF-fallback loaded: {self._sw}")
        if routing_algo == 'ecmp':
            print(f"Switch ECMP setting up: {self._sw}")
            self._configureECMP(la)
            print(f"Switch ECMP set up: {self._sw}")
        hub.spawn(self._write_in_initialized_file)
        # self._write_in_initialized_file()
    
    def _write_in_initialized_file(self, retries=5):
        with initialized_switch_writing_lock:
            with open('~current.sws.state', 'a') as f:
                f.write(f"{self._sw}{os.linesep}")
        if retries>0:
            sleep(random.uniform(0.5, 2.5))
            self._write_in_initialized_file(retries-1)

    def disconnected(self):
        print(f"Switch disconnected: {self._sw}")

    def add_flow(self, priority, match, actions, buffer_id=None, idle_timeout=0, hard_timeout=0):
        ofproto = self._datapath.ofproto
        parser = self._datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS,
            actions
        )]
        additionals = dict()
        if buffer_id:
            additionals['buffer_id'] = buffer_id
        if idle_timeout:
            additionals['idle_timeout'] = idle_timeout
        if hard_timeout:
            additionals['hard_timeout'] = hard_timeout
        mod = parser.OFPFlowMod(datapath=self._datapath,
                                priority=priority, match=match,
                                instructions=inst,
                                **additionals)
        self._datapath.send_msg(mod)

    def _the_other_link_endpoint(self, linktuple):
        return linktuple[abs(linktuple.index(self._sw)-1)]

    def _on_stats(self, ev, la: 'LatencyApp'):
        self._link_rules = usage_store_from_list(self._l)
        parser = self._datapath.ofproto_parser
        stats = ev.msg.body
        allkeys = []
        for k in self._link_rules._pairs.keys():
            self._link_rules._pairs[k] = 0
        for stat in stats:
            # ltp -> link tuple
            # ftp -> flow tuple
            # bc  -> byte count
            # obc -> old byte count
            action = stat.instructions[0].actions[0]
            outs = list()
            if isinstance(action, parser.OFPActionGroup):
                weight_sum = sum([
                    bucket.weight
                    for bucket in la.ecmp_group_id_buckets[action.group_id]
                ])
                for bucket in la.ecmp_group_id_buckets[action.group_id]:
                    outs.append((
                        bucket.actions[0].port,
                        bucket.weight/max(1, weight_sum)
                    ))
            else:
                outs.append((action.port, 1))
            for out_port, weight in outs:
                ltps = self._links.reverse_lookup(out_port)
                if len(ltps) <= 0:
                    continue
                ltp = ltps[0]
                nxt = ltp[abs(ltp.index(self._sw)-1)]
                # measuring link flows
                self._link_rules[ltp] = 1+self._link_rules[ltp]
                # measuring load
                if stat.match['eth_type'] == 0x0800:
                    src = stat.match.get('ipv4_src', '10.0.0.0')
                    dst = stat.match['ipv4_dst']
                    src = f"h{ip2id(src)+1}"
                    dst = f"h{ip2id(dst)+1}"
                    if src == 'h0':
                        src = None
                    key = (src, self._sw, nxt, dst)
                    bc = stat.byte_count
                    obc = self._flow_xfer.get(key, 0)
                    tfd = max(0, bc-obc)*weight  # bytes per cycle
                    tfr = ((8*tfd)/la.interval)/10**6  # mbps
                    self._flow_xfer[key] = bc
                    self._flow_speed[key] = tfr
                    allkeys.append(key)
        for k in (set(self._flow_speed.keys())-set(allkeys)):
            self._flow_speed[k] = 0

    # with parts from <https://github.com/wildan2711/multipath/blob/master/ryu_multipath.py>
    # commented by <https://wildanmsyah.wordpress.com/2018/01/13/multipath-routing-with-load-balancing-using-ryu-openflow-controller/>
    def _configureECMP(self, la: 'LatencyApp'):
        ofproto = self._datapath.ofproto
        parser = self._datapath.ofproto_parser
        prints = list()
        for h1p, h1 in enumerate(network_topo[0]):
            for h2p, h2 in enumerate(network_topo[0]):
                if h1p != h2p:
                    ips = id2ip(int(h1[1:])-1)
                    ipd = id2ip(int(h2[1:])-1)
                    match = parser.OFPMatch(
                        eth_type=0x0800,
                        ipv4_src=ips,
                        ipv4_dst=ipd
                    )
                    valid_paths = filter_out_invalid_paths_from_multiple_paths(
                        h1,
                        h2,
                        pop_apa_candidates[h1p][h2p],
                        self._sw
                    )
                    portouts = list()
                    nexthops = list()
                    for path in valid_paths:
                        nexthop = (path[path.index(self._sw)+1], 1.0)
                        link = (self._sw, nexthop[0])
                        portout = self._links[link]
                        portouts.append(portout)
                        nexthops.append(nexthop[0])
                    portouts = list(set(portouts))
                    nexthops = list(set(nexthops))
                    prints.append(
                        f"({ips}) {self._sw} --{portouts}-> {set(nexthops)} ({ipd})"
                    )
                    if len(portouts) <= 0:
                        continue
                        # no output
                    elif len(portouts) == 1:
                        actions = [parser.OFPActionOutput(portouts[0])]
                        self.add_flow(7, match, actions)
                        # add simple rule
                    else:
                        all_bws = [x if x is not None else UNLIMITED_BANDWIDTH for x in [
                            network_topo[2][portout-1][2] for portout in portouts]]
                        sum_all_bws = sum(all_bws)
                        weighted_bws = [bw/sum_all_bws for bw in all_bws]
                        out_ports = list(zip(portouts, weighted_bws))
                        del weighted_bws
                        del sum_all_bws
                        del portouts
                        tpl = tuple([h1, self._sw, h2])
                        gnw = False
                        if tpl not in la.ecmp_group_ids:
                            la.ecmp_group_ids[tpl] = len(la.ecmp_group_ids)+1
                            gnw = True
                        gid = la.ecmp_group_ids[tpl]
                        buckets = []

                        for port, weight in out_ports:
                            bucket_weight = int(
                                round(
                                    65535 * min(
                                        1.0,
                                        max(
                                            0.0,
                                            (1 - weight)
                                        )
                                    )
                                )
                            )
                            bucket_action = [parser.OFPActionOutput(port)]
                            buckets.append(
                                parser.OFPBucket(
                                    weight=bucket_weight,
                                    watch_port=port,
                                    watch_group=ofproto.OFPG_ANY,
                                    actions=bucket_action
                                )
                            )

                        la.ecmp_group_id_buckets[gid] = buckets

                        req = parser.OFPGroupMod(
                            self._datapath,
                            ofproto.OFPGC_ADD if gnw else ofproto.OFPGC_MODIFY,
                            ofproto.OFPGT_SELECT,
                            gid,
                            buckets
                        )
                        self._datapath.send_msg(req)
                        # set group

                        actions = [parser.OFPActionGroup(gid)]
                        self.add_flow(7, match, actions)
                        # add rule
        print(os.linesep.join(prints))
        pass

    def add_latency_segment(self, ips: str, ipd: str, nxt: str, ignore_routing_algo: bool = False):
        if (routing_algo not in ['ldr', 'minmax']) and not ignore_routing_algo:
            return
        link = (self._sw, nxt)
        parser = self._datapath.ofproto_parser
        actions = [parser.OFPActionOutput(self._links[link])]
        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_src=ips,
            ipv4_dst=ipd
        )
        self.add_flow(5, match, actions)
        # hs = f"h{ip2id(ips)+1}"
        # hd = f"h{ip2id(ipd)+1}"
        # self._flow_xfer[(hs, hd, nxt)] = 0

    def add_weighted_latency(self, la: 'LatencyApp', ips: str, ipd: str, nxts: Dict[str, float]):
        if len(nxts) <= 0:
            return
        elif len(nxts) == 1:
            self.add_latency_segment(ips, ipd, list(nxts.keys())[0])
        else:
            ofproto = self._datapath.ofproto
            parser = self._datapath.ofproto_parser
            match = parser.OFPMatch(
                eth_type=0x0800,
                ipv4_src=ips,
                ipv4_dst=ipd
            )
            h1 = f"h{ip2id(ips)+1}"
            h2 = f"h{ip2id(ipd)+1}"

            out_ports = [
                (self._links[(self._sw, nexthop)], weight)
                for nexthop, weight in nxts.items()
            ]
            tpl = tuple([h1, self._sw, h2])
            gnw = False
            if tpl not in la.ecmp_group_ids:
                la.ecmp_group_ids[tpl] = len(la.ecmp_group_ids)+1
                gnw = True
            gid = la.ecmp_group_ids[tpl]
            buckets = []

            for port, weight in out_ports:
                bucket_weight = int(round(weight * 65535))
                bucket_action = [parser.OFPActionOutput(port)]
                buckets.append(
                    parser.OFPBucket(
                        weight=bucket_weight,
                        watch_port=port,
                        watch_group=ofproto.OFPG_ANY,
                        actions=bucket_action
                    )
                )

            la.ecmp_group_id_buckets[gid] = buckets

            req = parser.OFPGroupMod(
                self._datapath,
                ofproto.OFPGC_ADD if gnw else ofproto.OFPGC_MODIFY,
                ofproto.OFPGT_SELECT,
                gid,
                buckets
            )
            self._datapath.send_msg(req)
            # set group

            actions = [parser.OFPActionGroup(gid)]
            self.add_flow(5, match, actions)
            # add rule

    @property
    def simulatable(self):
        return SimulatableSwitch(
            self._sw,
            self._flow_speed.copy(),
            self._bandwidth.copy()
        )


class SimulatableSwitch:
    def __init__(self, sw: str, fs: dict, bw: 'UsageStore'):
        self._sw = sw
        self._flow_speed = fs
        self._bandwidth = bw
        self._link_speed = UsageStoreProxyFromFlowDict(self._flow_speed)
        self._reinit()

    def _reinit(self):
        self._link_rules = self.get_link_rules()

    def get_link_rules(self):
        cnt = UsageStore()
        for key, bw in self._flow_speed.items():
            if bw > 0:
                k = (key[1], key[2])
                cnt[k] = 1+cnt[k]
        return cnt

    @property
    def name(self):
        return self._sw

    def copy(self):
        return type(self)(
            self._sw,
            self._flow_speed.copy(),
            self._bandwidth.copy()
        )


class SimulatableNetwork:
    def __init__(self, sws: List[SimulatableSwitch], paths: 'UsageStore'):
        self.switches: Dict[str, SimulatableSwitch] = {
            sw._sw: sw
            for sw in sws
        }
        self.max_speed = bandwidth_from_list(enumerate(network_topo[2]))
        self.paths = paths
        self._reinit()

    def _reinit(self):
        self._flow_speed = DictAggregator(
            [sw._flow_speed for sw in self.switches.values()]
        )
        self.last_speed = UsageStoreProxyFromCallableIterable(
            AttrCallableIterable(
                AttrCallableIterable(
                    self.switches.values,
                    '_link_speed'
                ),
                'as_regular_storage'
            ),
            sum
        ).as_regular_storage
        self.link_usage = self.max_speed.calculate(
            self.last_speed.as_regular_storage,
            lambda maxspeed, lastspeed: (
                lastspeed / max(maxspeed, 0.0000000000001)
            )
        ).as_regular_storage
        self.link_flows = self.get_link_flows()

    def get_link_flows(self):
        cnt = UsageStore()
        for switch in self.switches.values():
            for (_, sw, nxt, __), speed in switch._flow_speed.items():
                key = (sw, nxt)
                if switch._bandwidth[key] > 0 and speed > 0:
                    cnt[key] = 1+cnt[key]
        return cnt

    def get_routes(self):
        return self.paths.copy()

    def get_path(self, h1, h2):
        return self.paths[(h1, h2)]

    def copy(self) -> 'SimulatableNetwork':
        return type(self)(
            [sw.copy() for sw in self.switches.values()],
            self.paths.copy()
        )

    def sort_by_max_flow_load(self, seqs):
        wl = list()
        for seq in seqs:
            if not isinstance(seq, WeightedPathAggregate):
                seq = WeightedPathAggregate({tuple(seq): 1.0})
            ml = self.get_max_flow_load(seq)
            wl.append((
                ml,
                sorted(seq.keys(), key=lambda a: len(a))[0],
                seq
            ))
        return list(map(
            lambda a: a[2],
            reversed(sorted(wl))
        ))

    def get_max_flow_load(self, wpa):
        h1, h2 = _sort_pair(wpa[0], wpa[-1])
        ml = 0
        if not isinstance(wpa, WeightedPathAggregate):
            wpa = WeightedPathAggregate({tuple(wpa): 1.0})
        for seq, weight in wpa.items():
            for i in range(len(seq)-1):
                link = tuple(seq[i:i+2])
                revlink = tuple(list(reversed(link)))
                ml = max(
                    ml,
                    ((
                        (
                            self._flow_speed.get(tuple([h1, *link, h2]), 0)
                            /
                            self.max_speed[link]
                        )+(
                            self._flow_speed.get(tuple([h2, *revlink, h1]), 0)
                            /
                            self.max_speed[revlink]
                        )
                    ))*weight
                )
        return ml

    def get_max_flow_speed(self, wpa):
        h1, h2 = _sort_pair(wpa[0], wpa[-1])
        if not isinstance(wpa, WeightedPathAggregate):
            wpa = WeightedPathAggregate({tuple(wpa): 1.0})
        ml = 0
        for seq, weight in wpa.items():
            for i in range(len(seq)-1):
                link = tuple(seq[i:i+2])
                revlink = tuple(list(reversed(link)))
                ml = max(
                    ml,
                    ((
                        self._flow_speed.get(tuple([h1, *link, h2]), 0)
                        +
                        self._flow_speed.get(tuple([h2, *revlink, h1]), 0)
                    ))*weight
                )
        return ml

    def get_max_path_load(self, wpa):
        ml = 0
        if not isinstance(wpa, WeightedPathAggregate):
            wpa = WeightedPathAggregate({tuple(wpa): 1.0})
        for seq in wpa.keys():
            for i in range(len(seq)-1):
                link = tuple(seq[i:i+2])
                ml = max(
                    ml,
                    self.link_usage[link]
                )
        return ml

    def with_modified_path(self, newpath):
        mod = self.copy()
        oldpath = self.get_path(newpath[0], newpath[-1])
        flowspeed = self.get_max_flow_speed(oldpath)
        # removing old flows
        for sw in mod.switches.values():
            for k in sw._flow_speed.copy().keys():
                if (
                    k[0] in [newpath[0], newpath[-1]]
                    and
                    k[3] in [newpath[0], newpath[-1]]
                ):
                    del sw._flow_speed[k]
        # adding new flows
        if not isinstance(newpath, WeightedPathAggregate):
            newpath = WeightedPathAggregate({tuple(newpath): 1.0})
        for newpath2, weight in newpath.items():
            for i in range(1, len(newpath2)-1):
                ky = newpath2[0], newpath2[i], newpath2[i+1], newpath2[-1]
                rk = newpath2[-1], newpath2[i-1], newpath2[i], newpath2[0]
                if ky[1].startswith('s') and ky[1] in mod.switches:
                    mod.switches[ky[1]]._flow_speed[ky] = (weight*flowspeed)/2
                if rk[1].startswith('s') and rk[1] in mod.switches:
                    mod.switches[rk[1]]._flow_speed[rk] = (weight*flowspeed)/2
        for sw in mod.switches.values():
            sw._reinit()
        self.paths[tuple([newpath[0], newpath[-1]])] = newpath
        mod._reinit()
        return mod

    def copy_normalized(self):
        net = self.copy()
        for path in net.get_routes()._pairs.values():
            net = net.with_modified_path(path)
        return net

    # Gvozdiev et al @ SIGCOMM2018, p. 94 => Algorithm 1
    def copy_scaling(self, prev_prediction: Dict[Tuple[str], float], fixed_hedge: float, decay_multiplier: float) -> Tuple['SimulatableNetwork', Dict[Tuple[str], float]]:
        if prev_prediction is None:
            prev_prediction = dict()
        net = self.copy()
        next_prediction = dict()
        for sw in net.switches.values():
            for idtf, prev_value in sw._flow_speed.items():
                scaled_est = prev_value*fixed_hedge
                if scaled_est > prev_prediction.get(idtf, 0):
                    next_prediction[idtf] = scaled_est
                else:
                    decay_prediction = prev_prediction.get(
                        idtf, 0) * decay_multiplier
                    next_prediction[idtf] = max(decay_prediction, scaled_est)
        for sw in net.switches.values():
            for idtf in sw._flow_speed.keys():
                sw._flow_speed[idtf] = next_prediction[idtf]
            sw._reinit()
        net._reinit()
        return net, next_prediction


class AbstractPathEvaluator:
    def __init__(self, simulatable_network: SimulatableNetwork, keepdata: Optional[Any]):
        self._simnet: SimulatableNetwork = simulatable_network
        self._keepdata = keepdata

    def __call__(self) -> Tuple['UsageStore', NoneType]: pass


class NullPathEvaluator(AbstractPathEvaluator):
    def __call__(self) -> Tuple['UsageStore', NoneType]:
        return UsageStore(), None


class LDRSinglePathEvaluator(AbstractPathEvaluator):
    def __call__(self) -> Tuple['UsageStore', NoneType]:
        return self._figure13(self._simnet.copy()), None
        # return self._figure12(
        #     self._simnet.link_usage,
        #     self._simnet.link_flows
        # )

    def _figure13(self, net: SimulatableNetwork) -> 'UsageStore':
        net = net.copy_normalized()
        _tmp = self._figure12(
            net.link_usage,
            net.link_flows
        )
        target = len(_tmp._pairs)
        changed = UsageStore()
        newnet = None
        while len(changed._pairs) < target:
            aggregate_paths = self._figure12(
                net.link_usage,
                net.link_flows
            )
            loaded_paths = net.sort_by_max_flow_load([
                *aggregate_paths._pairs.values()
            ])
            most_loaded = None
            for loaded in loaded_paths:
                if not changed.contains((loaded[0], loaded[-1])):
                    most_loaded = loaded
                    break
            if most_loaded is None:
                break
            newnet = net.with_modified_path(most_loaded)
            old_path_for_most_loaded = net.get_path(
                most_loaded[0], most_loaded[-1])
            if (
                newnet.get_max_path_load(most_loaded)
                <=
                net.get_max_path_load(old_path_for_most_loaded)
            ):
                net = newnet
            changed[(most_loaded[0], most_loaded[-1])] = most_loaded
        return net.get_routes()

    def _figure12(self, link_usage, link_flows) -> 'UsageStore':
        processed = UsageStore()
        currently_reserved = UsageStore()
        ospf = Dijkstra(network_graph)
        l1 = network_topo[0][:]
        random.shuffle(l1)
        for h1 in l1:
            l2 = network_topo[0][:]
            random.shuffle(l2)
            for h2 in l2:
                if h1 != h2 and not processed.contains((h1, h2)):
                    h1p = network_topo[0].index(h1)
                    h2p = network_topo[0].index(h2)
                    ospf_aggregate = ospf(h1)(h2)[0]
                    ospf_delay = sum([
                        link_usage[
                            tuple([*ospf_aggregate[i:i+2]])
                        ] + hop_delay
                        for i in range(len(ospf_aggregate)-1)
                    ])
                    aggregates = list(pop_apa_candidates[h1p][h2p])
                    random.shuffle(aggregates)
                    del h1p
                    del h2p
                    min_aggregate = None
                    min_aggregate_val = None
                    min_aggregate_links = list()
                    nalist = list()
                    na = 0  # flows in aggregate
                    omax = 0  # maximum overload
                    for aggregate in aggregates:
                        links = [
                            _sort_pair(*aggregate[i:i+2])
                            for i in range(len(aggregate)-1)
                        ]
                        omax2 = 0
                        for link in links:
                            omax2 = max(omax2, link_usage[link])
                            if link not in nalist:
                                na += link_flows[link]
                                na += currently_reserved[link]
                                nalist.append(link)
                            pass  # fraction of aggregate on path
                        if omax2 > omax:
                            omax = omax2
                    # del nalist
                    # for aggregate in aggregates:
                        links = [
                            _sort_pair(*aggregate[i:i+2])
                            for i in range(len(aggregate)-1)
                        ]
                        eps2 = 0
                        xap = 1
                        for link in links:
                            dp = link_usage[link]+hop_delay
                            pass  # path delay
                            eps2 += xap*(dp+((dp*m1)/ospf_delay))
                        exp0 = m2*omax
                        eps3 = 0
                        eps3 += sum([link_usage[link] for link in links])
                        aggregate_val = na*eps2+exp0+eps3
                        if (
                            min_aggregate_val is None
                            or
                            min_aggregate_val > aggregate_val
                        ):
                            min_aggregate_val = aggregate_val
                            min_aggregate = aggregate
                            min_aggregate_links = links
                    processed[(h1, h2)] = min_aggregate
                    for link in min_aggregate_links:
                        currently_reserved[link] = 1+currently_reserved[link]
        return processed


class LDRPathEvaluator(AbstractPathEvaluator):
    def __call__(self) -> Tuple['UsageStore', NoneType]:
        net, kd = self._simnet.copy_scaling(self._keepdata, 1.1, 0.98)
        return self._figure12(net.copy()), kd

    def _figure13(self, net: SimulatableNetwork) -> 'UsageStore':
        net = net.copy_normalized()
        _tmp = self._figure12(net.copy())
        target = len(_tmp._pairs)
        changed = UsageStore()
        newnet = None
        while len(changed._pairs) < target:
            aggregate_paths = self._figure12(net.copy())
            loaded_paths = net.sort_by_max_flow_load([
                *aggregate_paths._pairs.values()
            ])
            most_loaded = None
            for loaded in loaded_paths:
                if not changed.contains((loaded[0], loaded[-1])):
                    most_loaded = loaded
                    break
            if most_loaded is None:
                break
            newnet = net.with_modified_path(most_loaded)
            old_path_for_most_loaded = net.get_path(
                most_loaded[0], most_loaded[-1])
            if (
                newnet.get_max_path_load(most_loaded)
                <=
                net.get_max_path_load(old_path_for_most_loaded)
            ):
                net = newnet
            changed[(most_loaded[0], most_loaded[-1])] = most_loaded
        return net.get_routes()

    def _figure12(self, net: SimulatableNetwork) -> 'UsageStore':
        link_usage = net.link_usage
        link_flows = net.link_flows
        ospf = Dijkstra(network_graph)
        opt_model = pulp.LpProblem("LDR", pulp.LpMinimize)
        xap = pulp.LpVariable("xa", 0, 1)
        processed = UsageStore(default=dict())
        l1 = network_topo[0][:]
        random.shuffle(l1)
        sumaggregates = 0
        for h1 in l1:
            l2 = network_topo[0][:]
            random.shuffle(l2)
            for h2 in l2:
                if h1 != h2 and not processed.contains((h1, h2)):
                    h1, h2 = _sort_pair(h1, h2)
                    opt_vars = dict()
                    processed[(h1, h2)] = opt_vars
                    h1p = network_topo[0].index(h1)
                    h2p = network_topo[0].index(h2)
                    ospf_aggregate = ospf(h1)(h2)[0]
                    ospf_delay = sum([
                        link_usage[
                            tuple([*ospf_aggregate[i:i+2]])
                        ] + hop_delay
                        for i in range(len(ospf_aggregate)-1)
                    ])
                    aggregates = list(pop_apa_candidates[h1p][h2p])[:]
                    for aggregate in aggregates[:]:
                        links = [
                            _sort_pair(*aggregate[i:i+2])
                            for i in range(len(aggregate)-1)
                        ]
                        dp = sum(
                            [link_usage[link]+hop_delay for link in links])
                        if (ospf_delay == 0) or ((dp/ospf_delay) > apa_path_stretch):
                            del aggregates[aggregates.index(aggregate)]
                    random.shuffle(aggregates)
                    sumpinpa = 0
                    sumxappinpa = 0
                    na = sum([
                        link_flows[link]
                        for aggregate in aggregates
                        for link in [
                            _sort_pair(*aggregate[i:i+2])
                            for i in range(len(aggregate)-1)
                        ]
                    ])
                    na = max(na, MIN_POSITIVE_FLOAT)
                    for aggregate in aggregates:
                        links = [
                            _sort_pair(*aggregate[i:i+2])
                            for i in range(len(aggregate)-1)
                        ]
                        xap = pulp.LpVariable(
                            f"xap_{h1}_{h2}__{'_'.join(aggregate)}", 0, 1)
                        opt_vars[tuple(aggregate)] = xap
                        omax = max(0, *[link_usage[link] for link in links])
                        olinks = sum([link_usage[link] for link in links])
                        dp = sum(
                            [link_usage[link]+hop_delay for link in links])
                        tiebreaker = (dp+((dp*m1)/ospf_delay))

                        sumxappinpa += xap
                        sumpinpa += xap*(tiebreaker+(m2*omax)+olinks)
                        opt_model += 0 <= xap <= 1
                    opt_model += sumxappinpa == 1
                    sumaggregates += na*sumpinpa
        opt_model += sumaggregates
        opt_model.solve()
        solution = {
            (tuple(k[4:].split('__')[0].split('_')), tuple(k[4:].split('__')[1].split('_'))):
            v.varValue
            for k, v in opt_model.variablesDict().items()
            if k.startswith('xap_')
        }
        # print(opt_model)
        d = dict()
        for (tpl, path), weight in solution.items():
            if tpl not in d:
                d[tpl] = dict()
            d[tpl][path] = weight
        weighted_result = UsageStore(initial={
            k: WeightedPathAggregate(v)
            for k, v in d.items()
        })
        # print(weighted_result)
        # opt_model.solve()                        # solving with CBC
        # opt_model.solve(solver=pulp.GLPK_CMD())  # solving with Glpk
        return weighted_result


class MinMaxSinglePathEvaluator(AbstractPathEvaluator):
    def __call__(self) -> Tuple['UsageStore', NoneType]:
        return self.minmax(self._simnet.copy()), None

    def minmax(self, net: SimulatableNetwork) -> 'UsageStore':
        net = net.copy_normalized()
        processed = UsageStore()
        l1 = network_topo[0][:]
        random.shuffle(l1)
        for h1 in l1:
            l2 = network_topo[0][:]
            random.shuffle(l2)
            for h2 in l2:
                if h1 != h2 and not processed.contains((h1, h2)):
                    h1p = network_topo[0].index(h1)
                    h2p = network_topo[0].index(h2)
                    aggregates = list(pop_apa_candidates[h1p][h2p])
                    configurations = list()
                    for aggregate in aggregates:
                        links = [
                            _sort_pair(*aggregate[i:i+2])
                            for i in range(len(aggregate)-1)
                        ]
                        newnet = net.with_modified_path(aggregate)
                        configurations.append((
                            newnet.get_max_path_load(aggregate),
                            len(aggregate),
                            aggregate,
                            newnet
                        ))
                    configurations.sort()
                    configuration = configurations[0]
                    processed[(h1, h2)] = configuration[2]
                    net = configuration[3]
        return processed


path_evaluators = {
    'ospf': NullPathEvaluator,
    'ldr-single': LDRSinglePathEvaluator,
    'minmax-single': MinMaxSinglePathEvaluator,
    'ecmp': NullPathEvaluator,
    'ldr': LDRPathEvaluator,
}

PathEvaluator = path_evaluators[routing_algo]

ppe = ProcessPoolExecutor(1)
last_process = None
last_process_lock = threading.Lock()
initialized_switch_writing_lock = threading.Lock()

class LatencyApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.controllers = {}
        self._paths = host_path_from_list(network_topo[0])
        self._loads = usage_store_from_list(enumerate([]))
        self.max_speed = bandwidth_from_list(enumerate(network_topo[2]))
        self.last_speed = UsageStoreProxyFromCallableIterable(
            AttrCallableIterable(
                AttrCallableIterable(
                    self.controllers.values,
                    '_link_speed'
                ),
                'as_regular_storage'
            ),
            sum
        )
        self.flow_count = UsageStoreProxyFromCallableIterable(
            AttrCallableIterable(self.controllers.values, '_link_rules'),
            sum
        )
        self.ospf_dijkstra = Dijkstra(network_graph)
        self.ecmp_group_ids = dict()
        self.ecmp_group_id_buckets = dict()
        self._last_process_data = None
        self.interval = float(network_config['monitoring']['interval'])
        hub.spawn(self._start_monitoring, self.interval)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _event_ofp_state_change(self, ev):
        datapath = ev.datapath
        dpid = datapath.id
        if ev.state == MAIN_DISPATCHER:
            if dpid not in self.controllers:
                self.controllers[dpid] = LatencyController(datapath)
                self.controllers[dpid].connected(self)
                self._request_stats(datapath)
        elif ev.state == DEAD_DISPATCHER:
            if dpid in self.controllers:
                self.controllers[dpid].disconnected()
                del self.controllers[dpid]

    def _start_monitoring(self, repeat):
        global last_process
        while True:
            print("Monitoring loop called")
            for ctrl in self.controllers.values():
                hub.spawn(self._request_stats, ctrl._datapath)
            hub.spawn(self._update_performance_state)
            hub.spawn(self._trigger_path_refresh)
            sleep(repeat)

    def _trigger_path_refresh(self):
        with last_process_lock:
            # if last_process is not None:
            #     last_process.cancel()
            last_process = ppe.submit(
                PathEvaluator(
                    *self._monitored_data(),
                    self._last_process_data
                )
            )
            last_process.add_done_callback(self._update_topo_done)

    def _request_stats(self, datapath):
        datapath.send_msg(
            datapath.ofproto_parser.OFPFlowStatsRequest(
                datapath
            )
        )

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        global last_process
        dpid = ev.msg.datapath.id
        ctrl = self.controllers.get(dpid)
        if ctrl is not None:
            ctrl._on_stats(ev, self)

    def _monitored_data(self):
        self._loads = self.max_speed.calculate(
            self.last_speed.as_regular_storage,
            lambda maxspeed, lastspeed: (
                lastspeed / max(maxspeed, 0.0000000000001)
            )
        )
        return (
            SimulatableNetwork([
                ctrl.simulatable
                for ctrl in self.controllers.values()
            ], self._paths),
        )

    def _update_topo_done(self, future):
        if not future.cancelled():
            res, keepdata = future.result()
            self._update_topo_done_successfully(res)
            self._last_process_data = keepdata
            self._update_performance_state()
        else:
            print(future.exception)

    def _update_topo_done_successfully(self, processed):
        print(f'-> Topo updated {datetime.datetime.now()}')
        for (h1, h2), path in processed._pairs.items():
            self._paths[(h1, h2)] = path
            ip1 = id2ip(int(h1[1:])-1)
            ip2 = id2ip(int(h2[1:])-1)
            if isinstance(path, WeightedPathAggregate):
                for src, weighted_destinations in path.transitions(h1).items():
                    if src.startswith('s'):
                        ctrl = self.controllers.get(int(src[1:]))
                        if ctrl is not None:
                            ctrl.add_weighted_latency(
                                self, ip1, ip2, weighted_destinations)
                for src, weighted_destinations in path.transitions(h2).items():
                    if src.startswith('s'):
                        ctrl = self.controllers.get(int(src[1:]))
                        if ctrl is not None:
                            ctrl.add_weighted_latency(
                                self, ip2, ip1, weighted_destinations)
            else:
                for i in range(len(path)-1):
                    segment = path[i:i+2]
                    if segment[0].startswith('s'):
                        ctrl = self.controllers.get(int(segment[0][1:]))
                        if ctrl is not None:
                            ctrl.add_latency_segment(ip1, ip2, segment[1])
                    if segment[1].startswith('s'):
                        ctrl = self.controllers.get(int(segment[1][1:]))
                        if ctrl is not None:
                            ctrl.add_latency_segment(ip2, ip1, segment[0])

    def _update_performance_state(self):
        sio = StringIO()
        print(f'@start.path', file=sio)
        for _, path in sorted(self._paths._pairs.items()):
            if isinstance(path, WeightedPathAggregate):
                print(repr(dict(sorted(path.items()))), file=sio)
            else:
                print(repr({tuple(path): 1.0}), file=sio)
        print(f'@end.path', file=sio)
        print(f'@start.load', file=sio)
        for (ne1, ne2), load in sorted(self._loads._pairs.items()):
            print(repr((ne1, ne2, load)), file=sio)
        print(f'@end.load', file=sio)
        # print(sio.getvalue(), end='')
        with open(f'{base_net_name}.state', 'w') as f:
            v = sio.getvalue()
            f.write(v)
        # os.rename(f'{base_net_name}.state2', f'{base_net_name}.state')


def portno_from_list(l):
    return UsageStore(dict([
        (tuple(x[:2]), i+1)
        for i, x in l
    ]))


def usage_store_from_list(l):
    return UsageStore(dict([
        (tuple(x[:2]), 0)
        for _, x in l
    ]))


def host_path_from_list(l):
    return UsageStore(dict([
        ((x, y), list())
        for x in l
        for y in l
        if x != y
    ]), default=list())


def bandwidth_from_list(l):
    return UsageStore(dict([
        (tuple(x[:2]), x[2])
        for _, x in l
    ]))


class PairSorterMixin:
    def _sort_pair(self, a, b):
        return _sort_pair(a, b)


class UsageStore(PairSorterMixin):
    def __init__(self, initial=dict(), default=0):
        self._pairs = dict()
        for k, v in initial.items():
            self[k] = v
        self._default = default

    def __getitem__(self, idx) -> float:
        srtd = self._sort_pair(*idx)
        pairs = self._pairs
        if srtd not in pairs:
            return self._default
        else:
            return pairs[srtd]

    def reverse_lookup(self, val):
        return [k for k, v in self._pairs.items() if v == val]

    def calculate(self, other, operation):
        return UsageStore({
            k: operation(v, other[k])
            for k, v in self._pairs.items()
        })

    def contains(self, idx) -> bool:
        return self._sort_pair(*idx) in self._pairs.keys()

    def __setitem__(self, idx, val: float):
        self._pairs[self._sort_pair(*idx)] = val

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"{type(self).__name__}({repr(self._pairs)})"

    def copy(self):
        return type(self)(self._pairs.copy(), self._default)

    def to_regular_storage(self):
        return self.copy()

    @property
    def as_regular_storage(self):
        return self.to_regular_storage()


class ValueGetterCallable:
    def __init__(self, value):
        self._val = value

    def __call__(self, *args, **kwargs):
        return self._val


class UsageStoreProxyFromCallableIterable(PairSorterMixin):
    def __init__(self, clb, get_behaviour=None, default=0):
        self._callable = clb
        self._behaviour = get_behaviour
        self.is_frozen = False
        self._default = default

    def __getitem__(self, idx) -> float:
        r = list()
        srtd = self._sort_pair(*idx)
        for us in self._callable():
            v = us._pairs.get(srtd)
            if v is not None:
                r.append(v)
        if self._behaviour is None:
            return self._default
        else:
            return self._behaviour(r)

    def __setitem__(self, idx, val: float):
        alo = False
        srtd = self._sort_pair(*idx)
        for us in self._callable():
            v = us._pairs.get(srtd)
            if v is not None:
                us._pairs[srtd] = val
                alo = True
        if not alo:
            raise ValueError(
                f"There's no existing connection between" +
                f" {idx[0]} and {idx[1]} " +
                f"to update"
            )

    def to_regular_storage(self):
        keys = set([
            key
            for us in self._callable()
            for key in us._pairs.keys()
        ])
        return UsageStore(dict([(key, self[key]) for key in keys]))

    @property
    def as_regular_storage(self):
        return self.to_regular_storage()

    @property
    def frozen(self):
        frz = type(self)(
            ValueGetterCallable(self._callable()),
            self._behaviour
        )
        frz.is_frozen = True
        return frz


class UsageStoreProxyFromFlowDict(UsageStore):
    def __init__(self, dct, aggregator=sum):
        self._flows = dct
        self._agg = aggregator

    @property
    def _pairs(self):
        d = dict()
        l = [(self._sort_pair(k[1], k[2]), v) for k, v in self._flows.items()]
        for k, _ in l:
            if k not in d:
                d[k] = list()
        for k, v in l:
            d[k].append(v)
        for k in d.keys():
            d[k] = self._agg(d[k])
        return d

    def to_regular_storage(self):
        return UsageStore(self._pairs)

    @property
    def as_regular_storage(self):
        return self.to_regular_storage()


class AttrCallableIterable:
    def __init__(self, callablecollection, attr):
        self._cc = callablecollection
        self._attr = attr

    def __call__(self):
        for i in self._cc():
            yield getattr(i, self._attr)
        yield from EMPTY_ITER


class DictAggregator:
    def __init__(self, ds):
        self._ds = ds

    def __getitem__(self, q):
        for d in self._ds:
            if q in d:
                return d[q]
        return self._ds[q]

    def get(self, q, e=None):
        for d in self._ds:
            if q in d:
                return d[q]
        return e

    def keys(self):
        return {
            k
            for d in self._ds
            for k in d.keys()
        }

    def values(self):
        return {
            v
            for d in self._ds
            for v in d.values()
        }

    def items(self):
        return {
            i
            for d in self._ds
            for i in d.items()
        }

    def to_regular_dict(self):
        return dict(self.items())

    def copy(self):
        return type(self)(self._ds.copy())


class WeightedPathAggregate:
    def __init__(self, weighted: Dict[Tuple[str], float] = dict()):
        self._subscriptable = list(weighted.keys())[0]
        self._weighted = weighted

    def items(self):
        return self._weighted.items()

    def keys(self):
        return self._weighted.keys()

    def values(self):
        return self._weighted.values()

    def __getitem__(self, val: int) -> str:
        return self._subscriptable[val]

    def transitions(self, in_src):
        transitions_algo_weighted = dict()
        for path, weight in self.items():
            if path[0] != in_src:
                path = tuple(list(reversed(list(path))))
            links = [
                path[i:i+2]
                for i in range(len(path)-1)
            ]
            for ne1, ne2 in links:
                if ne1.startswith('s'):
                    if ne1 not in transitions_algo_weighted:
                        transitions_algo_weighted[ne1] = dict()
                    if weight > transitions_algo_weighted[ne1].get(ne2, NEG_INF):
                        transitions_algo_weighted[ne1][ne2] = weight
        transitions_reweighted = dict()
        for src, d in transitions_algo_weighted.items():
            if src not in transitions_reweighted:
                transitions_reweighted[src] = dict()
            sw = sum(d.values())
            if sw <= 0:
                for dst, w in d.items():
                    transitions_reweighted[src][dst] = 1.0/len(d)
            else:
                for dst, w in d.items():
                    transitions_reweighted[src][dst] = w/sw
        return transitions_reweighted

    def __str__(self):
        return f"{type(self).__name__}({repr(self._weighted)})"

    def __repr__(self):
        return str(self)
