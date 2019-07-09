#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import json
from pathlib import Path
from counteriter import CounterIterator
from toporender import main as renderer

virtual_servers_per_physical_server = 0
physical_servers_per_rack_tower = 1
rack_tower_per_corridor = 2
corridors = 3
spines = 4

linkspd_virtual_physical = 0.1  # 100 mbps
linkspd_physicalhost_switch = 0.1  # 100 mbps
linkspd_physical_tower = 0.1  # 100 mbps
linkspd_tower_corridor = 1  # 1 gbps
linkspd_corridor_spine = 1  # 1 gbps
linkspd_spine_spine = 10  # 10 gbps

# overriding some stuff
linkspd_virtual_physical = 1  # 1 mbps
linkspd_physicalhost_switch = 1  # 1 mbps
linkspd_physical_tower = 1  # 1 mbps
linkspd_tower_corridor = 1  # 1 mbps
linkspd_corridor_spine = 1  # 1 mbps
linkspd_spine_spine = 1  # 1 mbps

hosts_iter = CounterIterator()
switch_iter = CounterIterator()


def reset_iters():
    global hosts_iter
    global switch_iter
    hosts_iter = CounterIterator()
    switch_iter = CounterIterator()


def create_virtual_server():
    this_hosts = []
    this_switches = []
    this_links = []
    this_hosts.append("h%d" % next(hosts_iter))
    return this_hosts, this_switches, this_links


def create_physical_server():
    this_hosts = []
    this_switches = []
    this_links = []
    serv = "h%d" % next(hosts_iter)
    sw = "s%d" % next(switch_iter)
    for _ in range(virtual_servers_per_physical_server):
        chd_hosts, chd_switches, chd_links = create_virtual_server()
        this_hosts += chd_hosts
        this_switches += chd_switches
        this_links += chd_links
        this_links.append((chd_hosts[-1], sw, linkspd_virtual_physical))
    this_hosts.append(serv)
    this_switches.append(sw)
    this_links.append((serv, sw, linkspd_physicalhost_switch))
    return this_hosts, this_switches, this_links


def create_racktower():
    this_hosts = []
    this_switches = []
    this_links = []
    sw = "s%d" % next(switch_iter)
    for _ in range(physical_servers_per_rack_tower):
        chd_hosts, chd_switches, chd_links = create_physical_server()
        this_hosts += chd_hosts
        this_switches += chd_switches
        this_links += chd_links
        lsw = chd_switches[-1]
        this_links.append((lsw, sw, linkspd_physical_tower))
    this_switches.append(sw)
    return this_hosts, this_switches, this_links


def create_corridor():
    this_hosts = []
    this_switches = []
    this_links = []
    sw1 = "s%d" % next(switch_iter)
    sw2 = "s%d" % next(switch_iter)
    for _ in range(rack_tower_per_corridor):
        chd_hosts, chd_switches, chd_links = create_racktower()
        this_hosts += chd_hosts
        this_switches += chd_switches
        this_links += chd_links
        lsw = chd_switches[-1]
        this_links.append((lsw, sw1, linkspd_tower_corridor))
        this_links.append((lsw, sw2, linkspd_tower_corridor))
    this_switches.append(sw1)
    this_switches.append(sw2)
    return this_hosts, this_switches, this_links


def create_spine():
    this_hosts = []
    this_switches = []
    this_links = []
    swsps = ["s%d" % next(switch_iter) for _ in range(spines)]
    for i in range(spines-1):
        chd_hosts, chd_switches, chd_links = create_corridor()
        this_hosts += chd_hosts
        this_switches += chd_switches
        this_links += chd_links
        lsw1, lsw2 = chd_switches[-2:]
        this_links.append((lsw1, swsps[i], linkspd_corridor_spine))
        this_links.append((lsw2, swsps[i+1], linkspd_corridor_spine))
    this_switches += swsps
    return this_hosts, this_switches, this_links


def create_datacenter():
    this_hosts = []
    this_switches = []
    this_links = []
    last_spined_corridor = []
    for _ in range(corridors):
        chd_hosts, chd_switches, chd_links = create_spine()
        this_hosts += chd_hosts
        this_switches += chd_switches
        this_links += chd_links
        spined_corridor = chd_switches[-spines:]
        if len(last_spined_corridor) > 0:
            for i in range(spines):
                this_links.append(
                    (last_spined_corridor[i], spined_corridor[i], linkspd_spine_spine))
        last_spined_corridor = spined_corridor
    return this_hosts, this_switches, this_links


def main(fn: str = 'bigtopo'):
    reset_iters()
    datacenter = create_datacenter()
    reset_iters()
    Path(f'{fn}.json').write_text(json.dumps(datacenter))
    renderer(fn)


if __name__ == '__main__':
    main()
