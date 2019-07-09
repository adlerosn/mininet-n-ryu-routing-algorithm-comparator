#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys
import json
from pathlib import Path
from toporender import main as renderer


def main(fn: str):
    mn = json.loads(Path(f'{fn}.mn').read_text())
    hosts = [i['opts']['hostname'] for i in mn['hosts']]
    switches = [i['opts']['hostname'] for i in mn['switches']]
    links = [
        (
            i['src'],
            i['dest'],
            i.get('opts', dict()).get('bw')
        )
        for i in mn['links']
    ]
    Path(f'{fn}.json').write_text(json.dumps([hosts, switches, links]))
    renderer(fn)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fn = ' '.join(sys.argv[1:])
        main(fn)
    else:
        print("Usage:", file=sys.stderr)
        print(f"  {sys.argv[0]} <toponame>", file=sys.stderr)
        print(f"  <toponame>.mn --> <toponame>.json --> <toponame>.py", file=sys.stderr)
