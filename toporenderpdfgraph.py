#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys
import json
from pathlib import Path
from topoviewer import nx_graph_from_topo
from networkx.drawing.layout import spring_layout
from networkx.drawing.nx_pylab import draw_networkx
from networkx.drawing.nx_pylab import draw_networkx_labels
from networkx.drawing.nx_pylab import draw_networkx_nodes
from networkx.drawing.nx_pylab import draw_networkx_edges
from networkx.drawing.nx_pylab import draw_networkx_edge_labels
from matplotlib import pyplot as plt
from matplotlib.figure import Figure


def main(fn: str):
    infile = Path(f'{fn}')
    outfile = infile.parent.joinpath(infile.stem+'.pdf')
    outfilebw = infile.parent.joinpath(infile.stem+'.pdf.bw.txt')
    topo = json.loads(infile.read_text())
    nxg = nx_graph_from_topo(topo)
    pos = spring_layout(nxg, iterations=4000)
    fig = Figure()
    fig.set_dpi(300)
    ax = fig.add_subplot(111)
    ax.axis('off')
    labels = dict()
    for edge in nxg.edges:
        bw = nxg.get_edge_data(edge[0], edge[1], dict()).get('bw', None)
        bw = '' if bw is None else '%.1f mbps' % (bw,)
        labels[edge] = bw
    if len(set(labels.values()))>1:
        draw_networkx_edge_labels(
            nxg, pos, ax=ax,
            edge_labels=labels,
            bbox=dict(
                facecolor='#FFFFFF88',
                edgecolor='none'
            ),
            font_size='x-small'
        )
    else:
        sbw = next(iter(set(labels.values())))
        outfilebw.write_text(sbw)
    draw_networkx_edges(
        nxg, pos, ax=ax,
        edgelist=nxg.edges, edge_color='black'
    )
    draw_networkx_nodes(
        nxg, pos, ax=ax,
        nodelist=topo[0], node_color='lightgreen', edgecolors="green"
    )
    draw_networkx_nodes(
        nxg, pos, ax=ax,
        nodelist=topo[1], node_color='cyan', edgecolors="darkcyan"
    )
    draw_networkx_labels(nxg, pos, ax=ax, font_size='small')
    fig.savefig(str(outfile))


if __name__ == "__main__":
    if len(sys.argv) == 2 and Path(sys.argv[1]).exists():
        fn = ' '.join(sys.argv[1:])
        main(fn)
    else:
        print("Usage:", file=sys.stderr)
        print(f"  {sys.argv[0]} <toponame.json>", file=sys.stderr)
        print(f"  <toponame.json> --> <toponame>.pdf", file=sys.stderr)
