"""Bounded, sequential public replay collector; models stay unopened here."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from protocol import (ROOT, OUT, OWN, now, instant, stamp_ns, sha, write, check_pins,
                      own_game, validate_listing, ordered_candidates, cohort_game)
sys.path.insert(0, str(ROOT))
from learning.api_client import ApiClient, atomic_write
from learning.ingest import validate_replay


class BudgetClient(ApiClient):
    def __init__(self, budget):
        super().__init__(min_interval=1.2, timeout=30)
        self.budget = budget

    def _pace(self):
        if self.requests_made >= self.budget:
            raise RuntimeError('frozen request budget exhausted')
        super()._pace()


def snapshot(client, cutoff, archive, tick, page_cap):
    """Require complete fixed-cursor coverage back to the cutoff before sealing."""
    rows = {}
    cursor = None
    previous = None
    params = dict(sort='played', order='desc', limit=100)
    for page_index in range(page_cap):
        page, record = client.games_page(params, cursor)
        write(archive / f'page-{tick:03d}-{page_index:02d}.json',
              dict(page=page, fetch=record.__dict__), exclusive=True)
        assert page['sort'] == 'played' and page['order'] == 'desc'
        reached_cutoff = False
        for row in page['games']:
            validate_listing(row)
            at = stamp_ns(row['createdAt'])
            assert previous is None or at <= previous, 'nonmonotone completed snapshot'
            previous = at
            assert row['id'] not in rows, 'duplicate ID within a fixed snapshot'
            if at < stamp_ns(cutoff):
                reached_cutoff = True
            rows[row['id']] = row
        cursor = page['nextCursor']
        if reached_cutoff or not cursor:
            return ordered_candidates(rows.values(), cutoff), page_index + 1
    raise RuntimeError('page cap reached before cutoff: incomplete coverage cannot seal a cohort')


def shared_store_available(raw):
    try:
        return raw.is_dir() and (raw/'games').is_dir() and (raw/'accepted.jsonl').is_file() and (raw/'accepted.jsonl').stat().st_size > 0
    except OSError:
        return False


def source(row, client, plan, archive):
    game = row['id']
    own = archive / 'games' / game
    saved = own / 'replay.json'
    if saved.exists():
        receipt = json.loads((own / 'fetch.json').read_text())
        assert sha(saved) == receipt['sha256']
        return json.loads(saved.read_bytes()), receipt
    shared_root = Path(plan['shared_raw'])
    shared = shared_root / 'games' / game / 'replay.json'
    data, cache_error = None, None
    try:
        if shared.is_file():
            data = shared.read_bytes()
    except OSError as exc:
        cache_error = repr(exc)
    if data is not None:
        receipt = dict(source='existing shared cache', path=str(shared), fetched_at=now())
    elif own_game(row) and not (plan.get('owner_fallback_on_store_loss',False)
                               and (cache_error is not None or not shared_store_available(shared_root))):
        # The existing Fable watcher owns collection of IAmAVirus games. Wait
        # for its next tick; never skip an earlier missing game to fill a cohort.
        return None, dict(source='deferred to Fable watcher', game=game)
    else:
        data, record = client.get_bytes('/api/games/' + game)
        receipt = dict(source='public completed-game API', fetch=record.__dict__)
        if own_game(row):
            receipt.update(owner_fallback='shared store unavailable',cache_error=cache_error,
                           shared_raw=str(shared_root))
    assert len(data) <= plan['replay_bytes_cap'], 'replay exceeds frozen byte bound'
    replay = json.loads(data)
    own.mkdir(parents=True, exist_ok=False)
    receipt.update(sha256=atomic_write(saved, data), stored_at=now())
    write(own / 'fetch.json', receipt, exclusive=True)
    return replay, receipt


def seal_candidates(rows, client, plan, archive, denied):
    games, decisions, pending = [], [], None
    seen = set(denied)
    for row in rows:
        replay, fetch = source(row, client, plan, archive)
        if replay is None:
            pending = fetch
            break
        game, reason = cohort_game(row, replay, fetch['sha256'], seen)
        if game is not None:
            _, problems = validate_replay(replay)
            assert not problems, (row['id'], problems)  # Do not discard mismatches to obtain a pass.
            seen.add(game['sequence_sha256'])
            games.append(game)
        decisions.append(dict(game=row['id'], created_at=row['createdAt'], eligible=game is not None,
                              exclusion=reason, source=fetch))
        if len(games) == plan['games']:
            return games, decisions, None
    return games, decisions, pending


def record_terminal(state, archive):
    """Keep the original failure while making incomplete completion fail closed."""
    try:
        write(archive / 'execution.json', state)
    except OSError as exc:
        state['archive_terminal_receipt_error'] = repr(exc)
        if state['status'] == 'complete':
            state.update(status='failed',phase='closed without scoring',error=repr(exc))
            write(OUT / 'execution.json', state)
            raise
    write(OUT / 'execution.json', state)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--publication-commit', required=True)
    args = parser.parse_args()
    plan = json.loads((OUT / 'plan.json').read_text())
    check_pins(plan)
    assert len(args.publication_commit) == 40
    committed = subprocess.check_output(['git', 'show', args.publication_commit + ':' +
                                         str((OUT / 'plan.json').relative_to(ROOT))], cwd=ROOT)
    assert committed == (OUT / 'plan.json').read_bytes()
    assert datetime.now(timezone.utc) < instant(plan['cutoff']), 'missed prospective launch; do not shift the cutoff'
    archive = Path(plan['archive'])
    archive.mkdir(parents=True, exist_ok=False)
    state = dict(started_at=now(), status='running', phase='waiting for cutoff', pid=os.getpid(),
                 publication_commit=args.publication_commit, plan_sha256=sha(OUT / 'plan.json'),
                 requests=0, collected=0, ticks=0)
    write(OUT / 'execution.json', state, exclusive=True)
    write(archive / 'launch.json', state, exclusive=True)
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('13-hour collector wall cap')))
    signal.alarm(plan['wall_seconds'])
    client = BudgetClient(plan['request_cap'])
    denied = {g['sequence_sha256'] for g in json.loads(Path(plan['previous_plan']).read_text())['games']}
    ticks = 0
    try:
        while datetime.now(timezone.utc) < instant(plan['cutoff']):
            time.sleep(max(0, min(30, (instant(plan['cutoff']) - datetime.now(timezone.utc)).total_seconds())))
        while datetime.now(timezone.utc) <= instant(plan['data_deadline']):
            rows, pages = snapshot(client, plan['cutoff'], archive, ticks, plan['page_cap'])
            rows = [row for row in rows if stamp_ns(row['createdAt']) <= stamp_ns(plan['data_deadline'])]
            # No older snapshot may silently change an immutable completed row.
            games, decisions, pending = seal_candidates(rows, client, plan, archive, denied)
            write(archive / f'tick-{ticks:03d}.json', dict(at=now(), pages=pages,
                  candidates=len(rows), eligible=len(games), pending=pending, decisions=decisions), exclusive=True)
            ticks += 1
            state.update(phase='collecting', requests=client.requests_made,
                         collected=len(games), ticks=ticks, pending=pending, updated_at=now())
            write(OUT / 'execution.json', state)
            print(json.dumps(state), flush=True)
            if sum(p.stat().st_size for p in archive.rglob('*') if p.is_file()) > plan['archive_bytes_cap']:
                raise RuntimeError('frozen archive size cap exceeded')
            if len(games) == plan['games']:
                cohort = dict(sealed_at=now(), cutoff=plan['cutoff'], publication_commit=args.publication_commit,
                              plan_sha256=sha(OUT / 'plan.json'), games=games, exclusions=decisions,
                              collection_tick=ticks-1, source_archive=str(archive),
                              no_models_or_predictions_opened=True)
                write(OUT / 'cohort.json', cohort, exclusive=True)
                write(archive / 'cohort.json', cohort, exclusive=True)
                state.update(status='complete', phase='sealed', cohort_sha256=sha(OUT / 'cohort.json'))
                return
            # Poll no faster than20min. Sleep in short intervals so the wall
            # alarm remains responsive; the tool handle, not this loop, is monitored.
            until = time.monotonic() + plan['poll_seconds']
            while time.monotonic() < until:
                time.sleep(max(0, min(30, until-time.monotonic())))
        state.update(status='insufficient_data', phase='closed without scoring')
    except BaseException as exc:
        state.update(status='failed', phase='closed without scoring', error=repr(exc))
        raise
    finally:
        signal.alarm(0)
        state.update(ended_at=now(), requests=client.requests_made, ticks=ticks)
        record_terminal(state, archive)


if __name__ == '__main__':
    main()
