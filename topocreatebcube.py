#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import json
from pathlib import Path
from counteriter import CounterIterator
from toporender import main as renderer

SPEED = 1
PODS = 4

hosts_iter = CounterIterator()
switch_iter = CounterIterator()


def reset_iters():
    global hosts_iter
    global switch_iter
    hosts_iter = CounterIterator()
    switch_iter = CounterIterator()


def sew_rows(r1, r2, bw=None):
    return [(i, j, bw) for i in r1 for j in r2]


def create_pod():
    this_hosts = []
    this_switches = []
    this_links = []
    sw = f's{next(switch_iter)}'
    hosts = [f'h{next(hosts_iter)}' for _ in range(PODS)]
    this_hosts += hosts
    this_switches += [sw]
    this_links += sew_rows([sw], hosts, SPEED)
    return this_hosts, this_switches, this_links


def create_topo():
    this_hosts = []
    this_switches = []
    this_links = []
    spines = [f's{next(switch_iter)}' for _ in range(PODS)]
    stategic = []
    for i in range(PODS):
        h, s, l = create_pod()
        this_hosts += h
        this_switches += s
        this_links += l
        stategic.append(h[-PODS:])
    this_links += [(i[0], i[1], SPEED) for l in stategic for i in zip(spines, l)]
    this_switches += spines
    return this_hosts, this_switches, this_links


def main(fn: str = 'bcube'):
    reset_iters()
    topo = create_topo()
    reset_iters()
    Path(f'{fn}.json').write_text(json.dumps(topo))
    renderer(fn)


if __name__ == '__main__':
    main()
