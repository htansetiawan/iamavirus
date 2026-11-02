#!/usr/bin/env python3
"""Track daily intelligence freshness separately from deployed learning artifacts.

Reads existing data only; never fits weights, rewrites the frozen regression
suite, changes the history table, or promotes an arena submission.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning.daily_report import accepted_rows, our_score, opponent, versions  # noqa: E402


def artifact(path: Path, hash_contents=False) -> dict:
    result = {'path': str(path)}
    try:
        stat = path.stat()
        result.update(exists=True, bytes=stat.st_size,
                      modified_at=dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc).isoformat())
        if hash_contents:
            with path.open('rb') as handle:
                result['sha256'] = hashlib.file_digest(handle, 'sha256').hexdigest()
    except OSError as exc:
        result.update(exists=False, error=str(exc))
    return result


def latest_report(out: Path) -> dict:
    for path in sorted(out.glob('????-??-??.json'), reverse=True):
        try:
            value = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if isinstance(value, dict) and 'taxonomy' in value:
            return dict(value, report_path=str(path))
    return {}


def rolling_losses(rows, since: str, per_group=3) -> list[dict]:
    """Bounded fresh loss index; not a validated decision suite or a training set."""
    count = Counter(); selected = []
    for row in sorted(rows, key=lambda r: (r.get('createdAt') or '', r['id']), reverse=True):
        if (row.get('createdAt') or '') < since or 'IAmAVirus' not in (row['white'], row['black']):
            continue
        if our_score(row) != 0:
            continue
        own, other = versions(row); side = 'white' if row['white'] == 'IAmAVirus' else 'black'
        key = (opponent(row), other, own, side)
        if count[key] >= per_group:
            continue
        count[key] += 1
        selected.append({'id': row['id'], 'created_at': row['createdAt'], 'opponent': key[0],
                         'opponent_version': other, 'our_version': own, 'side': side,
                         'plies': row.get('plies'), 'reason': row.get('reason'),
                         'arena_url': f"https://www.mit.edu/~6.7980/fow/?tab=arena&game={row['id']}"})
    return selected


def reference_archive(path: Path, arena_version: int) -> dict:
    report = {'arena_version': arena_version, **artifact(path, True)}
    if not report['exists']:
        return report
    try:
        with zipfile.ZipFile(path) as archive:
            model_path = ('src/movemodel_theta.h' if 'src/movemodel_theta.h' in archive.namelist()
                          else 'src/movemodel.c')
            model = archive.read(model_path)
            report['model'] = {'member': model_path, 'sha256': hashlib.sha256(model).hexdigest()}
            table = archive.read('data/history.bin')
            magic, version, count = struct.unpack('<8sII', table[:16])
            if magic != b'MISTHIST' or version != 1 or len(table) != 16 + 16 * count:
                raise ValueError('unrecognised history-table format')
            report['history'] = {'records': count, 'sha256': hashlib.sha256(table).hexdigest()}
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, struct.error) as exc:
        report['error'] = str(exc)
    return report


def mapped_active_archive(registry: Path, arena_version: int | None) -> dict:
    """Resolve the arena column, not a ZIP's potentially historical vN label.

    This verifies a local file against the shared release map. The public API
    supplies the active version, but does not expose the uploaded ZIP checksum.
    Unknown or ambiguous mappings stay unknown instead of falling back to v35.
    """
    report = {'arena_version': arena_version, 'registry': str(registry),
              'mapping_verified': False,
              'provenance': 'Repository release map; uploaded bytes are not API-verifiable.'}
    try:
        if not isinstance(arena_version, int) or isinstance(arena_version, bool):
            raise ValueError('active arena version unavailable')
        rows = []
        for line in registry.read_text().splitlines():
            if not line.startswith('|'):
                continue
            cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
            if cells and cells[0].strip('*` ') == str(arena_version):
                rows.append(cells)
        if len(rows) != 1 or len(rows[0]) < 4:
            raise ValueError(f'expected one release-map row for v{arena_version}; found {len(rows)}')
        cells = rows[0]
        names = re.findall(r'`([^`]+\.zip)`', cells[2])
        hashes = re.findall(r'`([0-9a-f]{12,64})`', cells[3])
        if not names or len(hashes) != 1:
            raise ValueError('release-map row lacks an archive name or SHA-256 prefix')
        # The first archive in the cell is canonical; later names may be aliases.
        path = (registry.parent / names[0]).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError('mapped archive is outside the project')
        archived = reference_archive(path, arena_version)
        report.update(archived, expected_sha256_prefix=hashes[0])
        if not archived.get('exists') or archived.get('error'):
            raise ValueError(archived.get('error', 'mapped archive missing'))
        if not archived['sha256'].startswith(hashes[0]):
            raise ValueError('mapped archive SHA-256 does not match the release-map prefix')
        report['mapping_verified'] = True
    except (OSError, ValueError) as exc:
        report['error'] = str(exc)
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--raw', type=Path, default=ROOT/'data/raw')
    ap.add_argument('--out', type=Path, default=ROOT/'data/reports/daily')
    ap.add_argument('--engine', type=Path, default=Path.home()/'git/fowsearch-c')
    ap.add_argument('--suite', type=Path, default=Path.home()/'fable-persist/suite/suite.json')
    ap.add_argument('--reference-archive', type=Path, default=ROOT/'fable-submissions/iamavirus-v35-mist-c-v14.zip')
    ap.add_argument('--reference-version', type=int, default=35)
    ap.add_argument('--registry', type=Path, default=ROOT/'fable-submissions/README.md')
    args = ap.parse_args(); now = dt.datetime.now(dt.timezone.utc); day = now.strftime('%Y-%m-%d')
    report = latest_report(args.out)
    rows = accepted_rows(str(args.raw))
    manifest_path = ROOT/'data/manifests/arena-latest.json'
    datasets = artifact(manifest_path)
    if datasets['exists']:
        try:
            data = json.loads(manifest_path.read_text())
            datasets.update(created_at=data.get('created_at'), counts=data.get('counts'),
                            content_sha256=data.get('content_sha256'))
        except (OSError, ValueError) as exc:
            datasets['error'] = str(exc)
    model = artifact(args.engine/'src/movemodel_theta.h', True)
    if model['exists']:
        text = (args.engine/'src/movemodel_theta.h').read_text()
        match = re.search(r'Fitted (\d{4}-\d{2}-\d{2}) on ([\d,]+) arena games', text)
        if match:
            model.update(declared_fit_date=match[1], declared_fit_games=int(match[2].replace(',', '')))
    suite = artifact(args.suite, True)
    if suite['exists']:
        try:
            data = json.loads(args.suite.read_text())
            suite['decisions'] = len(data) if isinstance(data, list) else None
        except (OSError, ValueError) as exc:
            suite['error'] = str(exc)
    archived = reference_archive(args.reference_archive, args.reference_version)
    active = report.get('our_active_version')
    active_archive = mapped_active_archive(args.registry, active)
    # A stale reference must not be silently labelled as the newly active bot.
    archived['matches_active_version_in_report'] = active == args.reference_version
    failures = rolling_losses(rows, (now-dt.timedelta(days=7)).isoformat())
    status = {'generated': now.isoformat(), 'active_version_from_snapshot': active,
              'source_report': report.get('report_path'), 'source_report_generated': report.get('generated'),
              'leaderboard_fetched_at': report.get('leaderboard_fetched_at'),
              'corpus_games': len(rows), 'latest_game_at': max((r.get('createdAt') or '' for r in rows), default=None),
              'taxonomy_previous_report': report.get('previous_report_generated'),
              'taxonomy_version_colour_groups': len(report.get('taxonomy_by_version_colour', [])),
              'dataset': datasets,
              'move_exports': [artifact(ROOT/f'data/derived/moves/arena-latest-{s}.txt') for s in ('train', 'test')],
              'working_model': model, 'reference_archive': archived, 'active_archive': active_archive,
              'frozen_regression_suite': suite,
              'rolling_loss_index': failures,
              'policy': {'automatic': ['replays', 'training exports', 'taxonomy', 'insights', 'scorecard', 'intel status and loss index'],
                         'candidate_only': ['fit model', 'rebuild history table', 'build regression supplement'],
                         'promotion': 'Requires measured validation and an explicit versioned release; the report never changes deployed weights.'}}
    md = [f'# Learning and intelligence status, {now:%Y-%m-%d %H:%M UTC}', '',
          f"Corpus: **{len(rows):,} games**. Latest game: {status['latest_game_at']}. "
          f"Leaderboard snapshot: {status['leaderboard_fetched_at']}.", '',
          '| Feed | Latest evidence | How it reaches the bot |', '|---|---|---|',
          f"| Replay and training data | Manifest modified {datasets.get('modified_at', 'unavailable')}; move-export metadata in JSON | Training input; no automatic promotion |",
          f"| Taxonomy | {status['taxonomy_version_colour_groups']} played-version/colour groups; previous report {status['taxonomy_previous_report']} | Diagnosis and case selection; not an input to the live policy or belief |",
          f"| Working move model | Declared fit {model.get('declared_fit_date', 'unknown')}, {model.get('declared_fit_games', 'unknown')} games | Candidate probabilities; requires validation and packaging |",
          f"| Active archive's history table | Snapshot v{active}; "
          + (f"{active_archive['history']['records']:,} records; release-map hash checked" if active_archive['mapping_verified']
             else f"mapping unresolved: {active_archive.get('error', 'unknown')}")
          + ' | Packaged model/table; changes require a new submission |',
          f"| Reference history table | Archive v{args.reference_version}, {archived.get('history', {}).get('records', 'unknown')} records | Fixed table packaged inside that archive; not updated by replay ingest |",
          f"| Frozen regression suite | {suite.get('decisions', 'unknown')} decisions; file modified {suite.get('modified_at', 'unknown')} | Fixed comparison set; retain it across experiments |",
          f"| Rolling loss index | {len(failures)} recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |", '',
          '## Reference versus active version', '',
          f"Snapshot active version: **{active}**. Reference archive: **v{args.reference_version}**. "
          + ('Versions match; hashes are recorded in the JSON.' if archived['matches_active_version_in_report']
             else 'The reference is retained for comparison; it is not the active deployment.'), '',
          (f"Active archive: `{Path(active_archive['path']).name}`, SHA-256 `{active_archive['sha256']}`. "
           'Its hash matches the shared release map; model-member and history-table hashes are in the JSON. '
           'The public API identifies the active version but cannot verify uploaded ZIP bytes.'
           if active_archive['mapping_verified'] else
           f"**Mapping update required:** {active_archive.get('error', 'active archive unavailable')}."), '',
          'File modification dates are filesystem freshness, not proof of retraining or dataset coverage. '
          'The working model is not necessarily the model in the active archive. '
          'Rebuilding inputs does not change the submitted ZIP.', '',
          '## From taxonomy to a measured change', '',
          'Select a behaviour by played version and colour, inspect actual replay cases, and measure '
          'predicted versus observed risk. Fit a correction using training games, check it on held-out '
          'games and the frozen suite plus fresh cases, then test full games. '
          'A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. '
          'Taxonomy ranks describe behaviour and can reflect the opponent mix.', '',
          '## Recent loss examples', '',
          'The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.', '']
    for item in failures[:20]:
        md.append(f"- [{item['id']}]({item['arena_url']}): our v{item['our_version']} as {item['side']} "
                  f"vs {item['opponent']} v{item['opponent_version']}, {item['plies']} plies, {item['reason']}.")
    args.out.mkdir(parents=True, exist_ok=True)
    for suffix, text in (('md', '\n'.join(md)+'\n'), ('json', json.dumps(status, indent=2)+'\n')):
        for name in (f'intel-{day}.{suffix}', f'intel-latest.{suffix}'):
            (args.out/name).write_text(text)
    print(args.out/f'intel-{day}.md')


if __name__ == '__main__':
    main()
