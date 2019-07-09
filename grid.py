#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call


def _init(topo):
    info('*** Adding switches\n')
    s1 = topo.addSwitch('s1', cls=OVSKernelSwitch)
    s2 = topo.addSwitch('s2', cls=OVSKernelSwitch)
    s3 = topo.addSwitch('s3', cls=OVSKernelSwitch)
    s4 = topo.addSwitch('s4', cls=OVSKernelSwitch)
    s5 = topo.addSwitch('s5', cls=OVSKernelSwitch)
    s6 = topo.addSwitch('s6', cls=OVSKernelSwitch)
    s7 = topo.addSwitch('s7', cls=OVSKernelSwitch)
    s8 = topo.addSwitch('s8', cls=OVSKernelSwitch)
    s9 = topo.addSwitch('s9', cls=OVSKernelSwitch)
    s10 = topo.addSwitch('s10', cls=OVSKernelSwitch)
    s11 = topo.addSwitch('s11', cls=OVSKernelSwitch)
    s12 = topo.addSwitch('s12', cls=OVSKernelSwitch)
    s13 = topo.addSwitch('s13', cls=OVSKernelSwitch)
    s14 = topo.addSwitch('s14', cls=OVSKernelSwitch)
    s15 = topo.addSwitch('s15', cls=OVSKernelSwitch)
    s16 = topo.addSwitch('s16', cls=OVSKernelSwitch)

    info('*** Adding hosts\n')
    h1 = topo.addHost('h1', cls=Host, ip='10.0.0.1', defaultRoute=None)
    h2 = topo.addHost('h2', cls=Host, ip='10.0.0.2', defaultRoute=None)
    h3 = topo.addHost('h3', cls=Host, ip='10.0.0.3', defaultRoute=None)
    h4 = topo.addHost('h4', cls=Host, ip='10.0.0.4', defaultRoute=None)
    h5 = topo.addHost('h5', cls=Host, ip='10.0.0.5', defaultRoute=None)
    h6 = topo.addHost('h6', cls=Host, ip='10.0.0.6', defaultRoute=None)
    h7 = topo.addHost('h7', cls=Host, ip='10.0.0.7', defaultRoute=None)
    h8 = topo.addHost('h8', cls=Host, ip='10.0.0.8', defaultRoute=None)
    h9 = topo.addHost('h9', cls=Host, ip='10.0.0.9', defaultRoute=None)
    h10 = topo.addHost('h10', cls=Host, ip='10.0.0.10', defaultRoute=None)
    h11 = topo.addHost('h11', cls=Host, ip='10.0.0.11', defaultRoute=None)
    h12 = topo.addHost('h12', cls=Host, ip='10.0.0.12', defaultRoute=None)
    h13 = topo.addHost('h13', cls=Host, ip='10.0.0.13', defaultRoute=None)
    h14 = topo.addHost('h14', cls=Host, ip='10.0.0.14', defaultRoute=None)
    h15 = topo.addHost('h15', cls=Host, ip='10.0.0.15', defaultRoute=None)
    h16 = topo.addHost('h16', cls=Host, ip='10.0.0.16', defaultRoute=None)

    info('*** Adding links\n')
    topo.addLink(h1, s1, 1, 1, cls=TCLink, bw=1)
    topo.addLink(h2, s2, 2, 2, cls=TCLink, bw=1)
    topo.addLink(s2, s1, 3, 3, cls=TCLink, bw=1)
    topo.addLink(h3, s3, 4, 4, cls=TCLink, bw=1)
    topo.addLink(s3, s2, 5, 5, cls=TCLink, bw=1)
    topo.addLink(h4, s4, 6, 6, cls=TCLink, bw=1)
    topo.addLink(s4, s3, 7, 7, cls=TCLink, bw=1)
    topo.addLink(h5, s5, 8, 8, cls=TCLink, bw=1)
    topo.addLink(h6, s6, 9, 9, cls=TCLink, bw=1)
    topo.addLink(s6, s5, 10, 10, cls=TCLink, bw=1)
    topo.addLink(h7, s7, 11, 11, cls=TCLink, bw=1)
    topo.addLink(s7, s6, 12, 12, cls=TCLink, bw=1)
    topo.addLink(h8, s8, 13, 13, cls=TCLink, bw=1)
    topo.addLink(s8, s7, 14, 14, cls=TCLink, bw=1)
    topo.addLink(s1, s5, 15, 15, cls=TCLink, bw=1)
    topo.addLink(s2, s6, 16, 16, cls=TCLink, bw=1)
    topo.addLink(s3, s7, 17, 17, cls=TCLink, bw=1)
    topo.addLink(s4, s8, 18, 18, cls=TCLink, bw=1)
    topo.addLink(h9, s9, 19, 19, cls=TCLink, bw=1)
    topo.addLink(h10, s10, 20, 20, cls=TCLink, bw=1)
    topo.addLink(s10, s9, 21, 21, cls=TCLink, bw=1)
    topo.addLink(h11, s11, 22, 22, cls=TCLink, bw=1)
    topo.addLink(s11, s10, 23, 23, cls=TCLink, bw=1)
    topo.addLink(h12, s12, 24, 24, cls=TCLink, bw=1)
    topo.addLink(s12, s11, 25, 25, cls=TCLink, bw=1)
    topo.addLink(s5, s9, 26, 26, cls=TCLink, bw=1)
    topo.addLink(s6, s10, 27, 27, cls=TCLink, bw=1)
    topo.addLink(s7, s11, 28, 28, cls=TCLink, bw=1)
    topo.addLink(s8, s12, 29, 29, cls=TCLink, bw=1)
    topo.addLink(h13, s13, 30, 30, cls=TCLink, bw=1)
    topo.addLink(h14, s14, 31, 31, cls=TCLink, bw=1)
    topo.addLink(s14, s13, 32, 32, cls=TCLink, bw=1)
    topo.addLink(h15, s15, 33, 33, cls=TCLink, bw=1)
    topo.addLink(s15, s14, 34, 34, cls=TCLink, bw=1)
    topo.addLink(h16, s16, 35, 35, cls=TCLink, bw=1)
    topo.addLink(s16, s15, 36, 36, cls=TCLink, bw=1)
    topo.addLink(s9, s13, 37, 37, cls=TCLink, bw=1)
    topo.addLink(s10, s14, 38, 38, cls=TCLink, bw=1)
    topo.addLink(s11, s15, 39, 39, cls=TCLink, bw=1)
    topo.addLink(s12, s16, 40, 40, cls=TCLink, bw=1)


class MyTopo(Topo):
    def __init__(self):
        Topo.__init__(self)
        _init(self)


def myNetwork(standalone = False):
    net = Mininet(
        topo=None,
        build=False,
        ipBase="10.0.0.0/8"
    )

    info('*** Adding controller\n')
    c0=net.addController(
        name='c0',
        controller=RemoteController,
        ip='127.0.0.1',
        protocol='tcp',
        port=6633
    )

    _init(net)

    info('*** Starting network\n')
    net.build()

    info('*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info('*** Starting switches\n')
    net.get('s1').start([c0])
    net.get('s2').start([c0])
    net.get('s3').start([c0])
    net.get('s4').start([c0])
    net.get('s5').start([c0])
    net.get('s6').start([c0])
    net.get('s7').start([c0])
    net.get('s8').start([c0])
    net.get('s9').start([c0])
    net.get('s10').start([c0])
    net.get('s11').start([c0])
    net.get('s12').start([c0])
    net.get('s13').start([c0])
    net.get('s14').start([c0])
    net.get('s15').start([c0])
    net.get('s16').start([c0])

    if standalone:
        info('*** Post configure switches and hosts\n')
        CLI(net)
        net.stop()

    return net


topos = {'mytopo': MyTopo}


if __name__ == "__main__":
    setLogLevel("info")
    myNetwork(True)
