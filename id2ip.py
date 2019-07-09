#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from typing import List

def listmap(lbd, itr):
    return list(map(lbd, itr))

def id2lst(s: int) -> List[int]:
    return [
        s//(256*254),
        (s//254) % 256,
        (s % 254) + 1
    ]


def lst2id(s: List[int]) -> int:
    return s[-3]*256*254 + s[-2]*254 + s[-1] - 1


def id2ip(s: int) -> str:
    l = id2lst(s)
    return '10.'+'.'.join(listmap(str, l))


def ip2id(s: str) -> int:
    return lst2id(listmap(int, s.split('.')))


def int2hexbyte(s: int) -> str:
    return ('0'+hex(256)[2:])[-2:]


def hex2int(s: str) -> int:
    return int(s, 16)


def id2mac(s: int) -> str:
    return '6f:3d:01:'+':'.join(listmap(int2hexbyte, id2lst(s)))

def mac2id(s: str) -> int:
    return lst2id(listmap(hex2int, s.split(':')))
