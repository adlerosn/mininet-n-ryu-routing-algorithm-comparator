#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from typing import Tuple


def _sort_pair(a: str, b: str) -> Tuple[str, str]:
    if a[0] == 'h' and b[0] == 's':
        return b, a  # h5,s7 => s7,h5
    elif a[0] != b[0]:
        return a, b  # s7,h5 => s7,h5
    elif int(a[1:]) > int(b[1:]):
        return b, a  # s7,s5 => s5,s7
    else:
        return a, b  # s5,s7 => s5,s7
