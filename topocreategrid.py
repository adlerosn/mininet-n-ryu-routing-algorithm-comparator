#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import json
from pathlib import Path
from counteriter import CounterIterator
from toporender import main as renderer

SPEED = 1
ROWS = 4
COLUMNS = 4

hosts_iter = CounterIterator()
switch_iter = CounterIterator()


def reset_iters():
    global hosts_iter
    global switch_iter
    hosts_iter = CounterIterator()
    switch_iter = CounterIterator()


def host():
    return f"h{next(hosts_iter)}"

def switch():
    return f"s{next(switch_iter)}"

def create_switchhost():
    this_hosts = [host()]
    this_switches = [switch()]
    this_links = [(this_hosts[0], this_switches[0], SPEED)]
    return this_hosts, this_switches, this_links


def create_row():
    this_hosts = []
    this_switches = []
    this_links = []
    previous = None
    for _ in range(COLUMNS):
        h, s, l = create_switchhost()
        this_hosts += h
        this_switches += s
        this_links += l
        if previous is not None:
            this_links.append((s[-1], previous, SPEED))
        previous = s[-1]

    return this_hosts, this_switches, this_links


def create_rows():
    this_hosts = []
    this_switches = []
    this_links = []
    previous = None
    for _ in range(ROWS):
        h, s, l = create_row()
        this_hosts += h
        this_switches += s
        this_links += l
        if previous is not None:
            current = s[-COLUMNS:]
            for p, c in zip(previous, current):
                this_links.append((p, c, SPEED))
        previous = s[-COLUMNS:]
    return this_hosts, this_switches, this_links


def create_topo():
    return create_rows()


def main(fn: str = 'grid'):
    reset_iters()
    topo = create_topo()
    reset_iters()
    Path(f'{fn}.json').write_text(json.dumps(topo))
    renderer(fn)


if __name__ == '__main__':
    main()
