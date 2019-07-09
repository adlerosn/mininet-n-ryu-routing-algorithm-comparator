#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import json
from pathlib import Path
from counteriter import CounterIterator
from toporender import main as renderer

SPEED = 1
CORE = 3
PODS = 4
LEAFS = 2

hosts_iter = CounterIterator()
switch_iter = CounterIterator()


def reset_iters():
    global hosts_iter
    global switch_iter
    hosts_iter = CounterIterator()
    switch_iter = CounterIterator()

def sew_rows(I, J, bw=None):
    return [(i, j, bw) for i in I for j in J]

def create_edge_layer(root):
    this_hosts = []
    this_switches = []
    this_links = []
    for _ in range(LEAFS):
        this_hosts.append(f'h{next(hosts_iter)}')
        this_links.append((root, this_hosts[-1], SPEED))
    return this_hosts, this_switches, this_links

def create_aggregation_layer():
    this_hosts = []
    this_switches = []
    this_links = []
    outer_sws = [f's{next(switch_iter)}' for i in range(LEAFS)]
    inner_sws = [f's{next(switch_iter)}' for i in range(LEAFS)]
    this_links+=sew_rows(outer_sws, inner_sws, SPEED)
    for i in inner_sws:
        h,s,l = create_edge_layer(i)
        this_hosts += h
        this_switches += s
        this_links += l
    this_switches += outer_sws
    this_switches += inner_sws
    return this_hosts, this_switches, this_links


def create_topo():
    this_hosts = []
    this_switches = []
    this_links = []
    cores = [f's{next(switch_iter)}' for i in range(CORE)]
    pods_inner_sws = []
    for i in range(PODS):
        h, s, l = create_aggregation_layer()
        this_hosts += h
        this_switches += s
        this_links += l
        pods_inner_sws += s[:-LEAFS]
    this_links += sew_rows(pods_inner_sws, cores, SPEED)
    this_switches += cores
    return this_hosts, this_switches, this_links


def main(fn: str = 'fattree'):
    reset_iters()
    topo = create_topo()
    reset_iters()
    Path(f'{fn}.json').write_text(json.dumps(topo))
    renderer(fn)


if __name__ == '__main__':
    main()
