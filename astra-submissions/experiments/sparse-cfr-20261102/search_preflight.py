"""Whole-engine integration: fixed-work parity, then shared-belief SF smoke."""
import json
import os
from pathlib import Path
import subprocess
import sys
from search_common import HERE, ROOT, OUT, now, sha, unique

sys.path[:0] = [str(ROOT), str(ROOT/'astra-submissions/tools')]
from fresh_taxonomy_gate import protocol


def main():
    OUT.mkdir(exist_ok=True)
    os.sched_setaffinity(0, {0, 1})
    cases = json.loads((ROOT/'astra-submissions/analysis/fresh-taxonomy-20261101/cases.json').read_text())
    replay = json.loads(Path(cases['cases'][0]['replay_path']).read_text())
    rows = []
    for sf in (False, True):
        for side in (0, 1):
            stem = f'preflight-sf{int(sf)}-side{side}'
            target = OUT/(stem+'.targets.jsonl')
            assert not target.exists()
            feed, forced = protocol(replay, side, side)
            assert not forced
            env = {k:v for k,v in os.environ.items() if not k.startswith(('MIST_', 'ASTRA_', 'FOW_'))}
            env.update(ASTRA_SOLVER_PAIR=str(side), ASTRA_PAIR_SECONDS='0.1' if sf else '0',
                       MIST_TEACHER_OUT=str(target), FOW_SEED='2541102')
            if sf:
                env['MIST_STOCKFISH'] = str(HERE/'build/diagnostic/bin/stockfish')
                env['MIST_HISTORY_TABLE'] = str(HERE/'build/diagnostic/data/history.bin')
            r = subprocess.run([str(HERE/'build/diagnostic/mist')], input=feed,
                               capture_output=True, text=True, env=env, timeout=30)
            (OUT/(stem+'.stdout')).write_text(r.stdout)
            (OUT/(stem+'.stderr')).write_text(r.stderr)
            assert r.returncode == 0, r.stderr
            records = [json.loads(s) for s in target.read_text().splitlines()]
            assert len(records) == 2
            assert records[0]['samples'] == records[1]['samples']
            assert records[0]['avoid_moves'] == records[1]['avoid_moves']
            assert [a['uci'] for a in records[0]['actions']] == [a['uci'] for a in records[1]['actions']]
            if not sf: assert records[0] == records[1], 'fixed-work whole-search mismatch'
            else: assert 'mist: stockfish ready' in r.stderr
            rows.append(dict(side=side,stockfish=sf,exit_code=r.returncode,
                             fixed_work_identical=records[0] == records[1],
                             samples_identical=True,target_sha256=sha(target)))
    unique(OUT/'preflight.json',dict(at=now(),passed=True,rows=rows,binary_sha256=sha(HERE/'build/diagnostic/mist')))
    print(json.dumps(dict(passed=True,cases=len(rows))))


if __name__ == '__main__': main()
