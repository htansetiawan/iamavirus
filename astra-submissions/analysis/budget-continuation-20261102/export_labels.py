"""Export audited continuation targets with linear-size private-history references.

These four development source groups are not a training or confirmation corpus.
Oracle boards stay in the replay, outside the actor projection. Censoring yields
no terminal-return target. Historical arena outcomes are never target inputs.
"""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def actor_input(game, ply):
    side = ply % 2
    key = ('white', 'black')[side]
    frames = game['frames']
    return dict(side=key, time_control=game['timeControl'],
                observations=[f[key] for f in frames[:ply + 1]],
                own_moves=[frames[i + 1]['move'] for i in range(side, ply, 2)],
                own_turn_clocks=[frames[i]['clocks'][side] for i in range(side, ply + 1, 2)],
                own_post_move_clocks=[frames[i + 1]['clocks'][side] for i in range(side, ply, 2)])


def main():
    review = json.loads((OUT / 'review.json').read_text())
    summary = json.loads((OUT / 'summary.json').read_text())
    plan = json.loads((OUT / 'plan.json').read_text())
    assert review['passed'] and review['summary_sha256'] == sha(OUT / 'summary.json')
    assert summary['complete'] and summary['attempted'] == len(plan['jobs'])
    receipts = {r['job']['id']: r for r in summary['rows']}
    rows, games, reward_rows = [], [], 0
    for job in plan['jobs']:
        case = plan['cases'][job['case']]
        path = OUT / job['id'] / 'replay.json'
        assert sha(path) == receipts[job['id']]['replay_sha256']
        game = json.loads(path.read_text())
        first, stop = case['branch_ply'], len(game['frames']) - 1
        censored = game['censored']
        white_return = None if censored else {'1-0': 1, '0-1': -1, '1/2-1/2': 0}[game['result']]
        games.append(dict(id=job['id'], replay=str(path.relative_to(OUT)), sha256=sha(path),
                          source_group=case['game'], seed=job['seed'],
                          max_seconds=job['max_seconds'], censored=censored,
                          first_decision=first, decisions=stop-first))
        for ply in range(first, stop):
            side = ply % 2
            value = None if white_return is None else white_return * (1 if side == 0 else -1)
            projection = actor_input(game, ply)
            # Check references against the inputs actually delivered to this bot.
            events = [e for e in game['protocol']['events']
                      if e['side'] == projection['side'] and e['direction'] == 'input' and e['ply'] <= ply]
            views = [e['text'] for e in events if len(e['text']) == 64]
            assert views == projection['observations']
            clocks = [float(e['text']) for e in events if len(e['text']) != 64
                      and e['text'] != 'fow' and not e['text'].startswith(('w ', 'b '))]
            assert len(clocks) == len(projection['own_turn_clocks'])
            assert all(abs(a-b) < 2e-6 for a, b in zip(clocks, projection['own_turn_clocks']))
            payload = json.dumps(projection, sort_keys=True, separators=(',', ':')).encode()
            rows.append(dict(id=f"{job['id']}:{ply}", source_group=case['game'],
                             continuation=job['id'], ply=ply, side=projection['side'],
                             actor_history=dict(replay=job['id']+'/replay.json', through_ply=ply,
                                                side=projection['side'], projection_sha256=hashlib.sha256(payload).hexdigest()),
                             action=game['frames'][ply+1]['move'], terminal_return=value,
                             censored=censored, target='fixed-policy terminal return, actor perspective'))
            reward_rows += value is not None
    with (OUT / 'decisions.jsonl').open('x') as f:
        for row in rows:
            f.write(json.dumps(row, separators=(',', ':')) + '\n')
    manifest = dict(schema=1, source_groups=len({c['game'] for c in plan['cases']}),
                    continuations=len(games), decision_rows=len(rows), terminal_return_rows=reward_rows,
                    censored_rows=len(rows)-reward_rows, games=games,
                    plan_sha256=sha(OUT/'plan.json'), review_sha256=sha(OUT/'review.json'),
                    exporter_sha256=sha(Path(__file__)), decisions_sha256=sha(OUT/'decisions.jsonl'),
                    split_contract='All prefixes, arms, repeats, and decisions from one source game stay in one split.',
                    correlation='Decision rows reuse one terminal event per continuation; source groups, not rows, are independent units.',
                    allowed_actor_projection='actor_input() in export_labels.py; excludes true boards, opponent views/moves/clocks and future frames.',
                    status='Development mechanics and cost pilot only. No model fit or population validation.')
    with (OUT/'dataset.json').open('x') as f:
        json.dump(manifest, f, indent=2)
        f.write('\n')
    print(json.dumps({k:manifest[k] for k in ('source_groups','continuations','decision_rows','terminal_return_rows','censored_rows')}))


if __name__ == '__main__':
    main()
