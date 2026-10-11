#!/usr/bin/env python3
"""Rules-check new public replays and retain a versioned tactical corpus.

This uses truth only for retrospective labels. It does not run an engine or
estimate playing strength. Time/protocol forfeits are retained but excluded
from board-terminal validation, since their cause is outside board rules.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

from m4_match_audit import audit


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--poll', type=Path, required=True)
    ap.add_argument('--replays', type=Path, required=True)
    ap.add_argument('--referee', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise ValueError('Use a new output directory; preserve earlier attempts')
    args.out.mkdir(parents=True)
    shutil.copyfile(args.poll, args.out/'poll.json')
    shutil.copyfile(args.referee, args.out/'referee.py')
    poll = json.loads((args.out/'poll.json').read_text())
    spec = importlib.util.spec_from_file_location('frozen_referee', args.out/'referee.py')
    referee = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(referee)
    sources, rows, skipped = [], [], []
    for event in poll['new_results']:
        path = args.replays/(event['game']+'.json.gz')
        replay = json.loads(gzip.decompress(path.read_bytes()))
        assert replay['id'] == event['game']
        assert replay[event['side']+'Version'] == event['arena_version']
        sources.append({'game': event['game'], 'source': str(path.resolve()), 'sha256': sha(path)})
        if replay['reason'] not in ('King capturable', 'Threefold repetition', '50-move rule', 'No legal moves'):
            skipped.append({'event': event, 'reason': 'Non-board termination requires a separate diagnostics audit'})
            continue
        row = audit(replay, event['side'], referee)
        row['event'] = event
        rows.append(row)
    record, opponents = Counter(), defaultdict(Counter)
    losses = []
    for row in rows:
        event = row['event']
        record[event['result']] += 1
        opponents[event['opponent']][event['result']] += 1
        if event['result'] == 'L' and row['reason'] == 'King capturable':
            losses.append(row)
    summary = {
        'classification': 'New completed public games, independently validated; retrospective labels, not an Elo estimate',
        'poll_at': poll['at'], 'polled_games': len(poll['new_results']), 'validated_games': len(rows),
        'frames_validated': sum(r['frames_validated'] for r in rows),
        'own_decisions': sum(len(r['decisions']) for r in rows),
        'validated_record': dict(record), 'opponent_records': dict(opponents),
        'king_losses': len(losses),
        'losses_with_immediate_survival_alternatives': sum(bool(r['decisions'][-1]['safe_moves']) for r in losses),
        'losses_with_only_hidden_terminal_attackers': sum(bool(r['terminal_attackers']) and
            all(not a['visible'] for a in r['terminal_attackers']) for r in losses),
        'losses_after_unchanged_observation': sum(not r['decisions'][-1]['opponent_move_changed_view'] for r in losses),
        'skipped': skipped, 'sources': sources,
        'poll_sha256': sha(args.out/'poll.json'), 'referee_sha256': sha(args.out/'referee.py'),
        'auditor_sha256': sha(Path(__file__).with_name('m4_match_audit.py')), 'tool_sha256': sha(Path(__file__)),
        'limitations': ['Game results are correlated and have varying opponents; no treatment comparison.',
            'Immediate survival is neither a winning continuation nor proof the bot could identify it.',
            'Public replays do not expose internal belief or search state.']}
    with gzip.open(args.out/'audits.json.gz', 'wt') as f:
        json.dump(rows, f)
    summary['audits_sha256'] = sha(args.out/'audits.json.gz')
    (args.out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('sources','limitations')}, indent=2))


if __name__ == '__main__':
    main()
