#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import json
from pathlib import Path
from counteriter import CounterIterator
from toporender import main as renderer

SPEED = 1
HPC = 4
HPS = 1

CELLS = HPC+1

hosts_iter = CounterIterator()
switch_iter = CounterIterator()


def reset_iters():
    global hosts_iter
    global switch_iter
    hosts_iter = CounterIterator()
    switch_iter = CounterIterator()


def circular_rshift(sbs, i):
    ai = i % len(sbs)
    return sbs[ai:]+sbs[:ai]


def filter_not(func, iterable):
    return filter(lambda a: not func(a), iterable)


def sew_rows(r1, r2, bw=None):
    return [(i, j, bw) for i in r1 for j in r2]


def create_edge_layer(root):
    this_hosts = []
    this_switches = []
    this_links = []
    for _ in range(HPS):
        h = f'h{next(hosts_iter)}'
        this_hosts.append(h)
        this_links.append((root, h, SPEED))
    return this_hosts, this_switches, this_links


def create_cell():
    this_hosts = []
    this_switches = []
    this_links = []
    sw = f's{next(switch_iter)}'
    hosts = [f's{next(switch_iter)}' for _ in range(HPC)]
    for swh in hosts:
        h, s, l = create_edge_layer(swh)
        this_hosts += h
        this_switches += s
        this_links += l
    this_switches += [sw]
    this_links += sew_rows([sw], hosts, SPEED)
    this_switches += hosts
    return this_hosts, this_switches, this_links


def create_topo():
    this_hosts = []
    this_switches = []
    this_links = []
    stategic = []
    for _ in range(CELLS):
        h, s, l = create_cell()
        this_hosts += h
        this_switches += s
        this_links += l
        stategic.append(s[-HPC:])
    processed = list()
    for i, cell in enumerate(stategic):
        cells_taken_by_this_cell = []
        while not all(map(processed.__contains__, cell)):
            h1, *_ = filter_not(processed.__contains__, cell)
            for j, cell2 in enumerate(stategic):
                if i >= j:
                    continue
                if j in cells_taken_by_this_cell:
                    continue
                h2, *_ = filter_not(processed.__contains__, cell2)
                this_links.append((h1, h2, SPEED))
                processed += [h1, h2]
                cells_taken_by_this_cell.append(j)
                break
    return this_hosts, this_switches, this_links


def main(fn: str = 'dcellswitched'):
    reset_iters()
    topo = create_topo()
    reset_iters()
    Path(f'{fn}.json').write_text(json.dumps(topo))
    renderer(fn)


if __name__ == '__main__':
    main()
