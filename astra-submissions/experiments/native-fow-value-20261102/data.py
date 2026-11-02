"""Freeze replay provenance, validate trajectories and export native leaf values.

No arena calls, source mutation, model fitting or test-score inspection.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import zipfile

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/native-fow-value-20261102'
BASE = HERE.parent / 'value-expansion-20261102/build/base'
ZIP = ROOT / 'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'
SNAP = ROOT / 'astra-submissions/analysis/arena-refresh-20261102-search/standings.json'
sys.path.insert(0, str(ROOT))
from learning import ingest, _native


def now(): return datetime.now(timezone.utc).isoformat()
def digest(data): return hashlib.sha256(data).hexdigest()
def sha(path): return digest(Path(path).read_bytes())
def write_new(path, obj):
    with Path(path).open('x') as f: json.dump(obj, f, indent=2, allow_nan=False); f.write('\n')


def encode(board):
    """Five categorical features per canonical square, plus halfmove scalar."""
    side = board.side; text = board.board_string()
    views = [board.observation(side), board.observation(side ^ 1)]
    x = np.zeros((64, 5), dtype=np.uint8)
    for dst in range(64):
        src = dst ^ (56 if side else 0)
        piece = text[src]
        if side: piece = piece.swapcase()
        x[dst, 0] = '-PNBRQKpnbrqk'.index(piece)
        x[dst, 1] = views[0][src] != '?'
        x[dst, 2] = views[1][src] != '?'
        x[dst, 3] = bool(board.castling & (1 << src))
        x[dst, 4] = board.en_passant == src
    half = min(board.halfmove_clock, 100)
    key = digest(x.tobytes() + bytes([half]))
    return x, half, key


def chosen_frames(game, states):
    candidates = [i for i in range(8, len(states) - 1) if states[i].outcome() is None]
    # Equal-width chronological bins; one hash-chosen frame from each.
    return [min(bin_.tolist(), key=lambda p: digest(f'237-position:{game}:{p}'.encode()))
            for bin_ in np.array_split(candidates, min(8, len(candidates))) if len(bin_)] if candidates else []


def freeze():
    (HERE / 'build').mkdir(exist_ok=True); (HERE / 'work').mkdir(exist_ok=True)
    with zipfile.ZipFile(ZIP) as z:
        for p in (BASE / 'src').iterdir():
            if p.suffix in ('.c', '.h'):
                assert p.read_bytes() == z.read('src/' + p.name), p
        assert (BASE / 'bin/stockfish').read_bytes() == z.read('bin/stockfish')
    src = BASE / 'src'
    cmd = ['gcc', '-std=c11', '-O2', '-Werror=format', '-pthread', '-D_POSIX_C_SOURCE=199309L', '-I', str(src),
           str(HERE / 'leaf_collect.c'), *[str(src / (n + '.c')) for n in
           ('board', 'belief', 'movemodel', 'cfr', 'eval', 'search', 'front', 'sfeval')],
           '-lm', '-o', str(HERE / 'build/leaf_collect')]
    built = subprocess.run(cmd, capture_output=True, text=True)
    write_new(OUT / 'build.json', dict(at=now(), command=cmd, exit=built.returncode,
                                     stdout=built.stdout, stderr=built.stderr))
    assert built.returncode == 0, built.stderr
    snapshot = json.loads(SNAP.read_text()); teams = {r['id'] for r in snapshot['players'] if r['rank'] <= 12}
    index = ROOT / 'data/raw/accepted.jsonl'; payload = index.read_bytes()
    by_id = {r['id']: r for r in map(json.loads, payload.splitlines())}
    selected = [r for r in by_id.values() if r.get('termination') == 'normal'
                and '2026-10-10' <= (r.get('createdAt') or '') < '2026-11-02'
                and r.get('whitePlayerId') in teams and r.get('blackPlayerId') in teams]
    folds = {k: [] for k in ('train', 'validation', 'test')}; seen = set(); duplicates = []
    for r in sorted(selected, key=lambda r: (r['createdAt'], r['id'])):
        h = r['moves_sha256']
        if h in seen: duplicates.append(r['id']); continue
        seen.add(h)
        fold = 'train' if r['createdAt'] < '2026-10-31' else 'validation' if r['createdAt'] < '2026-11-01' else 'test'
        folds[fold].append(r)
    manifest = []
    for fold, rows in folds.items():
        limit = 25000 if fold == 'train' else 2500
        chosen = sorted(rows, key=lambda r: digest(('237-game:' + r['id']).encode()))[:limit]
        for r in sorted(chosen, key=lambda r: (r['createdAt'], r['id'])):
            path = ROOT / 'data/raw/games' / r['id'] / 'replay.json'
            manifest.append(dict(fold=fold, row=r, path=str(path.relative_to(ROOT)), sha256=sha(path)))
    write_new(OUT / 'games.json', manifest)
    sources = list(src.glob('*.c')) + list(src.glob('*.h'))
    sources += list(HERE.glob('*.py')) + [HERE/'leaf_collect.c', HERE/'README.md', ROOT.parent/'fow-starter/referee.py',
        HERE/'build/leaf_collect', BASE/'bin/stockfish', ROOT/'learning/ingest.py', ROOT/'learning/rules.py',
        ROOT/'learning/_native.py', ROOT/'position.cc', ROOT/'observation.cc', ROOT/'bitboard.cc']
    sources += [_native.ensure_built(), ROOT/'learning/move_taxonomy.py']
    sources += [ROOT/p for p in _native.SOURCES+_native.HEADERS]
    plan = dict(at=now(), name='237 native FOW outcome value',
        source_zip_sha256=sha(ZIP), source_snapshot_sha256=sha(SNAP), accepted_index_sha256=digest(payload),
        games_sha256=sha(OUT/'games.json'), eligible_games=len(selected), trajectory_duplicates_removed=duplicates,
        games=dict(Counter(m['fold'] for m in manifest)),
        dependencies={str(p): sha(p) for p in sources},
        architecture={'teacher':{'width':128,'layers':4,'heads':4,'ffn':512,'dropout':0.1},
                      'student':{'embedding':128,'hidden':32,'clip':1.0,'distillation_outcome_weight':0.5}},
        optimization={'seed':2371102,'epochs_per_model':8,'batch':512,'learning_rate':0.001,'weight_decay':0.0001,
                      'optimizer':'AdamW','schedule':'cosine','loss':'game-weighted binary cross entropy',
                      'gpu_wall_cap_seconds':3600,'gradient_clip':1.0,'dtype':'float32; no OOM retry'},
        baseline='exact archived parent depth1 MultiPV child values, plus train-fitted two-parameter calibration',
        calibration={'logit_clip':1e-6,'intercept_bounds':[-5,5],'slope_bounds':[.05,5],'optimizer':'L-BFGS-B'},
        pilot_games=[next(g['row']['id'] for g in manifest if g['fold']==fold) for fold in ('train','validation','test')],
        gate={'minimum_relative_logloss_gain':0.02,'bootstrap_game_upper_difference_below':0,
              'brier_difference_max':0,'hidden_threat_logloss_difference_max':0,
              'hidden_threat_min_positions':100,'hidden_threat_min_games':30,'bootstrap_replicates':2000},
        inference_gate={'max_fp32_bytes':1048576,'max_median_microseconds':25},
        resource='CPU extraction only after pilot; GPU requires fresh free-device probe. Local ignored work while external disk unavailable.',
        scope='Off-policy value prediction. Not self-play RL, an equilibrium value, causal strength, or a release gate.')
    write_new(OUT/'plan.json', plan)
    print(json.dumps({'games':plan['games'],'eligible':len(selected),'plan_sha256':sha(OUT/'plan.json')}), flush=True)


def load():
    p = json.loads((OUT/'plan.json').read_text())
    assert sha(OUT/'games.json') == p['games_sha256']
    for name, h in p['dependencies'].items(): assert sha(ROOT/name) == h, name
    return p, json.loads((OUT/'games.json').read_text())


def run(pilot=False):
    plan, games = load(); begin = time.monotonic()
    tag = 'pilot' if pilot else 'dataset'
    target = HERE/'work'/tag; target.mkdir(exist_ok=False)
    games = [g for g in games if (g['row']['id'] in plan['pilot_games']) == pilot]
    write_new(target/'started.json',dict(at=now(),pid=os.getpid(),pilot=pilot,plan_sha256=sha(OUT/'plan.json')))
    env = {k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','OMP_','MKL_'))}
    env.update(MIST_SF_WORKERS='1',MIST_SF_MULTIPV='256',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    xs=[]; halves=[]; labels=[]; sf_values=[]; gids=[]; fold_ids=[]; threats=[]
    seen = {}; skipped = Counter(); checked_frames=0; counts=Counter(); raw_actions=0
    stderr=(target/'collector.stderr').open('w')
    proc=subprocess.Popen([str(HERE/'build/leaf_collect'),str(BASE/'bin/stockfish')],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,text=True,bufsize=1,env=env,start_new_session=True)
    write_new(target/'collector-handle.json',dict(pid=proc.pid,scope='original extraction process namespace',at=now()))
    try:
        with gzip.open(target/'native.jsonl.gz','wt') as native, gzip.open(target/'rows.jsonl.gz','wt') as records:
            for gi,g in enumerate(games):
                path=ROOT/g['path']; assert sha(path)==g['sha256'],path
                r=json.loads(path.read_text()); assert ingest.replay_hash(r)==g['row']['moves_sha256']
                states,errors=ingest.validate_replay(r); assert not errors,(r['id'],errors)
                checked_frames += len(states)
                for ply in chosen_frames(r['id'],states):
                    board=states[ply].board; parent=states[ply-1].board
                    x,half,key=encode(board)
                    if key in seen:
                        skipped[f"duplicate_{g['fold']}_after_{seen[key]}"]+=1;continue
                    seen[key]=g['fold']
                    ident=f"{r['id']}:{ply}";move=r['frames'][ply]['move']
                    line=f'{ident} {parent.board_string()} {parent.side} {parent.castling:x} {parent.en_passant} {parent.halfmove_clock} {move}\n'
                    proc.stdin.write(line);proc.stdin.flush(); response=proc.stdout.readline()
                    if not response:
                        try: rc=proc.wait(timeout=5)
                        except subprocess.TimeoutExpired: rc='not terminal after EOF'
                        raise RuntimeError(('collector stopped',rc,ident))
                    out=json.loads(response);assert out['id']==ident
                    for k in ('board','white','black'):assert out[k]==r['frames'][ply][k],(ident,k)
                    assert out['side']==board.side and int(out['castle'],16)==board.castling
                    assert out['ep']==board.en_passant and out['halfmove']==board.halfmove_clock
                    assert not out['terminal'],ident
                    a=next(a for a in out['actions'] if a['move']==move)
                    if a['found']:
                        # Utility is for the child side, opposite the scored parent mover.
                        assert abs(out['value']+math.tanh(a['cp']/400))<1e-12
                    assert -1<=out['value']<=1
                    native.write(response);raw_actions+=len(out['actions'])
                    label=.5 if r['result']=='1/2-1/2' else float((r['result']=='1-0')==(board.side==0))
                    hidden_threat=False
                    for attacker in (0,1):
                        king=board.king_square(attacker^1)
                        if board.is_attacked(king,attacker):
                            # Independent exact attacker enumeration is performed by the
                            # referee reviewer; the input feature remains only visibility.
                            import chess
                            from learning.move_taxonomy import fen
                            b=chess.Board(fen(board.board_string()));colour=chess.WHITE if attacker==0 else chess.BLACK
                            hidden_threat |= any(board.observation(attacker^1)[sq]=='?' for sq in b.attackers(colour,king))
                    row=dict(id=ident,game=r['id'],ply=ply,fold=g['fold'],game_index=gi,label=label,
                        feature_sha256=key,native_probability=(out['value']+1)/2,hidden_king_threat=bool(hidden_threat),
                        replay_sha256=g['sha256'],recorded_move=move,sf_scored=out['scored'],selected_scored=bool(a['found']))
                    records.write(json.dumps(row)+'\n')
                    xs.append(x);halves.append(half);labels.append(label);sf_values.append((out['value']+1)/2)
                    gids.append(gi);fold_ids.append(('train','validation','test').index(g['fold']));threats.append(hidden_threat);counts[g['fold']]+=1
                if (gi+1)%250==0:print(json.dumps({'at':now(),'games':gi+1,'positions':len(xs),'seconds':round(time.monotonic()-begin,2)}),flush=True)
                if time.monotonic()-begin>3600:raise TimeoutError('one-hour extraction cap')
        proc.stdin.close();rc=proc.wait(timeout=10);assert rc==0,rc
        np.savez(target/'data.npz',x=np.stack(xs),half=np.array(halves,dtype=np.uint8),y=np.array(labels,dtype=np.float32),
                 sf=np.array(sf_values,dtype=np.float32),game=np.array(gids,dtype=np.int32),fold=np.array(fold_ids,dtype=np.uint8),
                 hidden_threat=np.array(threats,dtype=np.bool_))
        receipt=dict(at=now(),status='complete',pilot=pilot,games=len(games),positions=dict(counts),checked_frames=checked_frames,
            action_values=raw_actions,duplicates=dict(skipped),collector_exit=rc,seconds=time.monotonic()-begin,
            plan_sha256=sha(OUT/'plan.json'),artifacts={p.name:sha(p) for p in target.iterdir() if p.is_file()},
            scope='Validated native baseline and outcome data, no model fitting or test score evaluation.')
        write_new(OUT/f'{tag}-receipt.json',receipt);print(json.dumps(receipt),flush=True)
    except BaseException as e:
        write_new(target/'failure.json',dict(at=now(),error=repr(e),games_processed=gi if 'gi' in locals() else 0))
        raise
    finally:
        # Only this newly created collector's own process group; no guessed PIDs.
        if proc.poll() is None:
            os.killpg(proc.pid,signal.SIGTERM)
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
        stderr.close()


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=('freeze','pilot','extract'));a=ap.parse_args()
    if a.command=='freeze':freeze()
    else:run(a.command=='pilot')
