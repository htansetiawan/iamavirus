#!/usr/bin/env python3
"""Read-only checks behind Astra's review; writes only its explicit JSON output."""
import argparse
import ast
import bisect
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[3]
    snapshot = Path(__file__).parent / 'arena/snapshots/20261026T040940Z'
    archive = root / 'fable-submissions/iamavirus-v35-mist-c-v14.zip'
    result = {'kind': 'source and reporting audit; no strength experiment',
              'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}
    with zipfile.ZipFile(archive) as z:
        sources = {f: z.read(f) for f in z.namelist() if f.startswith('src/')}
        result['release_source_matches_97b60f1'] = {
            f: sources[f] == subprocess.check_output([
                'git', '-C', str(root.parent / 'fowsearch-c'), 'show', '97b60f1:' + f])
            for f in ['src/main.c', 'src/belief.c', 'src/gtcfr.c', 'src/eval.c']}
        combined = b'\n'.join(sources.values())
        result['knob_present_in_v35_sources'] = {
            knob: knob.encode() in combined for knob in [
                'MIST_FOG_HAZARD', 'MIST_KING_MOVE_HAZARD', 'MIST_HAZARD',
                'MIST_GUARD_UNIFORM', 'MIST_MATERIAL_GUARD']}
        result['board_history_merge_source'] = sources['src/belief.c'].decode().splitlines()[55:60]

    ps = sorted((root / 'data/raw/snapshots').glob('*/leaderboard.json'))[-600:]
    raw_keys = [p.parent.name[:16] for p in ps]
    # Mirrors daily_insights.rating_at's string ordering for the three teams
    # present at every example endpoint. Normalized comparison uses UTC instants.
    parsed = [(dt.datetime.strptime(p.parent.name[:17], '%Y-%m-%dT%H%M%S')
               .replace(tzinfo=dt.timezone.utc), p) for p in ps]
    times = [t for t, _ in parsed]
    cases = []
    for stamp in ['2026-10-18T12:00:00+00:00', '2026-10-21T12:00:00+00:00',
                  '2026-10-24T12:00:00+00:00']:
        t = dt.datetime.fromisoformat(stamp)
        key = t.strftime('%Y%m%dT%H%M')
        old_i = min(max(bisect.bisect_left(raw_keys, key) - 1, 0), len(ps) - 1)
        new_i = bisect.bisect_left(times, t) - 1
        cases.append({'game_timestamp_example': stamp, 'query_key': key,
                      'existing_lookup_snapshot': ps[old_i].parent.name,
                      'prior_snapshot_by_utc': parsed[new_i][1].parent.name if new_i >= 0 else None})
    result['timestamp_lookup_reproductions'] = cases
    source = root / 'learning/daily_insights.py'
    result['daily_insights_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    for node in ast.parse(source.read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'TOP6' for t in node.targets):
            result['report_fixed_top6'] = ast.literal_eval(node.value)

    lb = json.loads((snapshot / 'leaderboard.json').read_text())
    ranked = sorted((p for p in lb['players'] if p.get('rating') is not None), key=lambda p: -p['rating'])
    result['snapshot_utc'] = '2026-10-26T04:09:40Z'
    result['snapshot_boston'] = '2026-10-26 00:09 EDT'
    result['leaders'] = [{'rank': i + 1, 'name': p['name'], 'elo': p['rating'],
                          'active_version': p['activeVersion']} for i, p in enumerate(ranked[:10])]
    games = json.loads((snapshot / 'games.json').read_text())
    if isinstance(games, dict):
        games = games['games']
    grouped = collections.defaultdict(lambda: [0, 0, 0])
    for g in games:
        white = g['whitePlayerId'] == 'a2c35173659545c99752376a70418438'
        opponent = 'black' if white else 'white'
        i = 1 if g['result'] == '1/2-1/2' else 0 if (g['result'] == '1-0') == white else 2
        grouped[(g[opponent], g[opponent + 'Version'])][i] += 1
    result['latest100_wdl'] = [{'opponent': n, 'version': v, 'wins': w, 'draws': d, 'losses': l}
                               for (n, v), (w, d, l) in sorted(grouped.items())]
    Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'output': args.output, 'source_matches': result['release_source_matches_97b60f1'],
                      'timestamp_cases': len(cases), 'games': len(games)}, indent=2))


if __name__ == '__main__':
    main()
