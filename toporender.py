#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys
import json
from pathlib import Path
from id2ip import id2ip
from os import linesep as eol


def render_topology(hosts, switches, links):
    indent = ' '*4
    s = ''
    s += f'#!/usr/bin/env python{eol}# -*- encoding: utf-8 -*-{eol}'+eol
    s += 'from mininet.net import Mininet'+eol
    s += 'from mininet.topo import Topo'+eol
    s += 'from mininet.node import Controller, RemoteController, OVSController'+eol
    s += 'from mininet.node import CPULimitedHost, Host, Node'+eol
    s += 'from mininet.node import OVSKernelSwitch, UserSwitch'+eol
    s += 'from mininet.node import IVSSwitch'+eol
    s += 'from mininet.cli import CLI'+eol
    s += 'from mininet.log import setLogLevel, info'+eol
    s += 'from mininet.link import TCLink, Intf'+eol
    s += 'from subprocess import call'+eol
    s += eol
    ##########################################################################
    # s += eol
    # s += f'class HostWithForward(Host):{eol}'
    # s += f"{indent}def config(self, **params):{eol}"
    # s += f"{indent}{indent}super().config(**params){eol}"
    # s += f"{indent}{indent}self.cmd('sysctl net.ipv4.ip_forward=1'){eol}"
    # s += eol
    # s += f"{indent}def terminate(self):{eol}"
    # s += f"{indent}{indent}self.cmd('sysctl net.ipv4.ip_forward=0'){eol}"
    # s += f"{indent}{indent}super().terminate(){eol}"
    # s += eol
    ##########################################################################
    s += eol
    s += f'def _init(topo):{eol}'
    # switch
    s += f"{indent}info('*** Adding switches\\n'){eol}"
    for sw in sorted(switches, key=lambda a: int(a[1:])):
        s += f"{indent}{sw} = topo.addSwitch('{sw}', cls=OVSKernelSwitch){eol}"
    s += eol
    # hosts
    s += f"{indent}info('*** Adding hosts\\n'){eol}"
    for hs in sorted(hosts, key=lambda a: int(a[1:])):
        ip = id2ip(int(hs[1:])-1)
        s += f"{indent}{hs} = topo.addHost('{hs}', cls=Host, ip='{ip}', defaultRoute=None){eol}"
    s += eol
    # links
    s += f"{indent}info('*** Adding links\\n'){eol}"
    for i, v in enumerate(links):
        e1, e2, bw = v
        s += f"{indent}topo.addLink({e1}, {e2}, {i+1}, {i+1}, cls=TCLink, bw={bw}){eol}"
    s += eol
    ##########################################################################
    s += eol
    s += f'class MyTopo(Topo):{eol}'
    s += f'{indent}def __init__(self):{eol}'
    s += f'{indent}{indent}Topo.__init__(self){eol}'
    s += f'{indent}{indent}_init(self){eol}'
    s += eol
    ##########################################################################
    s += eol
    s += 'def myNetwork(standalone = False):'+eol
    s += f'{indent}net = Mininet({eol}'
    s += f'{indent}{indent}topo=None,{eol}'
    s += f'{indent}{indent}build=False,{eol}'
    s += f'{indent}{indent}ipBase="10.0.0.0/8"{eol}'
    s += f'{indent}){eol}'
    s += eol
    # controller
    s += f"{indent}info('*** Adding controller\\n'){eol}"
    s += f"{indent}c0=net.addController({eol}"
    s += f"{indent}{indent}name='c0',{eol}"
    s += f"{indent}{indent}controller=RemoteController,{eol}"
    s += f"{indent}{indent}ip='127.0.0.1',{eol}"
    s += f"{indent}{indent}protocol='tcp',{eol}"
    s += f"{indent}{indent}port=6633{eol}"
    s += f"{indent}){eol}"
    s += eol
    # Topology
    s += f"{indent}_init(net){eol}"
    s += eol
    # rest
    s += f"{indent}info('*** Starting network\\n'){eol}"
    s += f"{indent}net.build(){eol}"
    s += eol
    s += f"{indent}info('*** Starting controllers\\n'){eol}"
    s += f"{indent}for controller in net.controllers:{eol}"
    s += f"{indent}{indent}controller.start(){eol}"
    s += eol
    s += f"{indent}info('*** Starting switches\\n'){eol}"
    for sw in sorted(switches, key=lambda a: int(a[1:])):
        s += f"{indent}net.get('{sw}').start([c0]){eol}"
    s += eol
    s += f"{indent}if standalone:{eol}"
    s += f"{indent}{indent}info('*** Post configure switches and hosts\\n'){eol}"
    s += f"{indent}{indent}CLI(net){eol}"
    s += f"{indent}{indent}net.stop(){eol}"
    s += eol
    s += f"{indent}return net{eol}"
    # main
    s += eol
    ##########################################################################
    s += eol
    s += "topos = {'mytopo': MyTopo}"+eol
    s += eol
    ##########################################################################
    s += eol
    s += f'if __name__ == "__main__":{eol}'
    s += f'{indent}setLogLevel("info"){eol}'
    s += f'{indent}myNetwork(True){eol}'
    return s


def main(fn: str):
    topo = json.loads(Path(f'{fn}.json').read_text())
    rendered = render_topology(*topo)
    Path(f'{fn}.py').write_text(rendered)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fn = ' '.join(sys.argv[1:])
        main(fn)
    else:
        print("Usage:", file=sys.stderr)
        print(f"  {sys.argv[0]} <toponame>", file=sys.stderr)
        print(f"  <toponame>.json --> <toponame>.py", file=sys.stderr)
