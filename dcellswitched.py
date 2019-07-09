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
    s17 = topo.addSwitch('s17', cls=OVSKernelSwitch)
    s18 = topo.addSwitch('s18', cls=OVSKernelSwitch)
    s19 = topo.addSwitch('s19', cls=OVSKernelSwitch)
    s20 = topo.addSwitch('s20', cls=OVSKernelSwitch)
    s21 = topo.addSwitch('s21', cls=OVSKernelSwitch)
    s22 = topo.addSwitch('s22', cls=OVSKernelSwitch)
    s23 = topo.addSwitch('s23', cls=OVSKernelSwitch)
    s24 = topo.addSwitch('s24', cls=OVSKernelSwitch)
    s25 = topo.addSwitch('s25', cls=OVSKernelSwitch)

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
    h17 = topo.addHost('h17', cls=Host, ip='10.0.0.17', defaultRoute=None)
    h18 = topo.addHost('h18', cls=Host, ip='10.0.0.18', defaultRoute=None)
    h19 = topo.addHost('h19', cls=Host, ip='10.0.0.19', defaultRoute=None)
    h20 = topo.addHost('h20', cls=Host, ip='10.0.0.20', defaultRoute=None)

    info('*** Adding links\n')
    topo.addLink(s2, h1, 1, 1, cls=TCLink, bw=1)
    topo.addLink(s3, h2, 2, 2, cls=TCLink, bw=1)
    topo.addLink(s4, h3, 3, 3, cls=TCLink, bw=1)
    topo.addLink(s5, h4, 4, 4, cls=TCLink, bw=1)
    topo.addLink(s1, s2, 5, 5, cls=TCLink, bw=1)
    topo.addLink(s1, s3, 6, 6, cls=TCLink, bw=1)
    topo.addLink(s1, s4, 7, 7, cls=TCLink, bw=1)
    topo.addLink(s1, s5, 8, 8, cls=TCLink, bw=1)
    topo.addLink(s7, h5, 9, 9, cls=TCLink, bw=1)
    topo.addLink(s8, h6, 10, 10, cls=TCLink, bw=1)
    topo.addLink(s9, h7, 11, 11, cls=TCLink, bw=1)
    topo.addLink(s10, h8, 12, 12, cls=TCLink, bw=1)
    topo.addLink(s6, s7, 13, 13, cls=TCLink, bw=1)
    topo.addLink(s6, s8, 14, 14, cls=TCLink, bw=1)
    topo.addLink(s6, s9, 15, 15, cls=TCLink, bw=1)
    topo.addLink(s6, s10, 16, 16, cls=TCLink, bw=1)
    topo.addLink(s12, h9, 17, 17, cls=TCLink, bw=1)
    topo.addLink(s13, h10, 18, 18, cls=TCLink, bw=1)
    topo.addLink(s14, h11, 19, 19, cls=TCLink, bw=1)
    topo.addLink(s15, h12, 20, 20, cls=TCLink, bw=1)
    topo.addLink(s11, s12, 21, 21, cls=TCLink, bw=1)
    topo.addLink(s11, s13, 22, 22, cls=TCLink, bw=1)
    topo.addLink(s11, s14, 23, 23, cls=TCLink, bw=1)
    topo.addLink(s11, s15, 24, 24, cls=TCLink, bw=1)
    topo.addLink(s17, h13, 25, 25, cls=TCLink, bw=1)
    topo.addLink(s18, h14, 26, 26, cls=TCLink, bw=1)
    topo.addLink(s19, h15, 27, 27, cls=TCLink, bw=1)
    topo.addLink(s20, h16, 28, 28, cls=TCLink, bw=1)
    topo.addLink(s16, s17, 29, 29, cls=TCLink, bw=1)
    topo.addLink(s16, s18, 30, 30, cls=TCLink, bw=1)
    topo.addLink(s16, s19, 31, 31, cls=TCLink, bw=1)
    topo.addLink(s16, s20, 32, 32, cls=TCLink, bw=1)
    topo.addLink(s22, h17, 33, 33, cls=TCLink, bw=1)
    topo.addLink(s23, h18, 34, 34, cls=TCLink, bw=1)
    topo.addLink(s24, h19, 35, 35, cls=TCLink, bw=1)
    topo.addLink(s25, h20, 36, 36, cls=TCLink, bw=1)
    topo.addLink(s21, s22, 37, 37, cls=TCLink, bw=1)
    topo.addLink(s21, s23, 38, 38, cls=TCLink, bw=1)
    topo.addLink(s21, s24, 39, 39, cls=TCLink, bw=1)
    topo.addLink(s21, s25, 40, 40, cls=TCLink, bw=1)
    topo.addLink(s2, s7, 41, 41, cls=TCLink, bw=1)
    topo.addLink(s3, s12, 42, 42, cls=TCLink, bw=1)
    topo.addLink(s4, s17, 43, 43, cls=TCLink, bw=1)
    topo.addLink(s5, s22, 44, 44, cls=TCLink, bw=1)
    topo.addLink(s8, s13, 45, 45, cls=TCLink, bw=1)
    topo.addLink(s9, s18, 46, 46, cls=TCLink, bw=1)
    topo.addLink(s10, s23, 47, 47, cls=TCLink, bw=1)
    topo.addLink(s14, s19, 48, 48, cls=TCLink, bw=1)
    topo.addLink(s15, s24, 49, 49, cls=TCLink, bw=1)
    topo.addLink(s20, s25, 50, 50, cls=TCLink, bw=1)


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
    net.get('s17').start([c0])
    net.get('s18').start([c0])
    net.get('s19').start([c0])
    net.get('s20').start([c0])
    net.get('s21').start([c0])
    net.get('s22').start([c0])
    net.get('s23').start([c0])
    net.get('s24').start([c0])
    net.get('s25').start([c0])

    if standalone:
        info('*** Post configure switches and hosts\n')
        CLI(net)
        net.stop()

    return net


topos = {'mytopo': MyTopo}


if __name__ == "__main__":
    setLogLevel("info")
    myNetwork(True)
