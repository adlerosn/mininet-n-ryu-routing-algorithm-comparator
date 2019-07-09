#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys
import json
import importlib
import subprocess
import configparser
from time import sleep
from pathlib import Path
from topoautotest import main as run_single_test

ALGOS = [
    'ospf',
    'ecmp',
    'ldr',
    'minmax-single',
    'ldr-single',
]

PROBLEMATIC_SKIPS = [
]

CONTROLLER_VARIABLES = Path('variables.ini')


def run_many_tests(topo, module, results, test_count, returns_result=False):
    sucessfulTests = list()
    cachedir = Path("resultcache")
    cachedir.mkdir(parents=True, exist_ok=True)
    cfg = configparser.ConfigParser()
    cfg.read_string(CONTROLLER_VARIABLES.read_text())
    algo = cfg['GENERAL']['algo']
    apacache = Path(f'{module.__name__}.apa.json')
    if apacache.exists():
        apacache.unlink()
    is_problematic = (algo, module.__name__) in PROBLEMATIC_SKIPS
    while len(sucessfulTests) < test_count:
        cachefile = cachedir.joinpath(
            f"{module.__name__}.{algo}.{len(sucessfulTests)}.json")
        if cachefile.exists():
            result = json.loads(cachefile.read_text())
            sucessfulTests.append(result)
            continue
        result = None
        if not is_problematic:
            subprocess.run(
                ['mn', '-c'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            ).check_returncode()
            print(
                f'*** Running test {len(sucessfulTests)+1} of {test_count} on {module.__name__} with {algo}', file=sys.stderr)
            ryuController = subprocess.Popen(
                [
                    'ryu-manager',
                    'latencycontroller.py',
                    f'{module.__name__}.json'
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            sleep(0.5)
            try:
                subprocess.run(
                    ["python3", "topoautotest.py", f"{module.__name__}"]
                ).check_returncode()
            except subprocess.CalledProcessError:
                pass
            finally:
                resultspath = Path(f'{module.__name__}.autotest.json')
                statepath = Path(f'{module.__name__}.state')
                curswsstatepath = Path(f'~current.sws.state')
                if resultspath.exists():
                    result = json.loads(resultspath.read_text())
                    resultspath.unlink()
                ryuController.kill()
                if statepath.exists():
                    statepath.unlink()
                if curswsstatepath.exists():
                    curswsstatepath.unlink()
        else:
            result = dict()
        if result is not None:
            cachefile.write_text(json.dumps(result))
            sucessfulTests.append(result)
    if returns_result:
        return sucessfulTests
    else:
        results.write_text(json.dumps(
            sucessfulTests,
            indent=4
        ))


def run_many_tests_bulk(out_path, call_args, returns_result=False):
    tests = dict()
    for i, call_arg in enumerate(call_args):
        print(
            f'** Testing topology {i+1} of {len(call_args)}: {call_arg[1].__name__}', file=sys.stderr)
        tests[call_arg[1].__name__] = run_many_tests(*call_arg, True)
    if returns_result:
        return tests
    else:
        out_path.write_text(json.dumps(
            tests,
            indent=4
        ))


def run_many_tests_bulk_all_algos(out_path, call_args, returns_result=False):
    original_config = CONTROLLER_VARIABLES.read_bytes()
    try:
        tests = dict()
        cfg = configparser.ConfigParser()
        cfg.read_string(CONTROLLER_VARIABLES.read_text())
        for i, algo in enumerate(ALGOS):
            cfg['GENERAL']['algo'] = algo
            with CONTROLLER_VARIABLES.open('w') as f:
                cfg.write(f)
            print(
                f'* Testing algorithm {i+1} of {len(ALGOS)}: {algo}', file=sys.stderr)
            tests[algo] = run_many_tests_bulk(out_path, call_args, True)
        if returns_result:
            return tests
        else:
            out_path.write_text(json.dumps(
                tests,
                indent=4
            ))
    finally:
        CONTROLLER_VARIABLES.write_bytes(original_config)


def main(out_path, call_args, returns_result=False):
    return run_many_tests_bulk_all_algos(out_path, call_args, returns_result)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Usage:')
        print(
            f'  {sys.argv[0]} <how_many_tests> <toponame1> [<toponame2> [... [<toponameN>]]]')
        print()
        print('   Where toponame is will be resolved to')
        print('   toponame.json')
    else:
        prog, tests, *modnames = sys.argv
        tests = int(tests)
        call_args = list()
        for modname in modnames:
            modfile = Path(f'{modname}.py')
            topopath = Path(f'{modname}.json')
            resultspath = Path(f'{modname}.autotests.json')
            if not topopath.exists():
                print(f'Topology {topopath}.json does not exist.')
            if not modfile.exists():
                print(f'Topology {topopath}.py does not exist.')
                print(f'You might want to use toporender.py to generate required files.')
            else:
                topo = json.loads(topopath.read_text())
                mod = importlib.import_module(modname)
                call_args.append((topo, mod, resultspath, tests))
        main(Path('__all__.autotests.json'), call_args)
