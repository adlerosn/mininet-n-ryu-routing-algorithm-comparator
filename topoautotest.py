#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys
import json
import importlib
import traceback
from typing import Set
from subprocess import run, PIPE
from time import sleep
from pathlib import Path

WAIT_TIMEOUT = int(5*60)
TIMEOUT_EXCEEDED_EXC = TimeoutError(f"Cannot wait more than {WAIT_TIMEOUT} seconds before testing starts")

seconds_waited = 0


def wait():
    global seconds_waited
    print('*** Waiting', file=sys.stderr)
    sleep(2)
    seconds_waited += 2


def reset_wait():
    global seconds_waited
    seconds_waited = 0


def speed_parser_iperf(iperfstdout):
    speed, unit = iperfstdout.splitlines()[-1].split('/')[0].split(' ')[-2:]
    speed = float(speed)
    multiplier = {
        'bits': 10**0,
        'kbits': 10**3,
        'mbits': 10**6,
        'gbits': 10**9,
        'tbits': 10**12,
    }.get(unit.lower(), 1)
    return int(speed*multiplier)


def make_host_pairs(hosts):
    s = len(hosts)//2
    r = hosts[-s:]
    rs = len(r)
    l = hosts[:-s][:rs]
    return list(zip(l, list(reversed(r))))


def test_ping_sync(src, dst):
    print(f'*** Pinging {src.IP()} -> {dst.IP()}', file=sys.stderr)
    k = src.pexec('ping', dst.IP(), '-c', str(10))
    if '100% packet loss' in k[0]:
        raise ValueError("Cannot evaluate PING if no packet returned")
    _, avg, __, dev = (
        list(map(
            float,
            k[0].splitlines()[-1].split('=')[1].strip().split(' ')[0].split('/')
        ))
    )
    return dict(avg=avg, mdev=dev)


def test_iperf_sync(src, dst):
    print(f'*** Iperfing {src.IP()} -> {dst.IP()}', file=sys.stderr)
    s = dst.popen('iperf', '-s')
    k = src.pexec('iperf', '-c', dst.IP())
    s.kill()
    if k[0] == '':
        raise Exception(k[1])
    return speed_parser_iperf(k[0])


def do_sequential_tests(pingpair, iperfpairs):
    print(f'*** Performing sequential tests', file=sys.stderr)
    iperfres = list()
    pingres = test_ping_sync(*pingpair)
    wait()
    for iperfpair in iperfpairs:
        iperfres.append(test_iperf_sync(*iperfpair))
        wait()
    return dict(ping=pingres, iperfs=iperfres)


class IperfWaiter:
    def __init__(self, *x):
        self._x = x

    def __call__(self):
        s, k, *_ = self._x
        k.wait()
        k = (k.stdout.read().decode(), )
        s.kill()
        return speed_parser_iperf(k[0])


def test_iperf_async(src, dst):
    print(f'*** Iperfing {src.IP()} -> {dst.IP()}', file=sys.stderr)
    s = dst.popen('iperf', '-s')
    k = src.popen('iperf', '-c', dst.IP())
    return IperfWaiter(s, k)


class PingWaiter:
    def __init__(self, *x):
        self._x = x

    def __call__(self):
        k, *_ = self._x
        k.wait()
        k = (k.stdout.read().decode(), )
        _, avg, __, dev = (
            list(map(
                float,
                k[0].splitlines()[-1].split('=')[1].strip().split(' ')[0].split('/')
            ))
        )
        return dict(avg=avg, mdev=dev)


def test_ping_async(src, dst):
    print(f'*** Pinging {src.IP()} -> {dst.IP()}', file=sys.stderr)
    k = src.popen('ping', dst.IP(), '-c', str(10))
    return PingWaiter(k)


def do_parallel_tests(pingpair, iperfpairs):
    print(f'*** Performing parallel tests', file=sys.stderr)
    iperfres = list()
    for iperfpair in reversed(iperfpairs):
        iperfres.append(test_iperf_async(*iperfpair))
    pingres = test_ping_async(*pingpair)
    pingres = pingres()
    iperfres = [r() for r in iperfres]
    # wait()
    return dict(ping=pingres, iperfs=iperfres)


def get_switch_set(topo) -> Set[str]:
    return set(topo[1])


def get_loaded_switches_set(path=Path("~current.sws.state")) -> Set[str]:
    return set(filter(len, path.read_text().splitlines()))


def is_routing_ready() -> bool:
    return Path(f'{Path("~current.state").read_text().strip()}.state').exists()


def do_tests(topo, hosts, net):
    print(f'*** Controller will bind its socket soon', file=sys.stderr)
    while len(run("netstat -lant | grep :6633", shell=True, stdout=PIPE).stdout) <= 2:
        if seconds_waited > WAIT_TIMEOUT:
            raise TIMEOUT_EXCEEDED_EXC
        wait()
    sws = seconds_waited
    swe = None
    if is_routing_ready():
        swe = seconds_waited
    print(f'*** Controller will register its switches', file=sys.stderr)
    while len(get_switch_set(topo).difference(get_loaded_switches_set())) > 0:
        if seconds_waited > WAIT_TIMEOUT:
            raise TIMEOUT_EXCEEDED_EXC
        wait()
        if swe is None and is_routing_ready():
            swe = seconds_waited
    if swe is None:
        print(
            f'*** Controller is taking very long to figure out a route...', file=sys.stderr)
    while not is_routing_ready():
        if seconds_waited > WAIT_TIMEOUT:
            raise TIMEOUT_EXCEEDED_EXC
        wait()
    if swe is None:
        swe = seconds_waited
    pairs = make_host_pairs(hosts)
    pingpair, *iperfpairs = pairs
    seqres = None
    seqres = do_sequential_tests(pingpair, iperfpairs)
    pllres = do_parallel_tests(pingpair, iperfpairs)
    return dict(
        routing_time=swe-sws,
        sequential=seqres,
        parallel=pllres
    )


def main(topo, mod, resultspath, returns_result=False):
    reset_wait()
    print(f'*** Creating network', file=sys.stderr)
    net = mod.myNetwork()
    try:
        x = {h.name: h for h in net.hosts}
        hosts = [x[h] for h in topo[0]]
        res = do_tests(topo, hosts, net)
        pingpair, *iperfpairs = make_host_pairs(topo[0])
        res = dict(
            pairs=dict(
                ping=pingpair,
                iperf=iperfpairs
            ),
            **res
        )
        net.stop()
        if returns_result:
            return res
        else:
            resultspath.write_text(json.dumps(
                res,
                indent=4
            ))
    except BaseException as e:
        print("*** Aborted application: ", end='', file=sys.stderr)
        print(str(e).strip(), file=sys.stderr)
        run(['mn', '-c'], stderr=PIPE, stdout=PIPE)
        if returns_result:
            return None
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage:')
        print(f'  {sys.argv[0]} <toponame>')
        print()
        print('   Where toponame is will be resolved to')
        print('   toponame.json and toponame.state')
    else:
        modname = f'{sys.argv[1]}'
        commentedname = modname+(
            '.' if len(sys.argv) > 2 else ''
        )+'.'.join(sys.argv[2:])
        modfile = Path(f'{modname}.py')
        topopath = Path(f'{modname}.json')
        resultspath = Path(f'{commentedname}.autotest.json')
        if not topopath.exists():
            print(f'Topology {topopath}.json does not exist.')
        if not modfile.exists():
            print(f'Topology {topopath}.py does not exist.')
            print(f'You might want to use toporender.py to generate required files.')
        else:
            topo = json.loads(topopath.read_text())
            mod = importlib.import_module(modname)
            main(topo, mod, resultspath)
