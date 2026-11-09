"""Publish the four successful staged reports with explicit feed timestamps."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'astra-submissions/analysis/report-order-20261109'
STAGE = OUT/'reports'
TARGET = ROOT/'data/reports/daily'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipt = json.loads((OUT/'refresh-receipt.json').read_text())
    assert receipt['passed'] and len(receipt['steps']) == 4
    assert all(r['exit_code'] == 0 and not r['timed_out'] for r in receipt['steps'])
    for name, digest in receipt['staged_files'].items():
        assert sha(STAGE/name) == digest, name
    intel = json.loads((STAGE/'intel-latest.json').read_text())
    assert intel['active_version_from_snapshot'] == 38 and intel['corpus_games'] > 200000
    coverage = intel['corpus_coverage']
    note = (f"> Recovery after the November 9 service timeout. Local own-game feed through "
            f"{coverage['latest']['ours']}; other-team feed through {coverage['latest']['other_only']}; "
            f"leaderboard snapshot {intel['leaderboard_fetched_at']}. "
            "Rolling archive views; API completeness is not established. "
            "Taxonomy changes compare the November 2 reference. "
            "A separate move export is running; no playing model was refitted.\n\n")
    names = ['2026-11-09.md', '2026-11-09.json', 'latest.md',
             'insights-2026-11-09.md', 'insights-latest.md',
             'scorecard-2026-11-09.md', 'scorecard-2026-11-09.json', 'scorecard-latest.md',
             'intel-2026-11-09.md', 'intel-2026-11-09.json', 'intel-latest.md', 'intel-latest.json']
    assert all((STAGE/name).stat().st_size > 0 for name in names)
    if (TARGET/'intel-latest.json').exists():
        prior = json.loads((TARGET/'intel-latest.json').read_text())
        assert prior['generated'] <= intel['generated'], 'preserve a newer report'
    records = {}
    for name in names:
        payload = (STAGE/name).read_bytes()
        if name.endswith('.md'):
            heading, body = payload.decode().split('\n', 1)
            payload = (heading+'\n\n'+note+body.lstrip('\n')).encode()
        with tempfile.NamedTemporaryFile(dir=TARGET, prefix='.astra-report-', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, TARGET/name)
        assert (TARGET/name).read_bytes() == payload
        records[str((TARGET/name).relative_to(ROOT))] = dict(staged_sha256=sha(STAGE/name),
              published_sha256=sha(TARGET/name), bytes=len(payload), coverage_note_added=name.endswith('.md'))
    with (OUT/'publication.json').open('x') as handle:
        json.dump(dict(at=datetime.now(timezone.utc).isoformat(), published=True,
                       steps_passed=True, coverage=coverage, files=records,
                       source_receipt_sha256=sha(OUT/'refresh-receipt.json'),
                       publisher_sha256=sha(Path(__file__)),
                       limitation='Source bodies preserved; Markdown adds feed timestamps. '
                       'No previous comparison JSON is copied over; no ingest or model update.'), handle, indent=2)
        handle.write('\n')
    print(json.dumps(dict(published=True, files=list(records), coverage=coverage)), flush=True)


if __name__ == '__main__':
    main()
