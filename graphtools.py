#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

EMPTY_ITER = iter(list())


def _get_transition_map(graph):
    transitions = [(source, target) for source, lnks in graph.items()
                   for target in lnks.keys()]
    transmap = dict()
    for s, t in transitions:
        if t not in transmap:
            transmap[t] = list()
        transmap[t].append(s)
    return {k: tuple(v) for k, v in transmap.items()}


def _find_all_paths(tm, initial, target, accumulator=None):
    if accumulator is None:
        accumulator = list()
    accumulator = [*accumulator, initial]
    if initial == target:
        yield tuple(accumulator)
    else:
        for intermediate in tm[initial]:
            if intermediate not in accumulator:
                yield from _find_all_paths(tm, intermediate, target, accumulator)
        yield from EMPTY_ITER


def find_all_paths(graph, initial, target, accumulator=None):
    if initial == target:
        yield tuple([])
    else:
        tm = _get_transition_map(graph)
        yield from _find_all_paths(tm, initial, target)


def dijkstra(graph, initial):
    visited = {initial: 0}
    path = dict()

    nodes = set(graph.keys())
    mentions = {node: list(graph[node].keys()) for node in nodes}

    while len(nodes) > 0:
        min_node = None
        for node in nodes:
            if node in visited:
                if min_node is None:
                    min_node = node
                elif visited[node] < visited[min_node]:
                    min_node = node

        if min_node is None:
            break

        nodes.remove(min_node)
        current_weight = visited[min_node]

        for edge in mentions[min_node]:
            weight = current_weight + 1
            if edge not in visited or weight < visited[edge]:
                visited[edge] = weight
                path[edge] = min_node
    return visited, path


def dijkstra_min_path(dijkstra_tuple, initial, target):
    visited, path = dijkstra_tuple
    min_path = list()
    current = target
    if current in path or current == initial:
        while current is not None:
            min_path.append(current)
            current = path.get(current)
        return (list(reversed(min_path)), visited[target])
    return ([], None)


class Dijkstra:
    def __init__(self, graph):
        self._graph = graph
        self._cache = dict()

    def __call__(self, initial):
        if initial not in self._cache:
            self._cache[initial] = dijkstra(self._graph, initial)
        return DijkstraResults(initial, self._cache[initial])


class DijkstraResults:
    def __init__(self, initial, dijkstra_tuple):
        self._i = initial
        self._dt = dijkstra_tuple

    def __call__(self, target):
        return dijkstra_min_path(self._dt, self._i, target)


def graph_from_topo(network_topo):
    network_graph = dict()
    for h in network_topo[0]:
        network_graph[h] = dict()
    for s in network_topo[1]:
        network_graph[s] = dict()
    for l in network_topo[2]:
        network_graph[l[0]][l[1]] = l[2]
        network_graph[l[1]][l[0]] = l[2]
    return network_graph
