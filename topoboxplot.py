#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys
import json
import ternary
import numpy as np
from matplotlib import pyplot as plt
from pathlib import Path
from operator import sub
from topotable import tbl2md
from topotable import tbl2csv
from topotable import build_table
from topotable import Phrases


def sub_itr(itr):
    return sub(*itr)


def listfind(self: list, search):
    try:
        return self.index(search)
    except ValueError:
        return -1


def tbl2tex(table):
    columns = len(table[0])
    clh = 'l|'+'c'*(columns-1)
    head, _, *tail = [
        x[2:]
        for x in (
            tbl2md(table)
            .replace('|', '&')
            .replace('&\n', '\\\\\n')
            [:-1]+'\\\\\n'
        ).splitlines()
    ]
    return (
        '\\rowcolors{1}{white}{black!10!white}\n' +
        '\\begin{tabular}{' + clh + '}\n' +
        '\n'.join([head, '\\hline', *tail]) +
        '\n\\end{tabular}'
    )


def avg(itr, ifempty=0):
    if len(itr) == 0:
        return ifempty
    else:
        return sum(itr)/len(itr)


def flatten(itr):
    return [el for subitr in itr for el in subitr]


def make_boxplot(data, labels, ylabel=None, title=None, rotate_x=False):
    fig, ax = plt.subplots()
    ax.grid(True)
    red_cross = dict(markeredgecolor='r', alpha=0.5, marker='x')
    meanpointprops = dict(
        marker='D',
        markeredgecolor='navy',
        markerfacecolor='dodgerblue'
    )
    medianprops = dict(
        color='green',
        linewidth=2.5
    )
    ax.boxplot(
        data,
        labels=labels,
        flierprops=red_cross,
        meanprops=meanpointprops,
        medianprops=medianprops,
        showmeans=True
    )
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    if title is not None:
        ax.set_title(title)
    if rotate_x:
        plt.xticks(rotation=45, horizontalalignment='right')
    return ax


FMT_LATENCY = (lambda a: '%.2f ms' % (a,),)[0]
FMT_SPEED = (lambda a: '%0.1f kbps' % (a/1000,),)[0]
FMT_SEC = (lambda a: '%0.1f s' % (a,),)[0]
FMT_PASSTHROUGH = (lambda a: a,)[0]
FMT_STRING = (lambda a: str(a),)[0]

FMTS = {
    'sl': FMT_LATENCY,
    'pl': FMT_LATENCY,
    'il': FMT_LATENCY,
    'sj': FMT_LATENCY,
    'pj': FMT_LATENCY,
    'ij': FMT_LATENCY,
    'sb': FMT_SPEED,
    'pb': FMT_SPEED,
    'ib': FMT_SPEED,
    'rd': FMT_SEC,
}

FMTS_YLABEL = {
    'sl': 'milisseconds',
    'pl': 'milisseconds',
    'il': 'milisseconds',
    'sj': 'milisseconds',
    'pj': 'milisseconds',
    'ij': 'milisseconds',
    'sb': 'kilobits per second',
    'pb': 'kilobits per second',
    'ib': 'kilobits per second',
    'rd': 'seconds',
}

FMTS_YSCALEMULTIPLIER = {
    'sl': 1,
    'pl': 1,
    'il': 1,
    'sj': 1,
    'pj': 1,
    'ij': 1,
    'sb': 1/1000,
    'pb': 1/1000,
    'ib': 1/1000,
    'rd': 1,
}

PHRASES = {
    'sl': 'Latency (sequential)',
    'pl': 'Latency (concurrent)',
    'il': 'Latency (impact)',
    'sj': 'Jitter (sequential)',
    'pj': 'Jitter (concurrent)',
    'ij': 'Jitter (impact)',
    'sb': 'Bandwidth (sequential)',
    'pb': 'Bandwidth (concurrent)',
    'ib': 'Bandwidth (impact)',
    'rd': 'Routing response time',

    'ospf': 'OSPF (single-path)',
    'ecmp': 'ECMP (multi-path)',
    'ldr': 'LDR (multi-path)',
    'minmax-single': 'MinMax (single-path)',
    'ldr-single': 'LDR (single-path)',

    'all': 'All',

    'clos': '3-layered CLOS',
    'clos5': '5-layered CLOS',
    'grid': 'Grid',
    'simpletree': 'Binary Tree',
    'fattree': 'Fat Tree',
    'bipartite': 'Bipartite',
    'principle': 'Triangle',
    'dcell': 'D-Cell',
    'dcellswitched': 'D-Cell',
    'bcube': 'B-Cube',
    'bcubeswitched': 'B-Cube',
}

PHRASES_BOXPLOT_PATCH = {
    'ospf': 'OSPF (SP)',
    'ecmp': 'ECMP (MP)',
    'ldr': 'LDR (MP)',
    'minmax-single': 'MinMax (SP)',
    'ldr-single': 'LDR (SP)',

    'clos': 'CLOS-3',
    'clos5': 'CLOS-5',
    'grid': 'Grid',
    'simpletree': 'Bin Tree',
    'fattree': 'Fat Tree',
    'bipartite': 'Bipartite',
    'principle': 'Triangle',
}

ALGOS_PREFERRED_ORDER = [
    'ospf',
    'ldr-single',
    'minmax-single',
    'ldr',
    'ecmp',
]

TOPOS_PREFERRED_ORDER = [
    'simpletree',
    'clos5',
    'bcubeswitched',
    'bcube',
    'fattree',
    'grid',
    'dcellswitched',
    'dcell',
    'bipartite',
    'clos',
    'principle',
]

MARKERS = [  # <https://matplotlib.org/3.1.0/api/markers_api.html>
    "D",  # m19 	diamond
    "o",  # m02 	circle
    ".",  # m00 	point
    "*",  # m14 	star
    "x",  # m18 	x
    "d",  # m20 	thin_diamond
    "X",  # m24 	x (filled)
    "+",  # m17 	plus
    "v",  # m03 	triangle_down
    "p",  # m13 	pentagon
    "^",  # m04 	triangle_up
    "<",  # m05 	triangle_left
    ">",  # m06 	triangle_right
    "1",  # m07 	tri_down
    "2",  # m08 	tri_up
    "3",  # m09 	tri_left
    "4",  # m10 	tri_right
    "8",  # m11 	octagon
    "s",  # m12 	square
    "P",  # m23 	plus (filled)
    "h",  # m15 	hexagon1
    "H",  # m16 	hexagon2
    "|",  # m21 	vline
    "_",  # m22 	hline
    ",",  # m01 	pixel
]

COLORS = [  # <https://matplotlib.org/2.0.0/examples/color/named_colors.html>
    'orange',
    'c',
    'magenta',
    'green',
    'blue',
    'm',
    'gold',
]


def main(results, outfolder):
    algos_raw = list(results.keys())
    topos_raw = list(results.values().__iter__().__next__().keys())
    algos = list(sorted(
        algos_raw,
        key=lambda a: (listfind(ALGOS_PREFERRED_ORDER, a), a)
    ))
    topos = list(sorted(
        topos_raw,
        key=lambda a: (listfind(TOPOS_PREFERRED_ORDER, a), a)
    ))
    metrics = ['sl', 'sj', 'sb', 'pl', 'pj', 'pb', 'il', 'ij', 'ib', 'rd']
    db = {
        algo: {
            topo: {
                'sl': [res['sequential']['ping']['avg'] for res in results[algo][topo]],
                'sj': [res['sequential']['ping']['mdev'] for res in results[algo][topo]],
                'sb': [avg(res['sequential']['iperfs']) for res in results[algo][topo]],
                'pl': [res['parallel']['ping']['avg'] for res in results[algo][topo]],
                'pj': [res['parallel']['ping']['mdev'] for res in results[algo][topo]],
                'pb': [avg(res['parallel']['iperfs']) for res in results[algo][topo]],
                'rd': [res['routing_time'] for res in results[algo][topo]],
            } for topo in topos
        } for algo in algos}
    db = {
        algo: {
            topo: {
                **db[algo][topo],
                'il': list(map(sub_itr, zip(db[algo][topo]['pl'], db[algo][topo]['sl']))),
                'ij': list(map(sub_itr, zip(db[algo][topo]['pj'], db[algo][topo]['sj']))),
                'ib': list(map(sub_itr, zip(db[algo][topo]['pb'], db[algo][topo]['sb']))),
            } for topo in topos
        } for algo in algos}
    db = {
        algo: {
            topo: db[algo][topo] if topo != 'all' else dict([
                (metric, flatten([
                    db[algo][topo2][metric]
                    for topo2 in topos
                ]))
                for metric in metrics
            ])
            for topo in [*topos, 'all']
        } for algo in algos}
    topos = [*topos, 'all']
    db = {
        algo: {
            topo: db[algo][topo] if algo != 'all' else dict([
                (metric, flatten([
                    db[algo2][topo][metric]
                    for algo2 in algos
                ]))
                for metric in metrics
            ])
            for topo in topos
        } for algo in [*algos, 'all']}
    algos = [*algos, 'all']
    avgdb = {
        algo: {
            topo: {
                persp: avg(db[algo][topo][persp])
                for persp in metrics
            } for topo in topos
        } for algo in algos}
    avgdiffdb = {
        algo: {
            topo: {
                persp: avgdb[algo][topo][persp] - avgdb['all'][topo][persp]
                for persp in metrics
            } for topo in topos
        } for algo in algos if algo != 'all'}
    for metric in metrics:
        formatter = FMTS[metric]
        for prefix, tbl in [
            ('avg', build_table(avgdb, algos, topos, metric, formatter, PHRASES)),
            ('avgdiff', build_table(avgdiffdb, [algo for algo in algos if algo != 'all'], topos, metric, formatter, PHRASES))
        ]:
            outtexfile = Path(outfolder).joinpath(f'{prefix}_{metric}.tex')
            outcsvfile = Path(outfolder).joinpath(f'{prefix}_{metric}.csv')
            outmdfile = Path(outfolder).joinpath(f'{prefix}_{metric}.md')
            outtexfile.write_text(tbl2tex(tbl))
            outcsvfile.write_text(tbl2csv(tbl))
            outmdfile.write_text(tbl2md(tbl))
    longer_phrases = Phrases(PHRASES)
    phrases = Phrases({**PHRASES, **PHRASES_BOXPLOT_PATCH})
    for algo in algos:
        for metric in metrics:
            ylabel = FMTS_YLABEL[metric]
            yscalemultiplier = FMTS_YSCALEMULTIPLIER[metric]
            thistopos = [topo for topo in topos if topo != "all"]
            data = [
                sorted([
                    y*yscalemultiplier
                    for y in db[algo][topo][metric]
                ], reverse=True)
                for topo in thistopos
            ]
            bp = make_boxplot(
                data,
                [phrases[x] for x in thistopos],
                ylabel,
                f"{longer_phrases[metric]} using {longer_phrases[algo]}",
                True
            )
            bp.figure.savefig(
                outfolder.joinpath(f"am_{algo}_{metric}.pdf"),
                bbox_inches='tight'
            )
            plt.cla()
            plt.clf()
            plt.close()
            print(f"am_{algo}_{metric}.pdf")
    for topo in topos:
        for metric in metrics:
            ylabel = FMTS_YLABEL[metric]
            yscalemultiplier = FMTS_YSCALEMULTIPLIER[metric]
            thisalgos = [algo for algo in algos if algo != "all"]
            data = [
                sorted([
                    y*yscalemultiplier
                    for y in db[algo][topo][metric]
                ], reverse=True)
                for algo in thisalgos
            ]
            bp = make_boxplot(
                data,
                [phrases[x] for x in thisalgos],
                ylabel,
                f"{longer_phrases[metric]} on {longer_phrases[topo]}"
            )
            bp.figure.savefig(
                outfolder.joinpath(f"tm_{topo}_{metric}.pdf"),
                bbox_inches='tight'
            )
            plt.cla()
            plt.clf()
            plt.close()
            print(f"tm_{topo}_{metric}.pdf")
    for flavour in 'ps':
        for topo in topos:
            _, ax = plt.subplots()
            ax.axis('off')
            tax = ternary.TernaryAxesSubplot(ax=ax, scale=1)
            tax.gridlines(multiple=0.1, color="gray")
            tax.boundary(linewidth=2.0)
            allthistopo = db['all'][topo]
            minl = min(allthistopo[flavour+'l'])
            minj = min(allthistopo[flavour+'j'])
            minb = min(allthistopo[flavour+'b'])
            maxl = max(allthistopo[flavour+'l'])
            maxj = max(allthistopo[flavour+'j'])
            maxb = max(allthistopo[flavour+'b'])
            dltl = maxl-minl
            dltj = maxj-minj
            dltb = maxb-minb
            dltl = dltl if dltl != 0 else 1
            dltj = dltj if dltj != 0 else 1
            dltb = dltb if dltb != 0 else 1
            for i, algo in enumerate(algos):
                if algo == 'all':
                    continue
                data = db[algo][topo]
                points = list(zip(
                    [(i-minl)/dltl for i in data[flavour+'l']],  # top
                    [(i-minj)/dltj for i in data[flavour+'j']],  # right
                    [(i-minb)/dltb for i in data[flavour+'b']]  # left
                ))
                tax.scatter(
                    points,
                    marker=MARKERS[i],
                    color=COLORS[i],
                    label=longer_phrases[algo]
                )
            # tax.ticks(axis='lbr', linewidth=1, multiple=0.2)
            tax.top_corner_label("High latency")
            tax.right_corner_label("High jitter")
            tax.left_corner_label("High bandwidth")
            tax.bottom_axis_label("Low latency")
            tax.left_axis_label("Low jitter")
            tax.right_axis_label("Low bandwidth")
            tax.legend()
            tax.savefig(
                outfolder.joinpath(f"tern_{flavour}_{topo}.pdf")
            )
            plt.cla()
            plt.clf()
            plt.close()
            print(f"tern_{flavour}_{topo}.pdf")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage:", file=sys.stderr)
        print(f"  {sys.argv[0]} <__all__.autotests.json> <outfolder>",
              file=sys.stderr)
    else:
        all_tests = Path(sys.argv[1])
        outfolder = Path(sys.argv[2])
        outfolder.mkdir(parents=True, exist_ok=True)
        main(json.loads(all_tests.read_text()), outfolder)
