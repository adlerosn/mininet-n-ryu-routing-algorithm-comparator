#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys
import time
import json
import tkinter
import networkx
import traceback
import threading
from pathlib import Path
from graphtools import Dijkstra, graph_from_topo
from sortundirectednodepair import _sort_pair
from networkx.drawing.layout import spring_layout
from networkx.drawing.nx_pylab import draw_networkx
from networkx.drawing.nx_pylab import draw_networkx_labels
from networkx.drawing.nx_pylab import draw_networkx_nodes
from networkx.drawing.nx_pylab import draw_networkx_edges
from networkx.drawing.nx_pylab import draw_networkx_edge_labels
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

matplotlib.use("TkAgg")


def nx_graph_from_topo(topo):
    g = networkx.Graph()
    g.add_nodes_from(topo[0])
    g.add_nodes_from(topo[1])
    g.add_edges_from([(x, y) for x, y, z in topo[2]])
    for h1, h2, bw in topo[2]:
        g[h1][h2]['bw'] = bw
    return g


def parse_state(s):
    pathb, loadb = [], []
    current = 0
    for line in s.splitlines():
        if line.startswith('@'):
            if line.startswith('@start.'):
                if line.endswith('path'):
                    current = 1
                elif line.endswith('load'):
                    current = 2
                else:
                    raise ValueError(f"Start of unexpected block: {line}")
            elif line.startswith('@end'):
                current = 0
            else:
                raise ValueError(f"Unexpected command: {line}")
        elif current == 1:
            pathb.append(eval(line))
        elif current == 2:
            loadb.append(eval(line))
    loads, path_segments = dict(), dict()
    for multiplepath in pathb:
        ws = sum([weight for weight in multiplepath.values()])
        for path, weight in multiplepath.items():
            for i in range(len(path)-1):
                path_segments[_sort_pair(*path[i:i+2])] = weight/ws
    for load in loadb:
        loads[_sort_pair(load[0], load[1])] = load[2]
    return pathb, path_segments, loads


def get_loaded_switches():
    pt = Path("~current.sws.state")
    if not pt.exists():
        return set()
    else:
        return set(filter(len, pt.read_text().splitlines()))


CLR = {True: 'FF', False: '00'}

topos = dict()
topoPos = dict()
topoDjkt = dict()
nxgs = dict()


def plot(ax, currentfile):
    ax.clear()
    ax.axis('off')
    if not currentfile.exists():
        return
    toponame = currentfile.read_text().strip()
    statepath = Path(f'{toponame}.state')
    if toponame not in topos:
        topos[toponame] = json.loads(Path(f'{toponame}.json').read_text())
    topo = topos[toponame]
    if toponame not in nxgs:
        nxgs[toponame] = nx_graph_from_topo(topo)
    nxg = nxgs[toponame]
    if toponame not in topoPos:
        topoPos[toponame] = spring_layout(nxg, iterations=2000)
    pos = topoPos[toponame]
    if toponame not in topoDjkt:
        djkt = Dijkstra(graph_from_topo(topo))
        djkt_pairs = list()
        for h1 in topo[0]:
            for h2 in topo[0]:
                if h1 != h2:
                    h1, h2 = _sort_pair(h1, h2)
                    djkt_seq = djkt(h1)(h2)[0]
                    for i in range(len(djkt_seq)-1):
                        djkt_pairs.append(_sort_pair(*djkt_seq[i:i+2]))
        topoDjkt[toponame] = djkt_pairs
    djkt = topoDjkt[toponame]
    state_txt = ""
    if statepath.exists():
        state_txt = statepath.read_text()
    paths, path_segments, loads = parse_state(state_txt)
    labels = dict()
    for unsortededge in nxg.edges:
        edge = _sort_pair(*list(map(str, unsortededge)))
        labels[unsortededge] = "%0.4f" % (loads.get(edge, 0.0),)
        # labels[unsortededge] = repr(loads.get(edge, 0.0),)
    edlab = draw_networkx_edge_labels(
        nxg, pos, ax=ax,
        edge_labels=labels,
        bbox=dict(
            facecolor='none',
            edgecolor='none'
        )
    )
    loaded_sws = set(topo[1]).intersection(get_loaded_switches())
    unloaded_sws = set(topo[1]).difference(loaded_sws)
    for unsortededge in nxg.edges:
        edge = _sort_pair(*list(map(str, unsortededge)))
        in_djkt = edge in djkt
        in_sgmt = min(
            1.0,
            max(
                0.0,
                path_segments.get(
                    edge,
                    path_segments.get(
                        tuple(reversed(edge)),
                        0.0
                    ))))
        in_sgmt = ('0'+(hex(round(in_sgmt*255))[2:]))[-2:].upper()
        in_unld = (edge[0] in unloaded_sws) or (edge[1] in unloaded_sws)
        color = '#'+CLR[in_djkt]+CLR[in_unld]+in_sgmt
        draw_networkx_edges(
            nxg, pos, ax=ax,
            edgelist=[edge], edge_color=color
        )
    draw_networkx_nodes(
        nxg, pos, ax=ax,
        nodelist=topo[0], node_color='lightgreen'
    )
    draw_networkx_nodes(
        nxg, pos, ax=ax,
        nodelist=unloaded_sws, node_color='pink'
    )
    draw_networkx_nodes(
        nxg, pos, ax=ax,
        nodelist=loaded_sws, node_color='cyan'
    )
    draw_networkx_labels(nxg, pos, ax=ax)


continuePlotting = True


def to_closing_state():
    global continuePlotting
    continuePlotting = False


def show_window(currentfile):
    root = tkinter.Tk()
    root.title("Network graph viewer")
    root.geometry("1000x600")

    lab = tkinter.Label(root, text="Plotting network")
    lab.pack()

    fig = Figure()

    ax = fig.add_subplot(111)
    ax.axis('off')
    fig.patch.set_facecolor("#D9D9D9")

    graph = FigureCanvasTkAgg(fig, master=root)
    graph.get_tk_widget().pack(side="top", fill='both', expand=True)

    b = tkinter.Button(root, text="Update GUI", command=graph.draw)
    b.pack()

    def plotter():
        while continuePlotting:
            try:
                plot(ax, currentfile)
                b.invoke()
            except BaseException:
                traceback.print_exc(file=sys.stderr)
            time.sleep(0.1)

    def close_cmd():
        to_closing_state()
        root.destroy()

    thread = threading.Thread(target=plotter)
    root.protocol("WM_DELETE_WINDOW", close_cmd)
    thread.start()

    root.mainloop()


def main(currentfile):
    show_window(currentfile)


if __name__ == "__main__":
    currentfile = Path(f'~current.state')
    main(currentfile)
