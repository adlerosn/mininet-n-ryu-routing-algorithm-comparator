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
    topo.addLink(s1, s2, 1, 1, cls=TCLink, bw=1)
    topo.addLink(s2, s3, 2, 2, cls=TCLink, bw=1)
    topo.addLink(s3, s4, 3, 3, cls=TCLink, bw=1)
    topo.addLink(s4, h1, 4, 4, cls=TCLink, bw=1)
    topo.addLink(s4, h2, 5, 5, cls=TCLink, bw=1)
    topo.addLink(s3, s5, 6, 6, cls=TCLink, bw=1)
    topo.addLink(s5, h3, 7, 7, cls=TCLink, bw=1)
    topo.addLink(s5, h4, 8, 8, cls=TCLink, bw=1)
    topo.addLink(s2, s6, 9, 9, cls=TCLink, bw=1)
    topo.addLink(s6, s7, 10, 10, cls=TCLink, bw=1)
    topo.addLink(s7, h5, 11, 11, cls=TCLink, bw=1)
    topo.addLink(s7, h6, 12, 12, cls=TCLink, bw=1)
    topo.addLink(s6, s8, 13, 13, cls=TCLink, bw=1)
    topo.addLink(s8, h7, 14, 14, cls=TCLink, bw=1)
    topo.addLink(s8, h8, 15, 15, cls=TCLink, bw=1)
    topo.addLink(s1, s9, 16, 16, cls=TCLink, bw=1)
    topo.addLink(s9, s10, 17, 17, cls=TCLink, bw=1)
    topo.addLink(s10, s11, 18, 18, cls=TCLink, bw=1)
    topo.addLink(s11, h9, 19, 19, cls=TCLink, bw=1)
    topo.addLink(s11, h10, 20, 20, cls=TCLink, bw=1)
    topo.addLink(s10, s12, 21, 21, cls=TCLink, bw=1)
    topo.addLink(s12, h11, 22, 22, cls=TCLink, bw=1)
    topo.addLink(s12, h12, 23, 23, cls=TCLink, bw=1)
    topo.addLink(s9, s13, 24, 24, cls=TCLink, bw=1)
    topo.addLink(s13, s14, 25, 25, cls=TCLink, bw=1)
    topo.addLink(s14, h13, 26, 26, cls=TCLink, bw=1)
    topo.addLink(s14, h14, 27, 27, cls=TCLink, bw=1)
    topo.addLink(s13, s15, 28, 28, cls=TCLink, bw=1)
    topo.addLink(s15, h15, 29, 29, cls=TCLink, bw=1)
    topo.addLink(s15, h16, 30, 30, cls=TCLink, bw=1)


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

    if standalone:
        info('*** Post configure switches and hosts\n')
        CLI(net)
        net.stop()

    return net


topos = {'mytopo': MyTopo}


if __name__ == "__main__":
    setLogLevel("info")
    myNetwork(True)
