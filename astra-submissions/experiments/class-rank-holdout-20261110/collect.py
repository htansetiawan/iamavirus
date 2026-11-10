"""One bounded retrospective cohort; no fitting, model inference or shared writes."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis/class-rank-holdout-20261110'
sys.path.insert(0, str(HERE.parent/'prospective-full-prior-20261110b'))
from protocol import now, sha, stamp_ns, write, check_pins, validate_listing, cohort_game
sys.path.insert(0, str(ROOT))
from learning.api_client import ApiClient


class Client(ApiClient):
    def __init__(self, plan):
        super().__init__(min_interval=1.2, timeout=20)
        self.plan = plan

    def _pace(self):
        assert self.requests_made < self.plan['request_cap'], 'request cap'
        # Let the primary prospective collector finish its bursts. No changes
        # to its execution, cursor, sources, scores or schedule are made here.
        while True:
            state = json.loads(Path(self.plan['primary_execution']).read_text())
            if state['status'] != 'running':
                break
            remaining = (datetime.fromisoformat(state['updated_at']).timestamp()
                         + 1200 - time.time())
            if remaining > 120:
                break
            time.sleep(10)
        super()._pace()


def metadata(row):
    # Current classifications/active versions can change between snapshots.
    return tuple(row.get(k) for k in ('id','createdAt','white','black','whitePlayerId',
                 'blackPlayerId','whiteVersion','blackVersion','plies','result','reason'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--publication-commit', required=True)
    args = parser.parse_args()
    plan = json.loads((OUT/'plan.json').read_text()); check_pins(plan)
    committed = subprocess.check_output(['git','show',args.publication_commit+':'+
                    str((OUT/'plan.json').relative_to(ROOT))], cwd=ROOT)
    assert committed == (OUT/'plan.json').read_bytes()
    assert not (OUT/'collection.json').exists(), 'one collection attempt'
    archive = Path(plan['archive']); archive.mkdir(exist_ok=False)
    assert archive.resolve().is_relative_to(ROOT) and os.stat(archive).st_dev == os.stat(ROOT).st_dev
    state = dict(started_at=now(), status='running', publication_commit=args.publication_commit,
                 plan_sha256=sha(OUT/'plan.json'))
    write(OUT/'collection.json', state, exclusive=True)
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('collection wall bound')))
    signal.alarm(plan['collection_seconds'])
    client = Client(plan); total_bytes = 0; rows = {}; overlap = 0
    fetches = []; decisions = []
    def store(name, data):
        nonlocal total_bytes
        total_bytes += len(data)
        assert total_bytes <= plan['archive_bytes_cap'], 'archive cap'
        path = archive/name
        with path.open('xb') as handle: handle.write(data)
        return sha(path)
    try:
        low, high = stamp_ns(plan['window'][0]), stamp_ns(plan['window'][1])
        for team in plan['priority']:
            cursor = None; seen_cursors = set(); previous = None
            params = dict(player=team, sort='played', order='desc', limit=100)
            for page in range(plan['pages_per_team']):
                data, rec = client.get_bytes('/api/games', dict(params, cursor=cursor))
                body = json.loads(data); name = f'page-{team}-{page:02d}.json'
                digest = store(name, data)
                fetches.append(dict(path=name,sha256=digest,fetch=rec.__dict__))
                assert body['sort']=='played' and body['order']=='desc'
                page_rows = body['games']
                for row in page_rows:
                    validate_listing(row)
                    assert team in (row['whitePlayerId'],row['blackPlayerId'])
                    t = stamp_ns(row['createdAt'])
                    assert previous is None or t <= previous, 'descending cursor snapshot'
                    previous = t
                    if low <= t < high:
                        old = rows.get(row['id'])
                        if old is not None:
                            assert metadata(old)==metadata(row), 'snapshot disagreement'
                            overlap += 1
                        rows[row['id']] = row
                cursor = body['nextCursor']
                if not cursor or (previous is not None and previous < low):
                    break
                assert cursor not in seen_cursors
                seen_cursors.add(cursor)
            else:
                raise RuntimeError('no complete source-window coverage within page cap')
        ordered = sorted(rows.values(),key=lambda r:(stamp_ns(r['createdAt']),r['id']))
        write(OUT/'listing.json',dict(games=ordered,pages=fetches,overlap_rows=overlap),exclusive=True)
        previous = json.loads(Path(plan['exclusions']).read_text())['games']
        denied_ids = {g['game'] for g in previous}; denied = {g['sequence_sha256'] for g in previous}
        games = []
        for row in ordered:
            if row['id'] in denied_ids:
                decisions.append(dict(game=row['id'],exclusion='excluded game ID')); continue
            if row['plies'] < 4:
                decisions.append(dict(game=row['id'],exclusion='fewer than four plies')); continue
            # Respect Fable's cache ownership. The external store is currently
            # unavailable; that permits a bounded private public-GET fallback.
            shared=ROOT/'data/raw'; cached=shared/'games'/row['id']/'replay.json'
            data=None; cache_error=None
            try:
                if cached.is_file(): data=cached.read_bytes()
                healthy=shared.is_dir() and (shared/'accepted.jsonl').is_file()
            except OSError as exc:
                healthy=False;cache_error=repr(exc)
            own=plan['own_id'] in (row['whitePlayerId'],row['blackPlayerId'])
            if data is None:
                assert not (own and healthy), 'healthy own-cache miss: defer to owner; close bounded run'
                data, rec = client.get_bytes('/api/games/'+row['id'])
                fetch=rec.__dict__
                if own: fetch=dict(fetch,owner_fallback='shared store unavailable',cache_error=cache_error)
            else:
                fetch=dict(source='existing shared cache',path=str(cached),sha256=__import__('hashlib').sha256(data).hexdigest())
            assert len(data) <= plan['replay_bytes_cap']
            digest = store(row['id']+'.json',data); replay = json.loads(data)
            assert replay.get('rulesVersion')=='fow-v1', 'unexpected rules; fail rather than skip'
            game, reason = cohort_game(row,replay,digest,denied)
            decisions.append(dict(game=row['id'],exclusion=reason,sha256=digest,fetch=fetch))
            if game is None: continue
            game['split'] = 'independent_retrospective_holdout'
            games.append(game); denied.add(game['sequence_sha256'])
            if len(games)==plan['games']: break
        assert len(games)==plan['games'], 'insufficient frozen-window independent trajectories'
        write(OUT/'cohort.json',dict(games=games,decisions=decisions,listing_sha256=sha(OUT/'listing.json'),
              plan_sha256=sha(OUT/'plan.json'),no_predictions=True),exclusive=True)
        state.update(status='complete',games=len(games),cohort_sha256=sha(OUT/'cohort.json'))
    except BaseException as exc:
        state.update(status='failed',error=repr(exc),decision='close_without_scoring')
        write(OUT/'partial-source-receipts.json',dict(pages=fetches,decisions=decisions),exclusive=True)
        raise
    finally:
        signal.alarm(0)
        state.update(ended_at=now(),requests=client.requests_made,archive_bytes=total_bytes)
        write(OUT/'collection.json',state)
        print(json.dumps(state),flush=True)


if __name__=='__main__': main()
