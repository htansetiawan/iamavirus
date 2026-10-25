"""Validate target export on the real v35 search without training or a new bot.

Only one include and one post-selection callback are inserted into a temp copy.
All actor protocol input comes from its own observations and prior own actions.
The JSON export is an offline diagnostic, never sent through the arena protocol.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

from run_probe import HERE, ROOT, ARCHIVE, EXPECTED


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_target(row, protocol_move=None):
    assert row['own_reach_consistent'], 'inconsistent own reach inside an infoset'
    assert row['root_histories'] == len(row['samples'])
    assert math.isclose(sum(w['weight'] for w in row['samples']), 1, abs_tol=1e-9)
    assert math.isclose(row['cf_mass'], 1, abs_tol=1e-9)
    assert math.isclose(row['own_reach'], 1, abs_tol=1e-9)
    actions = row['actions']
    assert len({a['uci'] for a in actions}) == len(actions)
    assert all(math.isfinite(a[k]) for a in actions
               for k in ('probability', 'cf_q', 'q', 'advantage'))
    assert all(0 <= a['probability'] <= 1 for a in actions)
    assert math.isclose(sum(a['probability'] for a in actions), 1, abs_tol=1e-9)
    value = sum(a['probability'] * a['q'] for a in actions)
    assert math.isclose(value, row['root_value'], abs_tol=1e-9)
    assert math.isclose(value, row['solver_value'], abs_tol=1e-9)
    assert abs(sum(a['probability'] * a['advantage'] for a in actions)) < 1e-9
    for a in actions:
        assert math.isclose(a['q'] - value, a['advantage'], abs_tol=1e-9)
        assert row['root_loss_value']-1e-9 <= a['q'] <= 1+1e-9
    assert max(actions, key=lambda a: a['probability'])['uci'] == row['solver_move']
    # A mismatch is a real integration issue; do not hide it by changing the label.
    if protocol_move is not None:
        assert row['solver_move'] == protocol_move, (row['solver_move'], protocol_move)


def run_case(source, case, target, seconds, paired=False, strong_first=False, timeout=90):
    path, frame_index = case
    replay = json.loads(path.read_bytes())
    side = frame_index % 2
    color = ('white', 'black')[side]
    frames = replay['frames'][:frame_index+1]
    forced = [replay['frames'][i+1]['move'] for i in range(frame_index)
              if i % 2 == side]
    lines = ['fow', f'{"w" if side == 0 else "b"} 180 2']
    for i, frame in enumerate(frames):
        lines.append(frame[color])
        if i % 2 == side:
            lines.append(str(frame['clocks'][side]))
    protocol = '\n'.join(lines)+'\n'
    env = {k:v for k,v in os.environ.items()
           if not (k.startswith(('MIST_','ASTRA_TEACHER_')) or k == 'FOW_SEED')}
    env.update(MIST_STOCKFISH=str(source/'bin/stockfish'),
               MIST_HISTORY_TABLE=str(source/'data/history.bin'),
               MIST_FORCE_MOVES=','.join(forced), MIST_MAX_SECONDS=str(10 if paired else seconds),
               MIST_CAP='200000', MIST_SF_WORKERS='2', FOW_SEED='20261025',
               MIST_TEACHER_OUT=str(target))
    if paired:
        env.update(ASTRA_TEACHER_B=str(seconds),
                   ASTRA_TEACHER_STRONG_FIRST=str(int(strong_first)))
    target.unlink(missing_ok=True)
    started = time.monotonic()
    proc = subprocess.run([str(source/'mist')], input=protocol, cwd=source,
                          env=env, text=True, capture_output=True, timeout=timeout)
    elapsed = time.monotonic()-started
    if proc.returncode:
        raise RuntimeError(proc.stderr[-1500:])
    played = [line[5:] for line in proc.stdout.splitlines() if line.startswith('move ')]
    assert played[:-1] == forced, (path, frame_index, 'history diverged')
    assert len(played) == len(forced)+1
    rows = [json.loads(line) for line in target.read_text().splitlines()]
    assert len(rows)==(2 if paired else 1), ('unexpected export count',len(rows))
    rows.sort(key=lambda r:r['search_budget_seconds'])
    row = rows[0]
    check_target(row,played[-1])
    if paired:
        check_target(rows[1])
        assert rows[0]['samples']==rows[1]['samples'], 'belief samples changed between budgets'
        assert rows[0]['avoid_moves']==rows[1]['avoid_moves'], 'root restrictions changed'
        assert [v['uci'] for v in rows[0]['actions']]==[v['uci'] for v in rows[1]['actions']]
    assert 'mist: stockfish ready' in proc.stderr, 'requires real shipped frontier'
    result={'replay':str(path.relative_to(ROOT)), 'replay_sha256':digest(path),
            'frame':frame_index, 'side':color, 'forced_own_moves':forced,
            'requested_max_seconds':seconds,
            'actor_protocol_sha256':hashlib.sha256(protocol.encode()).hexdigest(),
            'actor_protocol':lines, 'truth_supplied_to_actor':False,
            'protocol_move':played[-1], 'wall_seconds':elapsed,
            'target':row, 'checks':'passed', 'stderr_tail':proc.stderr.splitlines()[-6:]}
    if paired:
        result['paired_target']=rows[1]
        result['strong_first']=strong_first
        result['paired_runtime']=[line for line in proc.stderr.splitlines()
                                  if line.startswith('astra: paired_search')]
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--seconds',type=float,nargs='+',default=[.4])
    parser.add_argument('--frames',type=int,nargs='+',default=[0,1,12,54])
    parser.add_argument('--paired',action='store_true',help='same frozen belief at B and 4B')
    parser.add_argument('--panel',type=Path,help='frozen teacher-readiness case manifest')
    parser.add_argument('--wall-cap',type=float,default=600,help='hard cap for case execution, excluding compilation')
    args=parser.parse_args()
    if any(s<=0 or not math.isfinite(s) for s in args.seconds):
        parser.error('seconds must be finite and positive')
    if not math.isfinite(args.wall_cap) or args.wall_cap<=0:
        parser.error('wall cap must be finite and positive')
    if digest(ARCHIVE)!=EXPECTED:
        raise SystemExit('Archive hash differs from audited v35')
    replay=ROOT/'astra-submissions/analysis/hidden-slider-zone-20261025/v35-guard0001-fullclock-extra-20pairs-seed20261042-pair8-candidate-white.json'
    cases=[(replay,f) for f in args.frames]
    panel={}
    if args.panel:
        panel=json.loads(args.panel.read_bytes())
        cases=[]
        for case in panel['cases']:
            path=ROOT/case['replay']
            if digest(path)!=case['replay_sha256']:
                raise RuntimeError('panel replay changed: '+str(path))
            cases.append((path,case['frame']))
    with tempfile.TemporaryDirectory(prefix='astra-teacher-engine-') as td:
        source=Path(td)
        with zipfile.ZipFile(ARCHIVE) as z:
            z.extractall(source)
        p=source/'src/gtcfr.c'
        text=p.read_text()
        anchor='    free(x); free(idx); free(share); free(chance_kids); free(chance_p);'
        if text.count(anchor)!=1:
            raise RuntimeError('post-selection hook anchor changed')
        text=text.replace('#include "cfr.h"', '#include "cfr.h"\n#include "teacher_dump.h"')
        text=text.replace(anchor,
            '    astra_teacher_dump(&t.g,x,root_I,&ours,out,b,idx,share,K,params);\n'+anchor)
        p.write_text(text)
        for filename in ('teacher_targets.h','teacher_targets.c','teacher_dump.h','teacher_dump.c'):
            shutil.copy2(HERE/filename,source/'src'/filename)
        extra=[]
        if args.paired:
            main=source/'src/main.c'
            original=main.read_text()
            call='gtcfr_decide(&b, &gp, &r)'
            if original.count(call)!=1:
                raise RuntimeError('decision hook anchor changed')
            original=original.replace('#include <stdio.h>', '#include "teacher_pair.h"\n#include <stdio.h>',1)
            main.write_text(original.replace(call,'astra_teacher_pair(&b, &gp, &r)'))
            for filename in ('teacher_pair.h','teacher_pair.c'):
                shutil.copy2(HERE/filename,source/'src'/filename)
            extra=[source/'src/teacher_pair.c']
        inputs=[source/'src'/name for name in
                ('board.c','belief.c','movemodel.c','cfr.c','eval.c','search.c',
                 'gtcfr.c','front.c','sfeval.c','main.c','teacher_targets.c','teacher_dump.c')]
        subprocess.run(['cc','-std=c11','-O2','-pthread','-D_POSIX_C_SOURCE=199309L',
                        *map(str,inputs+extra),'-lm','-o',str(source/'mist')],check=True)
        (source/'bin/stockfish').chmod(0o755)
        binary_hash=digest(source/'mist')
        instrument_hashes={name:digest(HERE/name) for name in
                           ('run_engine_probe.py','teacher_targets.c','teacher_targets.h',
                            'teacher_dump.c','teacher_dump.h','teacher_pair.c','teacher_pair.h')}
        modified_hashes={name:digest(source/'src'/name) for name in ('main.c','gtcfr.c')}
        rows=[]
        failures=[]
        started=time.monotonic()
        requested=[(case,seconds) for seconds in args.seconds for case in cases]
        attempted=0
        for index,(case,seconds) in enumerate(requested):
            remaining=args.wall_cap-(time.monotonic()-started)
            if remaining<=0:
                break
            attempted+=1
            try:
                row=run_case(source,case,source/'targets.jsonl',seconds,
                             args.paired,index%2==1,min(90,remaining))
                if args.panel:
                    row['slice']=panel['cases'][index%len(cases)]['slice']
                rows.append(row)
            except (AssertionError,RuntimeError,subprocess.TimeoutExpired,FileNotFoundError) as e:
                if not args.panel:
                    raise
                failures.append({'replay':str(case[0].relative_to(ROOT)),
                                 'frame':case[1],'seconds':seconds,'error':str(e)})
            print(f'cases {attempted}/{len(requested)} passed={len(rows)} failed={len(failures)}',
                  file=sys.stderr,flush=True)
    print(json.dumps({'archive_sha256':EXPECTED,'instrumented_binary_sha256':binary_hash,
                      'instrumentation_sha256':instrument_hashes,'modified_source_sha256':modified_hashes,
                      'classification':'bounded export/teacher sanity check; not training or a strength estimate',
                      'paired_same_belief':args.paired,'wall_cap_seconds':args.wall_cap,
                      'panel_sha256':digest(args.panel) if args.panel else None,
                      'requested_cases':len(requested),'attempted_cases':attempted,
                      'failures':failures,
                      'cases':rows},indent=2))


if __name__=='__main__':
    main()
