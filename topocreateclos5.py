#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import json
from pathlib import Path
from counteriter import CounterIterator
from toporender import main as renderer

hosts_per_leaf = 2
k = [4,2,2,2,4]
k_bw = 1
h_bw = 1

hosts_iter = CounterIterator()
switch_iter = CounterIterator()


def reset_iters():
    global hosts_iter
    global switch_iter
    hosts_iter = CounterIterator()
    switch_iter = CounterIterator()


def create_row(i):
    return [f"s{next(switch_iter)}" for _ in range(i)]


def sew_rows(r1, r2, bw=None):
    return [(i, j, bw) for i in r1 for j in r2]


def create_topo():
    this_hosts = []
    this_switches = []
    this_links = []
    last_row = []
    for row in map(create_row, k):
        if len(last_row) <= 0:
            for sw in row:
                for _ in range(hosts_per_leaf):
                    h = f"h{next(hosts_iter)}"
                    this_hosts.append(h)
                    this_links.append((h, sw, h_bw))
        else:
            for sw in row:
                for lsw in last_row:
                    this_links.append((sw, lsw, k_bw))
        this_switches += row
        last_row = row
    for sw in last_row:
        for _ in range(hosts_per_leaf):
            h = f"h{next(hosts_iter)}"
            this_hosts.append(h)
            this_links.append((h, sw, h_bw))
    return this_hosts, this_switches, this_links


def main(fn: str = 'clos5'):
    reset_iters()
    topo = create_topo()
    reset_iters()
    Path(f'{fn}.json').write_text(json.dumps(topo))
    renderer(fn)


if __name__ == '__main__':
    main()
