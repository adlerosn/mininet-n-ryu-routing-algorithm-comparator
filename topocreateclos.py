#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import json
from pathlib import Path
from counteriter import CounterIterator
from toporender import main as renderer

# Based on and semantically equivalent to:
# https://github.com/HSRNetwork/Cloudlnf_Lab10_ryu/blob/master/mininetClosStartup.py

SPINE_SPEED = 1
LEAF_SPEED = 1

SPINE_COUNT = 3
LEAF_COUNT = 8
HOST_LEAF = 2

hosts_iter = CounterIterator()
switch_iter = CounterIterator()


def reset_iters():
    global hosts_iter
    global switch_iter
    hosts_iter = CounterIterator()
    switch_iter = CounterIterator()


def create_topo():
    this_hosts = []
    this_switches = []
    this_links = []
    spines = list()
    leafs = list()
    for _ in range(LEAF_COUNT):
        s = f"s{next(switch_iter)}"
        leafs.append(s)
        this_switches.append(s)
        for __ in range(HOST_LEAF):
            h = f"h{next(hosts_iter)}"
            this_hosts.append(h)
            this_links.append((s, h, LEAF_SPEED))
    for _ in range(SPINE_COUNT):
        s = f"s{next(switch_iter)}"
        spines.append(s)
        this_switches.append(s)
    for spine in spines:
        for leaf in leafs:
            this_links.append((spine, leaf, SPINE_SPEED))
    return this_hosts, this_switches, this_links


def main(fn: str = 'clos'):
    reset_iters()
    topo = create_topo()
    reset_iters()
    Path(f'{fn}.json').write_text(json.dumps(topo))
    renderer(fn)


if __name__ == '__main__':
    main()
