"""After-search full-population census; truth joins only in a separate audit."""
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis/root-population-20261110'
BUILD = HERE/'build'
CONTROL = HERE.parent/'guard-controls-20261109'
PRIOR = ROOT/'astra-submissions/analysis/guard-loss-review-20261110'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')


def helper():
    sys.path.insert(0, str(CONTROL))
    spec = importlib.util.spec_from_file_location('population_pair_helper', CONTROL/'run.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    result.BUILD = BUILD
    result.OUT = OUT
    class CaptureSubprocess:
        PIPE = subprocess.PIPE
        TimeoutExpired = subprocess.TimeoutExpired
        @staticmethod
        def Popen(cmd, *args, **kwargs):
            assert cmd == [str(BUILD/'mist')]
            kwargs['env']['ASTRA_POPULATION_OUT'] = str(Path(kwargs['env']['MIST_TEACHER_OUT']).parent/'population.json')
            return subprocess.Popen(cmd, *args, **kwargs)
    result.subprocess = CaptureSubprocess
    return result


def prepare():
    OUT.mkdir(exist_ok=False)
    BUILD.mkdir(exist_ok=False)
    shutil.copytree(CONTROL/'build/src', BUILD/'src')
    for name in ['bin', 'data']:
        (BUILD/name).symlink_to(CONTROL/'build'/name, target_is_directory=True)
    flags = ['-O2', '-std=c11', '-pthread', '-D_POSIX_C_SOURCE=199309L', '-I', str(BUILD/'src')]
    commands = []
    sources = [p for p in sorted((BUILD/'src').glob('*.c'))]
    objects = []
    for source in sources+[CONTROL/'pair.c', HERE/'snapshot.c']:
        obj = BUILD/(source.stem+'.o')
        cmd = ['gcc', *flags, *(['-Dastra_guard_pair=astra_guard_pair_original'] if source.name == 'pair.c' else []),
               '-c', str(source), '-o', str(obj)]
        subprocess.run(cmd, capture_output=True, check=True, timeout=60)
        commands.append(cmd); objects.append(obj)
    cmd = ['gcc', '-pthread', *map(str, objects), '-lm', '-o', str(BUILD/'mist')]
    subprocess.run(cmd, capture_output=True, check=True, timeout=60); commands.append(cmd)
    previous = json.loads((PRIOR/'plan.json').read_text())
    case = next(c for c in previous['cases'] if c['id'] == 'p0-black-candidate-81')
    module = helper()
    probe = dict(case, id='opening-preflight', ply=1)
    row = module.one(probe, 0, OUT/'preflight', .1)
    snap = json.loads((OUT/'preflight/population.json').read_text())
    assert snap['count'] == 20 and snap['us'] == 1
    assert len(snap['samples']) == len(row['arms']['base']['target']['samples'])
    for sample, exported in zip(snap['samples'], row['arms']['base']['target']['samples']):
        assert sample['index'] == exported['belief_index'] and sample['weight'] == exported['weight']
        assert snap['worlds'][sample['index']]['board'] == exported['hypothesis_board']
    deps = dict(previous['dependencies'])
    paths = [Path(__file__), HERE/'snapshot.c', BUILD/'mist', CONTROL/'pair.c']
    paths += list((BUILD/'src').glob('*'))
    deps.update({str(p): sha(p) for p in paths})
    plan = dict(at=datetime.now(timezone.utc).isoformat(), case=case, dependencies=deps,
                core=6, per_arm_seconds=2.5, process_seconds=150, actor_seed=2701109,
                design='Original paired function linked under another name, unchanged. Wrapper invokes it first, '
                       'then exports all worlds, weights, state metadata and action risk masks. No true board input. '
                       'One selected root, at most 64 root moves, no model or policy change.',
                limitations='New one-core reconstruction may thin differently from the live game and earlier replay. '
                            'Full/capped population support and calibration are distinct. This is not a strength test.')
    write(OUT/'preflight.json', dict(passed=True, commands=commands, count=snap['count'],
                                   samples_reproduce=True, result_sha256=sha(OUT/'preflight/result.json')))
    write(OUT/'plan.json', plan)
    print(json.dumps(dict(prepared=True, pins=len(deps), preflight_population=snap['count'])), flush=True)


def run():
    plan = json.loads((OUT/'plan.json').read_text())
    for path, value in plan['dependencies'].items():
        assert sha(path) == value, path
    os.sched_setaffinity(0, {6})
    os.nice(10)
    write(OUT/'started.json', dict(at=datetime.now(timezone.utc).isoformat(), pid=os.getpid()))
    result = helper().one(plan['case'], 1, OUT/'case', plan['per_arm_seconds'])
    population = json.loads((OUT/'case/population.json').read_text())
    write(OUT/'completion.json', dict(at=datetime.now(timezone.utc).isoformat(), passed=True,
          population=population['count'], result_sha256=sha(OUT/'case/result.json'),
          population_sha256=sha(OUT/'case/population.json'), paired=result['exercised'], scope=plan['limitations']))
    print(json.dumps(dict(completed=True, population=population['count'], paired=result['exercised'])), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'run'))
    globals()[parser.parse_args().action]()
