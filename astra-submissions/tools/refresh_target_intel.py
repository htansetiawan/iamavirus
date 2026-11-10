"""Bounded target replay refresh, using the existing validated shared raw store.

Leaves IAmAVirus replay downloads to Fable's existing watcher. It neither
changes the tested engine nor fits weights. Public GETs only, sequential.
"""
from collections import Counter
from datetime import datetime, timezone
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning import api_client, ingest, move_taxonomy

TARGETS = ['duck', 'Instructors', 'HYPOTHERMIA', 'Greek Gift', 'Mist Opportunities']
ME = 'a2c35173659545c99752376a70418438'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')


def run(args):
    args.out.mkdir(exist_ok=False)
    lock = (args.raw/'.astra-target-refresh.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    os.sched_setaffinity(0, {6})
    os.nice(10)
    start = time.monotonic()
    store = ingest.RawStore(args.raw)
    # Read one complete append-only prefix; a concurrently arriving last line
    # is excluded rather than interpreted as malformed existing data.
    with store.accepted.open('rb') as handle:
        data = handle.read(os.fstat(handle.fileno()).st_size)
    data = data[:data.rfind(b'\n')+1]
    known = {json.loads(line)['id'] for line in data.splitlines() if line.strip()}
    prefix = dict(bytes=len(data), sha256=sha(data), unique_ids=len(known))
    del data
    client = api_client.ApiClient(min_interval=1.2, cache_dir=args.raw, timeout=30)
    counts = Counter()
    targets, new_games, error = [], [], None
    def expired(*_):
        raise TimeoutError('Target refresh 900-second wall limit')
    old_handler = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 900)
    try:
        leaderboard, record = client.leaderboard()
        write(args.out/'leaderboard.json', dict(data=leaderboard, fetch=record.__dict__))
        stamp = record.fetched_at.replace(':', '').replace('+', 'Z')
        store.write_json(store.snapshots/stamp/'leaderboard.json',
                         dict(leaderboard=leaderboard, fetched=record.__dict__))
        players = {p['name']: p for p in leaderboard['players']}
        for name in TARGETS:
            player = players[name]
            params = dict(player=player['id'], sort='played', order='desc', limit=100)
            cursor, summaries = None, []
            for page_number in range(2):
                assert client.requests_made < 495
                page, fetch = client.games_page(params, cursor)
                write(args.out/'listings'/f"{name.replace(' ', '_')}-{page_number}.json",
                      dict(data=page, fetch=fetch.__dict__))
                summaries.extend(page['games'])
                cursor = page['nextCursor']
                if not cursor:
                    break
            counts['listed'] += len(summaries)
            for summary in summaries:
                game_id = summary['id']
                if game_id in known and (store.games/game_id/'replay.json').exists():
                    counts['cached'] += 1
                    continue
                if ME in (summary.get('whitePlayerId'), summary.get('blackPlayerId')):
                    counts['left_to_existing_own_team_watcher'] += 1
                    continue
                if client.requests_made >= 495:
                    raise RuntimeError('Target refresh request bound')
                replay, fetch, cached = client.replay(game_id)
                counts['cache_recovered' if cached else 'fetched'] += 1
                problems = ingest.ingest_replay(store, replay, summary,
                    dict(replay=fetch.__dict__, listing_source='/api/games', collector='astra-target-refresh'), None)
                if problems:
                    counts['quarantined'] += 1
                    raise RuntimeError(f'New replay {game_id} quarantined: {problems}')
                known.add(game_id)
                counts['accepted'] += 1
                item = dict(id=game_id, replay_sha256=sha((store.games/game_id/'replay.json').read_bytes()),
                            moves_sha256=ingest.replay_hash(replay), createdAt=replay['createdAt'])
                new_games.append(item)
                with (args.out/'new-games.jsonl').open('a') as handle:
                    handle.write(json.dumps(item)+'\n')
                if counts['accepted'] % 25 == 0:
                    print(json.dumps(dict(target=name, counts=dict(counts), requests=client.requests_made)), flush=True)
            # Only the version active at the frozen leaderboard enters the
            # taxonomy. All versions remain in the shared raw training corpus.
            labelled, scores, ids, exclusions = [], [], [], Counter()
            for summary in summaries:
                side = 'white' if summary['whitePlayerId'] == player['id'] else 'black'
                if summary.get(side+'Version') != player['activeVersion']:
                    exclusions['older_version'] += 1
                    continue
                path = store.games/summary['id']/'replay.json'
                if summary['id'] not in known or not path.exists():
                    exclusions['unavailable'] += 1
                    continue
                replay = json.loads(path.read_text())
                if ingest.classify_termination(replay['result'], replay['reason']) != 'normal':
                    exclusions['technical'] += 1
                    continue
                labelled.append(move_taxonomy.label_game(replay))
                ids.append(dict(id=summary['id'], side=side, replay_sha256=sha(path.read_bytes())))
                value = {'1-0': 1, '0-1': 0, '1/2-1/2': .5}[replay['result']]
                scores.append(value if side == 'white' else 1-value)
            sides = {item['id']: item['side'] for item in ids}
            taxonomy = move_taxonomy.aggregate(labelled, lambda game: sides[game['id']])
            row = dict(team=name, team_id=player['id'], active_version=player['activeVersion'],
                       rating=player['rating'], listed=len(summaries),
                       newest=max((s['createdAt'] for s in summaries), default=None),
                       oldest=min((s['createdAt'] for s in summaries), default=None),
                       score=sum(scores)/len(scores) if scores else None, games_used=ids,
                       exclusions=dict(exclusions), taxonomy=taxonomy)
            targets.append(row)
            write(args.out/f"{name.replace(' ', '_')}.json", row)
            print(json.dumps(dict(target=name, done=True, counts=dict(counts), taxonomy_games=len(ids))), flush=True)
        write(args.out/'summary.json', dict(targets=targets,
              scope='Latest 200 listed games per target; taxonomy current active version and normal cached/accepted games only. '
                    'Mixed opponents/colors and unequal time coverage; descriptive, not standardized strength or causal skill. '
                    'Labels do not update any model or guard.'))
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
        write(args.out/'receipt.json', dict(at=datetime.now(timezone.utc).isoformat(),
              completed=error is None, error=error, counts=dict(counts), requests=client.requests_made,
              elapsed_seconds=time.monotonic()-start, accepted_prefix=prefix, new_games=new_games,
              completed_targets=len(targets), source_sha256=sha(Path(__file__).read_bytes()),
              dependencies={str(p):sha(p.read_bytes()) for p in [Path(ingest.__file__),
                            Path(api_client.__file__), Path(move_taxonomy.__file__)]}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', type=Path, default=ROOT/'data/raw')
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args())
