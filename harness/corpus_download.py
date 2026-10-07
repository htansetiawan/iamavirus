#!/usr/bin/env python3
"""Download a corpus of real arena games from the public API.

Why this exists: local self-play cannot measure the failures that actually cost
rated games. Three changes today measured +33, -47 and +51 Elo, all at about one
sigma, because a bot playing itself is insensitive to a weakness both sides share.
The arena's public replays give thousands of real positions, played by opponents
several hundred Elo stronger, which is a far better test bench than more self-play.

Only the move list is kept. Observations are not stored, because the engine can
render them itself -- that renderer agrees with referee.py on 47,875 checks -- and
replaying the moves also recovers castling rights and en passant state, which a
board diagram alone does not carry.

The API rate-limits, so requests are spaced and 503s are retried with backoff.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://6s890.lids.mit.edu'
AGENT = 'iamavirus-corpus/1.0 (MIT 6.7980 student bot; contact via arena)'


def fetch(path, params=None, attempts=5):
    url = f'{BASE}{path}'
    if params:
        url += '?' + urllib.parse.urlencode(params)
    delay = 2.0
    for attempt in range(attempts):
        request = urllib.request.Request(url, headers={'User-Agent': AGENT})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as error:
            if error.code in (429, 503, 502, 504) and attempt + 1 < attempts:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt + 1 < attempts:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    raise RuntimeError(f'gave up on {url}')


def list_games(team, outcome, limit, pause):
    """Collect game summaries for a team, following cursors."""
    collected, cursor = [], None
    while len(collected) < limit:
        params = {'white': team, 'colors': 'any', 'sort': 'played',
                  'order': 'desc', 'limit': min(100, limit - len(collected))}
        if outcome:
            params['outcome'] = outcome
        if cursor:
            params['cursor'] = cursor
        page = fetch('/api/games', params)
        games = page.get('games') or []
        if not games:
            break
        collected += games
        cursor = page.get('nextCursor')
        if not cursor:
            break
        time.sleep(pause)
    return collected[:limit]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--team', required=True,
                        help='team name substring, e.g. "Greek Gift"')
    parser.add_argument('--outcome', default=None,
                        help='team-won, team-lost, decisive, ...')
    parser.add_argument('--limit', type=int, default=40)
    parser.add_argument('--pause', type=float, default=1.5,
                        help='seconds between requests; be polite')
    parser.add_argument('--out', required=True)
    parser.add_argument('--side', default='loser',
                        choices=['loser', 'winner', 'team', 'both'],
                        help='whose seat to emulate in the benchmark')
    args = parser.parse_args()

    summaries = list_games(args.team, args.outcome, args.limit, args.pause)
    print(f'{len(summaries)} games listed for {args.team!r}', file=sys.stderr)

    written = 0
    with open(args.out, 'w') as handle:
        for i, summary in enumerate(summaries):
            try:
                replay = fetch(f'/api/games/{summary["id"]}')
            except Exception as error:
                print(f'  skipped {summary["id"]}: {error}', file=sys.stderr)
                continue
            frames = replay.get('frames') or []
            moves = [f['move'] for f in frames if f.get('move')]
            if len(moves) < 4:
                continue
            result = replay['result']
            if result == '1-0':
                winner, loser = 'w', 'b'
            elif result == '0-1':
                winner, loser = 'b', 'w'
            else:
                winner = loser = None

            wanted = []
            if args.side == 'both' or args.side == 'team':
                team_side = 'w' if args.team.lower() in replay['white'].lower() else 'b'
                wanted = ['w', 'b'] if args.side == 'both' else [team_side]
            elif args.side == 'loser' and loser:
                wanted = [loser]
            elif args.side == 'winner' and winner:
                wanted = [winner]
            for side in wanted:
                opponent = replay['black'] if side == 'w' else replay['white']
                handle.write(f'{replay["id"]} {side} {result} '
                             f'{replay["reason"].replace(" ", "_")} '
                             f'{opponent.replace(" ", "_")} '
                             f'{" ".join(moves)}\n')
                written += 1
            print(f'  [{i+1}/{len(summaries)}] {summary["id"]} '
                  f'{replay["white"]} vs {replay["black"]} {result} '
                  f'{len(moves)} plies', file=sys.stderr)
            time.sleep(args.pause)
    print(f'wrote {written} seats to {args.out}', file=sys.stderr)


if __name__ == '__main__':
    main()
