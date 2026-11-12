"""Explain the historical export gap from saved logs and host unit messages.

No daily service, exporter, training job, network or publication is started.
The prior 272/273 fixes are antecedents, not newly discovered changes.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
NAME = 'dataset-freshness-lineage-20261111'
OUT = ROOT / 'astra-submissions/analysis' / NAME
STORE = ROOT / 'data/astra-spool' / NAME


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')


def main():
    OUT.mkdir(exist_ok=False)
    STORE.mkdir(exist_ok=False)
    command = ['/usr/bin/journalctl', '--user', '-u', 'iamavirus-daily.service',
               '--since', '2026-11-02 00:00:00 UTC', '--until', '2026-11-11 08:55:00 UTC',
               '--no-pager', '-o', 'json', '--grep',
               'Starting|Finished|start operation timed out|Main process exited|Failed with result']
    output = subprocess.run(command, check=True, capture_output=True, timeout=30).stdout
    (STORE / 'service-journal.jsonl').write_bytes(output)
    events = []
    for line in output.splitlines():
        row = json.loads(line)
        events.append(dict(at=datetime.fromtimestamp(int(row['__REALTIME_TIMESTAMP']) / 1e6,
                                                     timezone.utc).isoformat(), message=row['MESSAGE']))
    assert events, 'host journal unavailable; do not infer timeouts from a truncated log alone'
    events.sort(key=lambda r: r['at'])
    properties = ['ActiveState', 'SubState', 'Result', 'ExecMainStatus', 'ExecMainStartTimestamp',
                  'ExecMainExitTimestamp', 'TimeoutStartUSec']
    status_command = ['/usr/bin/systemctl', '--user', 'show', 'iamavirus-daily.service']
    for prop in properties:
        status_command.extend(['-p', prop])
    status = subprocess.run(status_command, check=True, capture_output=True, timeout=30).stdout
    (STORE / 'service-status.txt').write_bytes(status)
    unit = dict(line.split('=', 1) for line in status.decode().splitlines())
    days, source_hashes = [], {}
    for path in sorted((ROOT / 'data/logs/daily').glob('2026-11-*.log')):
        date = path.stem
        if not '2026-11-02' <= date <= '2026-11-10':
            continue
        raw = path.read_bytes()
        copy = STORE / path.name
        copy.write_bytes(raw)
        assert sha(copy) == sha(path)
        source_hashes[str(path)] = sha(copy)
        markers, progress, io_errors = [], [], 0
        for n, line in enumerate(raw.decode('utf-8', 'replace').splitlines(), 1):
            match = re.match(r'== (\d\d:\d\d:\d\d) (.*)', line)
            if match:
                markers.append(dict(at=date + 'T' + match[1] + '+00:00', step=match[2], line=n))
            match = re.search(r'dataset: (\d+)/(\d+) source games processed', line)
            if match:
                progress.append(dict(processed=int(match[1]), total=int(match[2]), line=n))
            io_errors += int('Input/output error' in line)
        event_rows = [e for e in events if e['at'][:10] == date]
        timeout = next((e for e in event_rows if 'start operation timed out' in e['message']), None)
        dataset = next((m for m in markers if m['step'] == 'dataset manifest'), None)
        move = next((m for m in markers if m['step'] == 'mist-c move export'), None)
        def seconds(a, b):
            return (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds()
        days.append(dict(date=date, last_marker=markers[-1] if markers else None,
                         dataset_stage=dataset, move_stage=move,
                         move_seconds_before_dataset=seconds(move['at'], dataset['at']) if move and dataset else None,
                         service_timeout=timeout,
                         dataset_seconds_until_service_timeout=seconds(dataset['at'], timeout['at']) if dataset and timeout else None,
                         last_logged_dataset_progress=progress[-1] if progress else None,
                         io_error_lines=io_errors,
                         done_marker=any(m['step'] == 'done' for m in markers),
                         service_events=event_rows))
    for date in ('2026-11-03', '2026-11-04', '2026-11-05', '2026-11-09'):
        row = next(r for r in days if r['date'] == date)
        assert row['service_timeout'], date
    manifest_path = ROOT / 'data/manifests/arena-latest.json'
    manifest = json.loads(manifest_path.read_bytes())
    for path in (manifest_path, ROOT / 'tools/daily_refresh.sh', Path(__file__),
                 ROOT / 'chatroom/272-astra-daily-report-order.md',
                 ROOT / 'chatroom/273-astra-incremental-move-export.md',
                 ROOT / 'astra-submissions/analysis/training-artifact-readiness-20261111/result.json',
                 ROOT / 'astra-submissions/analysis/corpus-metadata-recovery-20261111/review.json'):
        source_hashes[str(path)] = sha(path)
    save(OUT / 'result.json', dict(at=datetime.now(timezone.utc).isoformat(), days=days,
         current_unit=unit, historical_journal_command=command, status_command=status_command,
         current_episode_manifest=dict(created_at=manifest['created_at'], source_games=manifest['source_games'],
                                       split_method=manifest['split_method'], undated_source_games=manifest['undated_source_games']),
         known_fixes=dict(report_order='cca63ed7', cached_move_export='a94110fd',
                         new_complete_run_after_storage_recovery_verified=False),
         source_sha256=source_hashes,
         saved_evidence_sha256={str(p): sha(p) for p in STORE.iterdir() if p.is_file()},
         scope='Historical failure attribution and presentation provenance. Existing 272/273 fixes are unchanged; no new pipeline repair, hardware certification, service action, export, split, fit, model, match, Git or deployment.'))
    print(json.dumps(dict(days=len(days), timeouts=[r['date'] for r in days if r['service_timeout']],
                          episode_manifest_created_at=manifest['created_at'], current_service=unit['ActiveState'])))


if __name__ == '__main__':
    main()
