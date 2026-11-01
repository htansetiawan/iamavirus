#!/usr/bin/env python3
"""Freeze chronological games and extract packed actor-visible examples."""
from array import array
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis/visible-response-20261101'
BUILD = HERE/'build'
sys.path.insert(0, str(ROOT))
from learning import features, ingest
from learning.histories import phase_of_frame

TEAMS = ['Greek Gift', 'Knight Vision', 'Strongly Invisible', 'Decent Chess Bot',
         'Crimson Fog', 'Instructors', 'Mist Opportunities', 'duck', 'HYPOTHERMIA']
WINDOWS = {'train': ['2026-10-20', '2026-10-28', 4000],
           'validation': ['2026-10-28', '2026-10-30', 600],
           'test': ['2026-10-30', '2026-11-01', 1000]}


def sha(data): return hashlib.sha256(data).hexdigest()


def encode_view(view, side):
    out = np.zeros(64, dtype=np.uint8)
    for sq, token in enumerate(view):
        c = features.relative_class(token, side)
        out[sq ^ (56 if side else 0)] = 12 if c < 0 else 13 if c == 12 else c
    return out


def encode_move(move, side):
    flip = 56 if side else 0
    def square(s): return (ord(s[0])-97 + 8*(int(s[1])-1)) ^ flip
    return square(move[:2]) | square(move[2:4]) << 6 | ((' nbrq'.index(move[4]) if len(move) == 5 else 0) << 12)


def actor_decisions(replay, side):
    tracker = features.FeatureTracker(side); key = ['white', 'black'][side]
    frames = replay['frames']
    for ply, frame in enumerate(frames[:-1]):
        tracker.observe(frame[key], phase_of_frame(ply, frames, side), ply)
        if ply % 2 != side: continue
        legal = sorted(tracker.legal_candidates())
        move = frames[ply+1]['move']
        yield ply, encode_view(frame[key], side), legal, move
        tracker.record_own_move(move)


def freeze():
    OUT.mkdir(exist_ok=True, parents=True); BUILD.mkdir(exist_ok=True)
    assert not (OUT/'manifest.json').exists()
    raw = (ROOT/'data/raw/accepted.jsonl').read_bytes()
    rows = {r['id']: r for r in map(json.loads, raw.splitlines())}
    excluded = set()
    for rel in ['temporal-prior-20261101/manifest.json', 'temporal-prior-20261101/data-v2/manifest.json',
                'king-event-calibration-20261101/plan.json']:
        p = OUT.parent/rel
        if p.exists():
            for g in json.loads(p.read_text()).get('games', []):
                if isinstance(g, dict): excluded.add(g.get('id', g.get('game')))
    choices = sorted([r for r in rows.values() if r['id'] not in excluded
                      and any(r.get(s) in TEAMS for s in ['white', 'black'])],
                     key=lambda r: sha(('visible-response208:'+r['id']).encode()))
    selected = []; seen = set()
    for split, (lo, hi, count) in WINDOWS.items():
        group = []
        for r in choices:
            if not lo <= (r.get('createdAt') or '') < hi: continue
            payload = (ROOT/'data/raw/games'/r['id']/'replay.json').read_bytes()
            replay = json.loads(payload)
            if replay.get('rulesVersion') != 'fow-v1': continue
            sequence = sha(' '.join(f['move'] for f in replay['frames'][1:]).encode())
            if sequence in seen: continue
            seen.add(sequence)
            group.append(dict(game=r['id'], index=len(selected)+len(group), split=split,
                              white=r['white'], black=r['black'], created_at=r['createdAt'],
                              white_version=r.get('whiteVersion'), black_version=r.get('blackVersion'),
                              replay_sha256=sha(payload), sequence_sha256=sequence))
            if len(group) == count: break
        assert len(group) == count, (split, len(group))
        selected.extend(group)
    plan = dict(created_at=datetime.now(timezone.utc).isoformat(), teams=TEAMS, windows=WINDOWS,
                games=selected, excluded_ids=sorted(x for x in excluded if x), accepted_sha256=sha(raw),
                data_source_sha256=sha(Path(__file__).read_bytes()),
                selection='Fixed hash within chronological windows; no result or move-quality selection; complete-sequence dedup across splits.',
                inputs='Actor current observation plus legal candidates derived from permitted history. Team/result/true board are not inputs.')
    (OUT/'manifest.json').write_text(json.dumps(plan, indent=2)+'\n')
    print(json.dumps({'games': dict(Counter(g['split'] for g in selected)), 'excluded_ids': len(excluded)}))


def prepare():
    plan = json.loads((OUT/'manifest.json').read_text())
    assert sha(Path(__file__).read_bytes()) == plan['data_source_sha256']
    receipts = []
    for split in WINDOWS:
        destination = BUILD/(split+'.npz'); assert not destination.exists()
        tokens=array('B'); actions=array('H'); offsets=array('Q',[0]); target=array('H')
        game_index=array('I'); plies=array('H'); sides=array('B'); teams=array('B')
        frames_checked = 0; version_counts = Counter(); n_games = 0
        for g in [x for x in plan['games'] if x['split'] == split]:
            payload = (ROOT/'data/raw/games'/g['game']/'replay.json').read_bytes()
            assert sha(payload) == g['replay_sha256']
            replay = json.loads(payload); states, errors = ingest.validate_replay(replay)
            assert not errors, (g['game'], errors)
            frames_checked += len(states)
            for side, key in enumerate(['white', 'black']):
                if replay[key] not in TEAMS: continue
                for ply, view, legal, actual in actor_decisions(replay, side):
                    truth_legal = sorted(states[ply].board.legal_moves())
                    if legal != truth_legal:
                        failure=dict(game=g['game'], side=side, ply=ply, observed=legal, truth=truth_legal)
                        (OUT/'legal-mismatch.json').write_text(json.dumps(failure, indent=2)+'\n')
                        raise RuntimeError(failure)
                    assert actual in legal
                    if len(legal) < 2: continue
                    encoded = [encode_move(m, side) for m in legal]
                    assert all(view[m & 63] < 6 for m in encoded)
                    tokens.extend(view.tolist()); actions.extend(encoded); offsets.append(len(actions)); target.append(legal.index(actual))
                    game_index.append(g['index']); plies.append(ply); sides.append(side); teams.append(TEAMS.index(replay[key]))
                    version_counts[f"{replay[key]}:v{replay.get(key+'Version')}"] += 1
            n_games += 1
            if n_games % 250 == 0: print(split, n_games, 'games', len(target), 'decisions', flush=True)
        arrays = dict(tokens=np.frombuffer(tokens,dtype=np.uint8).reshape(-1,64), actions=np.frombuffer(actions,dtype=np.uint16),
                      offsets=np.frombuffer(offsets,dtype=np.uint64), target=np.frombuffer(target,dtype=np.uint16),
                      game=np.frombuffer(game_index,dtype=np.uint32), ply=np.frombuffer(plies,dtype=np.uint16),
                      side=np.frombuffer(sides,dtype=np.uint8), team=np.frombuffer(teams,dtype=np.uint8))
        assert sum(a.nbytes for a in arrays.values()) < 256*1024**2
        np.savez(destination, **arrays)
        rec=dict(split=split, games=n_games, decisions=len(target), actions=len(actions), frames_checked=frames_checked,
                 bytes=destination.stat().st_size, sha256=sha(destination.read_bytes()), versions=dict(version_counts))
        receipts.append(rec); (OUT/'data-receipts.json').write_text(json.dumps(receipts, indent=2)+'\n')
        print(json.dumps({k:v for k,v in rec.items() if k != 'versions'}), flush=True)
    assert sum(r['bytes'] for r in receipts) < 400*1024**2


if __name__ == '__main__': globals()[sys.argv[1]]()
