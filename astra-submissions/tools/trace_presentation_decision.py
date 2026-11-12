"""One fixed-history v38 teaching trace, with output-only source annotations.

This is neither a candidate nor a reproduction of an arena search. The two
first attempts have different logging costs and are not a speed comparison.
"""
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
NAME = 'presentation-real-decision-20261111'
OUT = ROOT / 'astra-submissions/analysis' / NAME
BUILD = ROOT / 'astra-submissions/experiments' / NAME
PRIVATE = ROOT / 'data/astra-spool' / NAME
ZIP = ROOT / 'astra-submissions/iamavirus-v38-mist-c-allchildren.zip'
SHIP = ROOT / 'astra-submissions/experiments/guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'
REPLAY = ROOT / 'data/astra-spool/v38-mist-wins-20261111/c8ozqj0m.json'
REFEREE = Path('/home/henrytan/git/fow-starter/referee.py')
MODULES = ('board', 'belief', 'movemodel', 'cfr', 'eval', 'search', 'gtcfr', 'front', 'sfeval', 'main')


def now(): return datetime.now(timezone.utc).isoformat()
def read(path): return json.loads(Path(path).read_text())
def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def save(path, value):
    with path.open('x') as stream: stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')
def update(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n'); temp.replace(path)


def replace(source, before, after):
    assert source.count(before) == 1, before
    return source.replace(before, after)


MAIN_HOOK = r'''
        /* Astra: output-only teaching snapshot, after guards and before search. */
        if (!(forced && *forced)) {
            double astra_total = 0;
            for (size_t astra_i = 0; astra_i < b.count; ++astra_i)
                astra_total += b.logw ? exp((double)b.logw[astra_i]) : 1.0;
            fprintf(stderr, "@astra {\"kind\":\"belief\",\"count\":%zu,\"cap\":%zu,\"overflowed\":%d,\"budget\":%.17g,\"decision\":%d,\"temperature\":%.17g}\n",
                    b.count, b.cap, b.overflowed, gp.seconds, decisions + 1, belief_temperature());
            for (size_t astra_i = 0; astra_i < b.count && astra_i < 4096; ++astra_i) {
                char astra_board[65], astra_view[65];
                pos_to_board_string(&b.items[astra_i], astra_board);
                observation(&b.items[astra_i], us, astra_view);
                fprintf(stderr, "@astra {\"kind\":\"world\",\"index\":%zu,\"board\":\"%s\",\"view\":\"%s\",\"side\":%d,\"ep\":%d,\"castle\":%llu,\"halfmove\":%d,\"history\":\"%016llx\",\"logw\":%.17g,\"weight\":%.17g}\n",
                        astra_i, astra_board, astra_view, b.items[astra_i].side, b.items[astra_i].ep,
                        (unsigned long long)b.items[astra_i].castle_rooks, b.items[astra_i].halfmove,
                        (unsigned long long)b.hist[astra_i], b.logw ? (double)b.logw[astra_i] : 0.0,
                        (b.logw ? exp((double)b.logw[astra_i]) : 1.0) / astra_total);
            }
        }
'''
GUARD_HOOK = r'''
                char astra_uci[6]; move_to_uci(allowed.moves[i], astra_uci);
                fprintf(stderr, "@astra {\"kind\":\"guard\",\"move\":\"%s\",\"king\":%.17g,\"king_sharp\":%.17g,\"queen\":%.17g,\"queen_sharp\":%.17g,\"combined\":%.17g,\"combined_sharp\":%.17g,\"excluded\":%d}\n",
                        astra_uci, krisk[i], kriskt[i], qrisk[i], qriskt[i], risk[i], riskt[i], out[i]);
'''
CHILD_HOOK = r'''
    if (only) {
        char astra_board[65]; pos_to_board_string(p, astra_board);
        for (int astra_a = 0; astra_a < l.count; ++astra_a) {
            char astra_uci[6]; move_to_uci(l.moves[astra_a], astra_uci);
            const int astra_scored = sf > 0 && sf_found[astra_a];
            const int astra_leaf = kids[astra_a] < t->cap_leaf_of && t->leaf_of[kids[astra_a]] >= 0;
            fprintf(stderr, "@astra {\"kind\":\"initial_child\",\"board\":\"%s\",\"action\":%d,\"move\":\"%s\",\"sf_scored\":%d,\"sf_cp\":%d,\"matched_scores\":%d,\"ranked_floor\":%d,\"frontier\":%d,\"utility\":%.17g}\n",
                    astra_board, astra_a, astra_uci, astra_scored, astra_scored ? sf_cp[astra_a] : 0,
                    sf, ranked, astra_leaf, t->g.nodes[kids[astra_a]].value);
        }
    }
'''
SAMPLE_HOOK = r'''
    for (int astra_k = 0; astra_k < K; ++astra_k)
        fprintf(stderr, "@astra {\"kind\":\"sample\",\"index\":%d,\"chance_weight\":%.17g,\"requested\":%d,\"distinct\":%d}\n",
                idx[astra_k], share[astra_k], draws, K);
'''
ROOT_HOOK = r'''
    for (int astra_a = 0; astra_a < ours.count; ++astra_a) {
        char astra_uci[6]; move_to_uci(ours.moves[astra_a], astra_uci);
        fprintf(stderr, "@astra {\"kind\":\"root\",\"action\":%d,\"move\":\"%s\",\"probability\":%.17g,\"regret\":%.17g,\"last\":%.17g,\"selected\":%d,\"value\":%.17g,\"root_infoset\":%d}\n",
                astra_a, astra_uci, x[o + astra_a], t.g.regret[o + astra_a], t.g.last[o + astra_a],
                astra_a == best, out->value, root_I);
    }
'''
CFR_HOOK = r'''
        if (t <= 2 && player == 0) {
            const int astra_o = g->is_offset[0];
            for (int astra_a = 0; astra_a < g->is_actions[0]; ++astra_a)
                fprintf(stderr, "@astra {\"kind\":\"cfr_update\",\"iteration\":%d,\"action\":%d,\"strategy\":%.17g,\"regret_before\":%.17g,\"last_before\":%.17g,\"instantaneous\":%.17g}\n",
                        t, astra_a, x[astra_o + astra_a], g->regret[astra_o + astra_a], g->last[astra_o + astra_a], inst[astra_o + astra_a]);
        }
'''


def stage():
    assert sha(ZIP) == 'ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f'
    replay = read(REPLAY)
    audit = read(ROOT / 'astra-submissions/analysis/v38-mist-positive-20261111/result.json')
    assert sha(REPLAY) == next(r['replay_sha256'] for r in audit['records'] if r['id'] == 'c8ozqj0m')
    OUT.mkdir(exist_ok=False); BUILD.mkdir(exist_ok=False); PRIVATE.mkdir(exist_ok=False)
    members = {}
    with zipfile.ZipFile(ZIP) as archive:
        for member in archive.namelist():
            if member.startswith('src/') and member.endswith(('.c', '.h')):
                data = archive.read(member); members[member] = hashlib.sha256(data).hexdigest()
                for arm in ('control', 'trace'):
                    dest = BUILD / arm / member; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data)
        for member in ('bin/stockfish', 'data/history.bin'):
            assert sha(SHIP / member) == hashlib.sha256(archive.read(member)).hexdigest()
    assert len(members) == 19
    trace = BUILD / 'trace/src'
    text = (trace / 'main.c').read_text()
    text = replace(text, '        SearchResult r; int ok = 0;', MAIN_HOOK + '\n        SearchResult r; int ok = 0;')
    text = replace(text, '                qout[i] = out[i]', GUARD_HOOK + '\n                qout[i] = out[i]')
    (trace / 'main.c').write_text(text)
    text = (trace / 'gtcfr.c').read_text()
    text = replace(text, '#include <math.h>', '#include <math.h>\n#include <stdio.h>')
    text = replace(text, '    return l.count;\n}', CHILD_HOOK + '\n    return l.count;\n}')
    text = replace(text, '    const int K = belief_sample(b, draws, &draw_rng, idx, share);',
                   '    const int K = belief_sample(b, draws, &draw_rng, idx, share);\n' + SAMPLE_HOOK)
    text = replace(text, '    out->iterations = iteration;', '    out->iterations = iteration;\n' + ROOT_HOOK)
    (trace / 'gtcfr.c').write_text(text)
    text = (trace / 'cfr.c').read_text()
    text = replace(text, '#include <math.h>', '#include <math.h>\n#include <stdio.h>')
    text = replace(text, '        traverse(g, g->root, player, 1.0, x, inst);\n        for (int I',
                   '        traverse(g, g->root, player, 1.0, x, inst);\n' + CFR_HOOK + '\n        for (int I')
    (trace / 'cfr.c').write_text(text)
    builds = []
    for arm in ('control', 'trace'):
        command = ['gcc', '-std=c11', '-O2', '-pthread', '-D_POSIX_C_SOURCE=199309L',
                   *[str(BUILD / arm / 'src' / (name + '.c')) for name in MODULES], '-lm', '-o', str(BUILD / arm / 'mist')]
        done = subprocess.run(command, capture_output=True, text=True, timeout=90)
        builds.append(dict(arm=arm, command=command, code=done.returncode, stdout=done.stdout, stderr=done.stderr))
        save(OUT / (arm + '-build.json'), builds[-1]); assert done.returncode == 0
    frames = replay['frames']; feed = ['fow', 'w 180 2', frames[0]['white'], str(frames[0]['clocks'][0])]
    for ply in (2, 4): feed += [frames[ply-1]['white'], frames[ply]['white'], str(frames[ply]['clocks'][0])]
    (PRIVATE / 'input.txt').write_text('\n'.join(feed) + '\n')
    paths = [Path(__file__), ZIP, REPLAY, REFEREE, SHIP / 'bin/stockfish', SHIP / 'data/history.bin', PRIVATE / 'input.txt',
             *[p for arm in ('control', 'trace') for p in (BUILD / arm).rglob('*') if p.is_file()]]
    plan = dict(at=now(), scope='Two single-decision offline reconstructions for teaching. No candidate, match, model fit, performance comparison, promotion or publication.',
        game='c8ozqj0m', selected_ply_before=4, decision=3, recorded_move=frames[5]['move'], forced=['d2d4', 'c1f4'],
        selection='Third White decision in the already selected presentation win. Chosen before these outputs; no new case selection by model result.',
        arms=['control', 'trace'], seed=3751111, search_seconds=2.0, cores=[2,3], call_timeout=90, output_byte_cap=16*1024**2,
        source_members=members, changed_trace_files=['cfr.c','gtcfr.c','main.c'], dependencies={str(p):sha(p) for p in paths},
        information_boundary='Protocol contains only recorded White views and clocks. Two earlier own actions forced. No true board or opponent action input reaches either bot. Replay truth used only in later independent review.',
        limitations=['Search time shortened to two seconds; not the original arena search or exact root strategy.',
                     'Read-only annotations cost time; different node counts or moves between arms are not a strength or speed estimate.',
                     'Early belief has no claimed coverage of later capped middlegames; source output limited to first 4096 worlds.',
                     'Initial Stockfish child utilities differ from final values after tree expansion.'])
    save(OUT / 'plan.json', plan)
    print(json.dumps(dict(plan_sha256=sha(OUT/'plan.json'),builds=[(b['arm'],b['code']) for b in builds],selection=plan['selection'])),flush=True)


@contextmanager
def lease():
    owner = 'astra-' + NAME
    def change(take):
        with open('/tmp/iamavirus-cores-json.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX); path=ROOT/'chatroom/cores.json'; value=read(path)
            if take:
                assert not any(set(r['cores']) & {2,3} for r in value['allocation'])
                value['allocation'].append(dict(owner=owner,cores=[2,3],pid=os.getpid(),at=now(),purpose='fixed v38 teaching decision'))
            else: value['allocation']=[r for r in value['allocation'] if not (r['owner']==owner and r.get('pid')==os.getpid())]
            value['updated']=now(); update(path,value)
    change(True)
    try: yield
    finally: change(False)


def run():
    plan=read(OUT/'plan.json')
    for path,digest in plan['dependencies'].items(): assert sha(path)==digest,path
    state=dict(at=now(),status='running',completed=0,plan_sha256=sha(OUT/'plan.json'));save(OUT/'execution.json',state)
    started=time.monotonic()
    try:
        with lease():
            for arm in plan['arms']:
                env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_','OMP_','MKL_','OPENBLAS_'))}
                env.update(MIST_STOCKFISH=str(SHIP/'bin/stockfish'),MIST_HISTORY_TABLE=str(SHIP/'data/history.bin'),
                           ASTRA_SF_ALLCHILDREN='1',MIST_FORCE_MOVES=','.join(plan['forced']),MIST_TIMING='1',MIST_RISK='1',
                           MIST_MAX_SECONDS=str(plan['search_seconds']),FOW_SEED=str(plan['seed']),OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
                process=subprocess.Popen(['taskset','-c','2,3',str(BUILD/arm/'mist')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                         text=True,env=env,start_new_session=True)
                state.update(arm=arm,pid=process.pid);update(OUT/'execution.json',state);print(json.dumps(state),flush=True)
                try: stdout,stderr=process.communicate((PRIVATE/'input.txt').read_text(),timeout=plan['call_timeout'])
                except BaseException:
                    os.killpg(process.pid,signal.SIGKILL);stdout,stderr=process.communicate()
                    (PRIVATE/(arm+'.stdout')).write_text(stdout);(PRIVATE/(arm+'.stderr')).write_text(stderr);raise
                (PRIVATE/(arm+'.stdout')).write_text(stdout);(PRIVATE/(arm+'.stderr')).write_text(stderr)
                receipt=dict(arm=arm,code=process.returncode,stdout_sha256=sha(PRIVATE/(arm+'.stdout')),stderr_sha256=sha(PRIVATE/(arm+'.stderr')))
                save(OUT/(arm+'-execution.json'),receipt)
                assert process.returncode==0 and 'mist: stockfish ready' in stderr and 'failed to start' not in stderr
                assert len(stdout.encode())+len(stderr.encode())<=plan['output_byte_cap']
                state['completed']+=1;update(OUT/'execution.json',state)
        state['status']='complete'
    except BaseException as exc: state.update(status='failed',error=repr(exc));raise
    finally:
        state.update(ended_at=now(),seconds=time.monotonic()-started);update(OUT/'execution.json',state);print(json.dumps(state),flush=True)


if __name__ == '__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('stage','run')
    if sys.argv[1]=='stage':
        with lease(): stage()
    else: run()
