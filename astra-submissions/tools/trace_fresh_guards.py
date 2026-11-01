#!/usr/bin/env python3
"""Print already-computed root guard probabilities in isolated diagnostic builds.

Only adds stderr output; does not change weights or decision rules. Logging can
affect wall-clock search, so these are diagnostics, not part of the policy gate.
"""
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning import compare_archives as ca, ingest
from fresh_taxonomy_gate import protocol


def main():
    out = Path(sys.argv[1]).resolve()
    plan = json.loads((out/'diagnostic-plan.json').read_text())
    original = {35: out/'builds/iamavirus-v35-mist-c-v14', 37: out/'builds/iamavirus-v37-mist-c-v14-allfit'}
    binaries = {}; provenance = {}; traces = []
    for v, source in original.items():
        target = out/'guard-audit-builds'/f'v{v}'
        target.mkdir(parents=True, exist_ok=False)
        shutil.copytree(source/'src', target/'src')
        shutil.copyfile(source/'build.sh', target/'build.sh')
        path = target/'src/main.c'; before = path.read_text()
        needle = '                qdropped += qout[i];'
        assert before.count(needle) == 1
        after = before.replace(needle, needle + '''
                if (getenv("MIST_GUARD_AUDIT")) {
                    char audit_uci[6]; move_to_uci(allowed.moves[i], audit_uci);
                    fprintf(stderr, "astra_guard %s king=%.9f/%.9f queen=%.9f/%.9f veto=%d\\n",
                            audit_uci, krisk[i], kriskt[i], qrisk[i], qriskt[i], out[i]);
                }''')
        path.write_text(after)
        patch = ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), 'a/src/main.c', 'b/src/main.c'))
        (out/f'guard-audit-v{v}.patch').write_text(patch)
        subprocess.run(['bash', 'build.sh'], cwd=target, check=True, capture_output=True)
        binaries[v] = target/'mist'
        provenance[str(v)] = {'base_main_sha256': hashlib.sha256(before.encode()).hexdigest(),
                              'instrumented_main_sha256': hashlib.sha256(after.encode()).hexdigest(),
                              'binary_sha256': hashlib.sha256(binaries[v].read_bytes()).hexdigest()}
    for case in plan['cases']:
        payload = Path(case['replay_path']).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == case['replay_sha256']
        replay = json.loads(payload); states, problems = ingest.validate_replay(replay); assert not problems
        side = ('white','black').index(case['side']); feed, forced = protocol(replay, case['ply'], side)
        state = states[case['ply']]
        for v, binary in binaries.items():
            env = {k:x for k,x in os.environ.items() if not k.startswith(('MIST_', 'FOW_'))}
            env.update(MIST_GUARD_AUDIT='1', MIST_FORCE_MOVES=','.join(forced), FOW_SEED='11012026', MIST_MAX_SECONDS='2.5',
                       MIST_STOCKFISH=str(original[v]/'bin/stockfish'), MIST_HISTORY_TABLE=str(original[v]/'data/history.bin'))
            proc = subprocess.Popen(['taskset','-c','0,1',str(binary)], stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
            try:
                stdout, stderr = proc.communicate(feed, timeout=180)
            except subprocess.TimeoutExpired:
                ca.kill_tree(proc.pid); proc.wait(); raise
            moves = [l[5:].strip() for l in stdout.splitlines() if l.startswith('move ')]
            assert proc.returncode == 0 and len(moves) == len(forced)+1 and moves[:-1] == forced
            risks = []
            for line in stderr.splitlines():
                if not line.startswith('astra_guard '): continue
                _, move, king, queen, veto = line.split()
                risks.append({'move': move, 'king': [float(x) for x in king[5:].split('/')],
                              'queen': [float(x) for x in queen[6:].split('/')], 'veto': bool(int(veto[5:])),
                              'true_fatal': state.board.move_loses_king(move) if move in state.board.legal_moves() else None})
            log = out/'logs'/f"guard-{case['game']}-{case['ply']}-v{v}.stderr"; log.write_text(stderr)
            traces.append({'game': case['game'], 'ply': case['ply'], 'version': v, 'risks': risks, 'diagnostic_move': moves[-1]})
    (out/'guard-traces.json').write_text(json.dumps({'provenance': provenance, 'traces': traces}, indent=2)+'\n')


if __name__ == '__main__':
    main()
