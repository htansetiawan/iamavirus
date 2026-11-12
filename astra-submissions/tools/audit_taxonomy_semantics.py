"""Read-only taxonomy audit on already-audited presentation/match fixtures.

Checks report vocabulary and one rules-exact en-passant counterexample.
No engine, model, fit, new game, network call or deployment is invoked.
"""
from argparse import ArgumentParser
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning import move_taxonomy as mt


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def audit():
    taxonomy = ROOT / 'learning/move_taxonomy.py'
    daily = ROOT / 'learning/daily_report.py'
    source = taxonomy.read_text()
    tree = ast.parse(source)
    emitted = sorted({node.args[0].value for node in ast.walk(tree)
                      if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                      and isinstance(node.func.value, ast.Name) and node.func.value.id == 'tags'
                      and node.func.attr == 'append' and node.args and isinstance(node.args[0], ast.Constant)
                      and isinstance(node.args[0].value, str)})
    selected = next(ast.literal_eval(n.value) for n in ast.parse(daily.read_text()).body
                    if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'TAGS' for t in n.targets))
    assert len(mt.KEYS) == 19 and len(selected) == 11 and len(emitted) == 21
    referee_path = ROOT.parent / 'fow-starter/referee.py'
    spec = importlib.util.spec_from_file_location('taxonomy_audit_referee', referee_path)
    referee = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(referee)
    ep_path = ROOT / 'data/astra-spool/compact-mass-playing-20261111/jobs/mass-p3-black/replay.json'
    replay = json.loads(ep_path.read_text())
    receipt = json.loads((ep_path.parent / 'result.json').read_text())
    assert sha(ep_path) == receipt['replay_sha256']
    board = referee.FowBoard()
    repetitions = Counter({referee.position_key(board): 1})
    for frame in replay['frames'][1:119]:
        assert referee.outcome(board, repetitions) is None
        move = board.parse_uci(frame['move'])
        assert move in referee.fow_moves(board)
        board.push(move)
        repetitions[referee.position_key(board)] += 1
    move = board.parse_uci(replay['frames'][119]['move'])
    assert move.uci() == 'e5f6' and board.is_en_passant(move) and board.is_capture(move)
    assert board.piece_at(move.to_square) is None
    victim = board.piece_at(37)  # f5, the en-passant victim square
    assert victim is not None and victim.symbol() == 'p'
    board.push(move)
    assert board.piece_at(37) is None
    actual = ''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64))
    assert actual == replay['frames'][119]['board']
    ep_tags = next(m['tags'] for m in mt.label_game(replay)['moves'] if m['ply'] == 119)
    assert 'quiet' in ep_tags and 'capture' not in ep_tags
    win_path = ROOT / 'data/astra-spool/v38-mist-wins-20261111/c8ozqj0m.json'
    win = json.loads(win_path.read_text())
    prior = json.loads((ROOT / 'astra-submissions/analysis/v38-mist-positive-20261111/result.json').read_text())
    assert sha(win_path) == next(r['replay_sha256'] for r in prior['records'] if r['id'] == win['id'])
    rook = next(m for m in mt.label_game(win)['moves'] if m['ply'] == 33)
    assert rook['move'] == 'g5g7' and 'king_threat' in rook['tags'] and 'king_threat_unseen' not in rook['tags']
    with zipfile.ZipFile(ROOT / 'astra-submissions/iamavirus-v38-mist-c-allchildren.zip') as zipped:
        native = '\n'.join(zipped.read(n).decode() for n in zipped.namelist() if n.startswith('src/') and n.endswith(('.c', '.h')))
        assert 'move_taxonomy' not in native and 'taxonomy.json' not in native
    paths = [Path(__file__), taxonomy, daily, ROOT / 'tools/daily_refresh.sh', referee_path, ep_path, ep_path.parent / 'result.json', win_path]
    return dict(at=datetime.now(timezone.utc).isoformat(), source_sha256={str(p): sha(p) for p in paths},
                aggregate_keys=mt.KEYS, aggregate_key_count=len(mt.KEYS), daily_columns=selected,
                daily_column_count=len(selected), statically_emitted_tags=emitted,
                emitted_but_not_core_aggregate=sorted(set(emitted) - set(mt.KEYS)),
                en_passant=dict(game='mass-p3-black', ply=119, move='e5f6', actual_capture=True,
                                victim_square='f5', labeler_tags=ep_tags, defect='v0 destination-only victim check labels en passant quiet'),
                hidden_support_example=dict(game=win['id'], ply=33, move=rook['move'], tags=rook['tags'],
                                            explicit_hidden_support_bait_tag=False,
                                            scope='Actual v38 win; visible checking rook supported by an unseen queen. Not an unseen-check counter.'),
                data_flow=dict(uses_replay_truth_and_both_private_views=True, some_labels_use_future_frames=True,
                               all_labels_actor_observable_before_move=False,
                               native_v38_loads_taxonomy_report=False, automatic_deployed_weight_update=False),
                limitations=['Two selected already-audited fixtures, no frequency or strength inference.',
                             'The source labeler and historical reports are left unchanged.',
                             'Nineteen report metrics are overlapping tags, not nineteen exclusive strategy classes.',
                             'No full replay review or new full-field taxonomy has completed in this audit.'])


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = audit()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open('x') as stream:
            stream.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ['aggregate_key_count', 'daily_column_count', 'emitted_but_not_core_aggregate', 'en_passant', 'hidden_support_example']}, indent=2))
