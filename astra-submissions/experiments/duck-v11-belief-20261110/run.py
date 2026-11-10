"""Reuse the audited v38 replay harness on Duck's earlier material decisions."""
from collections import Counter
from datetime import datetime, timezone
import argparse
import ctypes
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIOR = HERE.parent/'priority-diagnosis-20261109'
BUILD = HERE/'build'
ANALYSIS = ROOT/'astra-submissions/analysis'
OUT = ANALYSIS/HERE.name
TEACHER = ANALYSIS/'prospective-quiet-teacher-20261110'
SOURCE = ROOT/'data/astra-spool/duck-v11-matchup-20261110'
STORE = ROOT/'data/astra-spool'/HERE.name
VALIDATOR = HERE.parent/'last-only-pilot-20261110/build/native-validator.so'
OWNER = 'astra-'+HERE.name
sys.path.insert(0, str(ROOT))
from learning import _native, rules


def sha(path):
    with Path(path).open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def cpp_match(board, action, reply, expected_type):
    source = rules.square_index(reply[:2])
    target = rules.square_index(reply[2:4])
    attacker = expected_type + 6*(1-board.side)
    if board.piece_at(source) != attacker:
        return 0
    child = board.copy()
    child.push(action)
    if child.mover_lost() or child.piece_at(source) != attacker or reply not in child.legal_moves():
        return 1
    ep = expected_type == 0 and target == child.en_passant and source%8 != target%8
    victim = child.piece_at(target)
    if not ep and (victim < 0 or victim//6 != board.side):
        return 1
    child.push(reply)
    return 1 if child.mover_lost() else 3


def verify_c_predicate(cases):
    _native.ensure_built = lambda verbose=True: VALIDATOR
    library = ctypes.CDLL(str(BUILD/'capture-check.so'))
    library.fow_init()
    function = library.astra_capture_flags
    function.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_uint64, ctypes.c_int,
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    function.restype = ctypes.c_int
    checked = Counter()
    for case in cases:
        frames = json.loads(Path(case['replay_path']).read_text())['frames']
        board = rules.Board()
        for frame in frames[1:case['ply']+1]:
            board.push(frame['move'])
        assert board.board_string() == frames[case['ply']]['board']
        kind = 'pnbrqk'.index(case['attacking_piece'])
        for action in board.legal_moves():
            expected = cpp_match(board, action, case['duck_capture'], kind)
            actual = function(board.board_string().encode(), board.side, board.castling,
                board.en_passant, action.encode(), case['duck_capture'].encode(), kind)
            assert actual == expected, (case['id'], action, actual, expected)
            if action == case['recorded_move']:
                assert actual == 3
            checked[actual] += 1
    return dict(cases=len(cases), compared_actions=sum(checked.values()), counts=dict(checked))


def prepare():
    old = json.loads((ANALYSIS/PRIOR.name/'plan.json').read_text())
    match = ANALYSIS/'duck-v11-matchup-20261110'
    result = json.loads((match/'result.json').read_text())
    options = SOURCE/'prior-material-options.json'
    assert sha(options) == json.loads((match/'earlier-options.json').read_text())['analysis_rows_sha256']
    cases = []
    for row in json.loads(options.read_text()):
        game = row['game']
        path = SOURCE/'source/games'/game/'replay.json'
        assert sha(path) == result['source_replay_sha256'][game]
        ply = row['decision_ply']
        cases.append(dict(id=f'{game}-{ply}', game=game, side=('white','black')[ply%2],
            ply=ply, replay_path=str(path), replay_sha256=sha(path),
            recorded_move=row['captured_piece_move'], duck_capture=row['duck_capture'],
            attacking_piece=row['attacking_piece'], prevents_recorded_capture=row['prevents_recorded_capture']))
    assert len(cases) == 16
    assert not {(r['game'],r['ply']) for r in old['cases']} & {(r['game'],r['ply']) for r in cases}
    cases.sort(key=lambda case:hashlib.sha256(case['id'].encode()).hexdigest())
    BUILD.mkdir(exist_ok=False)
    OUT.mkdir(exist_ok=False)
    old_src = PRIOR/'build/src'
    source_files = [path for path in sorted(old_src.iterdir()) if path.is_file()]
    assets = [PRIOR/'build/bin/stockfish', PRIOR/'build/data/history.bin']
    for path in [*source_files,*assets]:
        assert sha(path) == old['dependencies'][str(path)], path
    for name in ('bin','data'):
        (BUILD/name).symlink_to(PRIOR/'build'/name, target_is_directory=True)
    text = (old_src/'main.c').read_text()
    marker = '        printf("move %s\\n", uci); fflush(stdout);'
    assert text.count(marker) == 1
    declaration = 'extern void astra_capture_readout(const Belief *, double);\n'
    anchor = 'int main('
    assert text.count(anchor) == 1
    text = text.replace(anchor, declaration+anchor)
    text = text.replace(marker, marker+'\n        astra_capture_readout(&b, guard_temp);')
    (BUILD/'main.c').write_text(text)
    common = ['gcc','-std=c11','-O2','-pthread','-D_POSIX_C_SOURCE=199309L','-I',str(old_src)]
    files = [str(path) for path in source_files if path.suffix == '.c' and path.name != 'main.c']
    for command in (
        [*common,*files,str(BUILD/'main.c'),str(HERE/'capture_readout.c'),'-lm','-o',str(BUILD/'mist-diagnostic')],
        [*common,'-shared','-fPIC',str(old_src/'board.c'),str(HERE/'capture_readout.c'),'-lm','-o',str(BUILD/'capture-check.so')]):
        subprocess.run(command, check=True, timeout=60)
    preflight = verify_c_predicate(cases)
    dependencies = [*source_files,*assets,Path(__file__),HERE/'capture_readout.c',BUILD/'main.c',
        BUILD/'mist-diagnostic',BUILD/'capture-check.so',PRIOR/'run.py',PRIOR/'prepare.py',
        ROOT/'astra-submissions/tools/fresh_taxonomy_gate.py',ROOT.parent/'fow-starter/referee.py',
        VALIDATOR,options,match/'result.json',TEACHER/'plan.json',
        *[Path(case['replay_path']) for case in cases]]
    plan = dict(at=now(), cases=cases, seed=3381110, cores=[2,3], per_call_seconds=120,
        batch_seconds=540, dependencies={str(path):sha(path) for path in dependencies},
        setup='Same v38 search, guards, scorer and replay clock prompts as 269. Readout after move emission.')
    write(OUT/'plan.json', plan)
    write(OUT/'preflight.json', preflight)
    print(json.dumps(preflight|dict(pins=len(plan['dependencies']),plan_sha256=sha(OUT/'plan.json'))), flush=True)


def legacy_runner():
    sys.path.insert(0,str(PRIOR))
    spec = importlib.util.spec_from_file_location('priority_replay', PRIOR/'run.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.BUILD = BUILD
    return module


def lease(take, cores):
    path = ROOT/'chatroom/cores.json'
    with Path('/tmp/iamavirus-cores-json.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        state = json.loads(path.read_text())
        if take:
            assert all(not set(cores)&set(r['cores']) for r in state['allocation'])
            state['allocation'].append(dict(owner=OWNER,cores=cores,at=now(),pid=os.getpid(),
                purpose='bounded Duck replay readout between teacher collection ticks'))
        else:
            state['allocation'] = [row for row in state['allocation'] if row['owner'] != OWNER]
        state['updated'] = now()
        temporary = path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(state,indent=2)+'\n')
        temporary.replace(path)


def observation_row(case, raw, result):
    assert result['fault'] is None
    assert all(sha(raw/name) == digest for name,digest in result['files'].items())
    text = (raw/'stderr.txt').read_text()
    assert 'mist: stockfish ready' in text and 'stockfish failed to start' not in text
    matches = [line.split('astra: exact-capture ',1)[1] for line in text.splitlines()
               if line.startswith('astra: exact-capture ')]
    assert len(matches) == 1
    mass = json.loads(matches[0])
    assert 0 <= mass['capture_worlds'] <= mass['piece_worlds'] <= mass['worlds']
    for weighting in ('fitted','sharpened'):
        assert 0 <= mass['capture_'+weighting] <= mass['piece_'+weighting] <= 1+1e-12
    root = re.search(r'astra: placement count=(\d+)', text)
    assert root and int(root[1]) == mass['worlds']
    actions = {match[1]: match[2]=='0' for match in re.finditer(r'astra: action (\S+) excluded=(\d+)',text)}
    prevents = set(case['prevents_recorded_capture'])
    sampled = None
    if result['tree_exported']:
        tree = json.loads((raw/'tree.jsonl').read_text())
        weights = [w['weight'] for w in tree['samples']]
        assert math.isclose(sum(weights),1,abs_tol=1e-8)
        attacker = case['attacking_piece'] if case['side']=='white' else case['attacking_piece'].upper()
        source = rules.square_index(case['duck_capture'][:2])
        sampled = sum(w['weight'] for w in tree['samples'] if w['hypothesis_board'][source]==attacker)
    return dict(case=case['id'], attacking_piece=case['attacking_piece'], **mass,
        sampled_piece_mass=sampled, visible_alternatives=len(prevents & actions.keys()),
        retained_alternatives=sum(actions.get(move,False) for move in prevents),
        selected_prevents_recorded_threat=result['move'] in prevents, selected_fatal=result['fatal'])


def run():
    plan = json.loads((OUT/'plan.json').read_text())
    for path,digest in plan['dependencies'].items():
        assert sha(path) == digest, path
    teacher = json.loads((TEACHER/'execution.json').read_text())
    if teacher['status'] == 'running':
        assert teacher['phase'] == 'collecting', 'Teacher is using its reserved cores'
        last = datetime.fromisoformat(teacher['updated_at'])
        elapsed = (datetime.now(timezone.utc)-last).total_seconds()
        pace = json.loads((TEACHER/'plan.json').read_text())['poll_seconds']
        assert 0 <= elapsed and elapsed+plan['batch_seconds']+120 < pace, 'Next teacher tick is too close'
    module = legacy_runner()
    STORE.mkdir(parents=True,exist_ok=False)
    os.sched_setaffinity(0,set(plan['cores']))
    lease(True,plan['cores'])
    started = time.monotonic()
    rows = []
    try:
        for case in plan['cases']:
            if time.monotonic()-started+plan['per_call_seconds'] > plan['batch_seconds']:
                raise TimeoutError('Remaining window cannot fit another replay')
            def launch(command, *args, **kwargs):
                kwargs['env'].update(ASTRA_RECORDED_MOVE=case['recorded_move'],
                    ASTRA_RECORDED_CAPTURE=case['duck_capture'],ASTRA_RECORDED_ATTACKER=case['attacking_piece'])
                return subprocess.Popen(command,*args,**kwargs)
            module.subprocess = SimpleNamespace(PIPE=subprocess.PIPE, Popen=launch,
                TimeoutExpired=subprocess.TimeoutExpired)
            raw = STORE/case['id']
            result = module.call(case,plan['seed'],raw)
            rows.append(observation_row(case,raw,result))
            print(json.dumps({'completed':len(rows),'seconds':round(time.monotonic()-started,2)}),flush=True)
        totals = dict(cases=len(rows), occupancy_absent=sum(r['piece_worlds']==0 for r in rows),
            exact_capture_absent=sum(r['capture_worlds']==0 for r in rows),
            low_capture_mass=sum(r['capture_sharpened']<.05 for r in rows),
            sampled_piece_absent=sum(r['sampled_piece_mass']==0 for r in rows),
            sampled_unavailable=sum(r['sampled_piece_mass'] is None for r in rows),
            no_alternative_in_view=sum(r['visible_alternatives']==0 for r in rows),
            alternatives_all_excluded=sum(r['visible_alternatives']>0 and r['retained_alternatives']==0 for r in rows),
            selected_prevents_recorded_threat=sum(r['selected_prevents_recorded_threat'] for r in rows),
            selected_fatal=sum(r['selected_fatal'] for r in rows))
        write(STORE/'case-readouts.json', rows)
        write(OUT/'result.json',dict(at=now(),counts=totals,seconds=time.monotonic()-started,
            plan_sha256=sha(OUT/'plan.json'),private_rows_sha256=sha(STORE/'case-readouts.json')))
        print(json.dumps(totals),flush=True)
    finally:
        lease(False,plan['cores'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=('prepare','run'))
    (prepare if parser.parse_args().action == 'prepare' else run)()
