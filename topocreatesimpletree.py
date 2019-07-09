#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import json
from pathlib import Path
from counteriter import CounterIterator
from toporender import main as renderer

SPEED = 1
LEVELS = 3

hosts_iter = CounterIterator()
switch_iter = CounterIterator()


def reset_iters():
    global hosts_iter
    global switch_iter
    hosts_iter = CounterIterator()
    switch_iter = CounterIterator()


def create_tree(root, levels_coming=0):
    this_hosts = []
    this_switches = []
    this_links = []
    for _ in range(2):
        if levels_coming <= 0:
            this_hosts.append(f'h{next(hosts_iter)}')
            this_links.append((root, this_hosts[-1], SPEED))
        else:
            this_switches.append(f's{next(switch_iter)}')
            this_links.append((root, this_switches[-1], SPEED))
            h, s, l = create_tree(this_switches[-1], levels_coming-1)
            this_hosts += h
            this_switches += s
            this_links += l
    return this_hosts, this_switches, this_links


def create_topo():
    this_hosts = []
    this_switches = []
    this_links = []
    root = f's{next(switch_iter)}'
    this_switches.append(root)
    h, s, l = create_tree(root, LEVELS)
    this_hosts += h
    this_switches += s
    this_links += l
    return this_hosts, this_switches, this_links


def main(fn: str = 'simpletree'):
    reset_iters()
    topo = create_topo()
    reset_iters()
    Path(f'{fn}.json').write_text(json.dumps(topo))
    renderer(fn)


if __name__ == '__main__':
    main()
