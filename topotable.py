#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import csv
import json
from csv2md import table_to_md as tbl2md
from io import StringIO
from pathlib import Path


def tbl2csv(tbl):
    conv = StringIO()
    csvw = csv.writer(conv)
    for row in tbl:
        csvw.writerow(list(map(str, row)))
    return conv.getvalue()


def float_fmt(f):
    return '%0.4f' % f


def kbps_fmt(f):
    return '%0.1f kbps' % (f/1000,)


def avg(itr):
    if len(itr) <= 0:
        return 0
    return sum(itr)/len(itr)


class Phrases:
    def __init__(self, d=dict()):
        self._d = d

    def __call__(self, val):
        return self[val]

    def __getitem__(self, val):
        return self._d.get(val, val)


def build_table(d, clmns, rws, fld, fmt, phrase_dict=dict()):
    phrases = Phrases(phrase_dict)
    tbl = [['' for x in range(len(clmns)+1)] for y in range(len(rws)+1)]
    for i, clmn in enumerate(clmns):
        tbl[0][i+1] = phrases[str(clmn)]
    for i, rw in enumerate(rws):
        tbl[i+1][0] = phrases[str(rw)]
    for x, clmn in enumerate(clmns):
        for y, rw in enumerate(rws):
            tbl[y+1][x+1] = fmt(d[clmn][rw][fld])
    tbl[0][0] = phrases[fld]
    return tbl


def main(target='.'):
    d = dict()
    for stat in Path(target).glob('*.autotest.json'):
        topo, algo = stat.name.split('.')[:-2]
        jsdata = json.loads(stat.read_text())
        spng = jsdata['sequential']['ping']['avg']
        ppng = jsdata['parallel']['ping']['avg']
        sprf = avg(jsdata['sequential']['iperfs'])
        pprf = avg(jsdata['parallel']['iperfs'])
        if topo not in d:
            d[topo] = dict()
        d[topo][algo] = {
            'sequential_ping': spng,
            'sequential_iperf': sprf,
            'parallel_ping': ppng,
            'parallel_iperf': pprf,
        }
    columns = sorted(list(d.keys()))
    rows = ['ospf', 'lowlat']
    fields = [
        'sequential_ping',
        'sequential_iperf',
        'parallel_ping',
        'parallel_iperf',
    ]
    for field in fields:
        formatter = float_fmt if 'ping' in field else kbps_fmt
        tbl = build_table(d, columns, rows, field, formatter)
        outcsvfile = Path(target).joinpath(f'autotest_table.{field}.csv')
        outmdfile = Path(target).joinpath(f'autotest_table.{field}.md')
        outcsvfile.write_text(tbl2csv(tbl))
        outmdfile.write_text(tbl2md(tbl))


if __name__ == "__main__":
    main()
