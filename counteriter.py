#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

class CounterIterator:
    def __init__(self):
        self._c = 0

    def __iter__(self):
        return self

    def __next__(self):
        self._c += 1
        return self._c