"""Reuse 230's immutable native exporter, with supervised labels joined last."""
from collections import Counter
import ctypes
import hashlib
import json
import time
import numpy as np
from config import ROOT, OUT, array, encode, library, position_tuple, StateKey, sha, unique
from learning import ingest, rules


def collect(plan, split, receipt_name=None, audit_rules=False):
    lib = library(); key_of = StateKey(); cases = []; receipt = []; frames_checked = 0
    digest = hashlib.sha256(); started = time.monotonic(); total_bytes = 0
    rule_parents = rule_actions = rule_consistent = 0
    for gindex, game in enumerate(g for g in plan['games'] if g['split'] == split):
        path = ROOT / 'data/raw/games' / game['game'] / 'replay.json'
        assert sha(path) == game['replay_sha256']
        replay = json.loads(path.read_text()); truth, errors = ingest.validate_replay(replay)
        assert not errors, (game['game'], errors)
        frames_checked += len(truth); lib.pl_start(game['us']); found = []; audit = []; stop = 'replay_end'
        for ply in range(1, len(replay['frames']) - 1):
            parents = lib.pl_count()
            if not parents or parents > 4096 or lib.pl_capped():
                stop = 'empty' if not parents else 'cap' if lib.pl_capped() else 'size_limit'; break
            frame = replay['frames'][ply]; view = frame[('white', 'black')[game['us']]]
            if (ply - 1) % 2 == game['us']:
                lib.pl_own(encode(frame['move']), view.encode()); continue
            if parents > 256:
                lib.pl_opponent(view.encode()); continue
            pieces = []; u = []; hn = []; pkeys = []; sizes = []
            for i in range(parents):
                current = array(lib.pl_position(i), 1)[0]
                assert key_of(*position_tuple(current)) == int(current['key'])
                pkeys.append(int(current['key']))
                n = ctypes.c_int(); w = ctypes.c_float(); N = ctypes.c_uint()
                ptr = lib.pl_parent(i, view.encode(), ctypes.byref(n), ctypes.byref(w), ctypes.byref(N))
                rows = array(ptr, n.value); assert n.value > 0
                if audit_rules:
                    position = rules.Board.from_board_string(*position_tuple(current))
                    position.halfmove_clock = int(current['halfmove'])
                    legal = {encode(m): m for m in position.legal_moves()}
                    assert set(legal) == set(map(int, rows['move'])) and len(legal) == len(rows)
                    rule_parents += 1
                    for action in rows:
                        child = position.copy(); child.push(legal[int(action['move'])])
                        consistent = not child.mover_lost() and child.observation(game['us']) == view
                        assert consistent == bool(action['key'])
                        if consistent:
                            state = (child.board_string(), child.side, child.castling, child.en_passant)
                            assert state == position_tuple(action) and key_of(*state) == int(action['key'])
                            rule_consistent += 1
                        rule_actions += 1
                pieces.append(rows); sizes.append(n.value); u.append(w.value); hn.append(N.value)
            lib.pl_opponent(view.encode())
            assert lib.pl_count() and not lib.pl_capped()
            actions = np.concatenate(pieces); native = np.concatenate([array(lib.pl_position(i), 1) for i in range(lib.pl_count())])
            a_parent = np.repeat(np.arange(parents), sizes)
            # No target data has been supplied to the exporter or native update.
            target = truth[ply].board; before = truth[ply - 1].board
            target_key = key_of(target.board_string(), target.side, target.castling, target.en_passant)
            parent_key = key_of(before.board_string(), before.side, before.castling, before.en_passant)
            valid = actions['key'] != 0; positive = valid & (actions['key'] == target_key)
            actor_parent = np.array(pkeys, np.uint64) == parent_key
            actor_edge = actor_parent[a_parent] & (actions['move'] == encode(frame['move']))
            # Preserve missing-support records; no insertion or invented target.
            supported = bool(positive.any()) and bool(actor_edge.any())
            assert np.all(~actor_edge | positive)
            mass = np.exp(native['base'].astype(float)); truth_mass = float(mass[native['key'] == target_key].sum() / mass.sum())
            captured = sum(c.islower() if game['us'] else c.isupper() for c in replay['frames'][ply - 1]['board']) > sum(c.islower() if game['us'] else c.isupper() for c in frame['board'])
            src = ord(frame['move'][0]) - 97 + 8 * (int(frame['move'][1]) - 1)
            surprise = captured and replay['frames'][ply - 1][('white', 'black')[game['us']]][src] == '?'
            item = dict(x=actions['x'].copy(), base=actions['base'].copy(), counts=actions['history_count'].copy(),
                u=np.array(u, np.float32), hn=np.array(hn, np.uint32), a_parent=a_parent,
                valid=valid, positive=positive, actor_parent=actor_parent, actor_edge=actor_edge)
            item['meta'] = dict(game=game['game'], ply=ply, us=game['us'], actor=game['actor'],
                parents=parents, worlds=len(native), actions=len(actions), natural_support=supported,
                primary=len(native) > 1 and len(np.unique(a_parent[valid])) > 1,
                surprise=bool(surprise), late=ply >= 16, baseline_truth_mass=truth_mass)
            found.append(item)
            audit.append(item['meta'])
        lib.pl_free()
        if split == 'train':
            found = sorted(sorted(found, key=lambda row: hashlib.sha256(f"posterior231:{game['game']}:{row['meta']['ply']}".encode()).digest())[:plan['train_cases_per_game']], key=lambda row: row['meta']['ply'])
        for row in found:
            for key in ('x', 'base', 'counts', 'u', 'hn', 'a_parent', 'valid', 'positive', 'actor_parent', 'actor_edge'):
                digest.update(row[key].tobytes()); total_bytes += row[key].nbytes
            assert total_bytes <= plan['max_feature_bytes'], 'Feature memory bound exceeded'
            cases.append(row)
        receipt.append(dict(game=game['game'], stop=stop, stop_ply=ply, exported=len(audit), retained=len(found),
            decisions=audit, selected_plies=[r['meta']['ply'] for r in found]))
        if (gindex + 1) % 100 == 0:
            print(json.dumps({'collect': split, 'games': gindex + 1, 'cases': len(cases), 'bytes': total_bytes}), flush=True)
    result = dict(split=split, games=receipt, cases=len(cases), bytes=total_bytes,
        validated_frames=frames_checked, features_sha256=digest.hexdigest(), elapsed=time.monotonic() - started)
    if audit_rules:
        result['independent_rules'] = dict(parents=rule_parents, actions=rule_actions, consistent=rule_consistent)
    unique(OUT / (receipt_name or (split + '-data.json')), result)
    print(json.dumps({k: v for k, v in result.items() if k != 'games'}), flush=True)
    return cases
