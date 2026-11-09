"""One real-replay parity comparison with the unchanged private exporter."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT/'astra-submissions/analysis/move-cache-20261109'
BUILD = HERE/'build'
EXPORTER = ROOT/'astra-submissions/tools/export_move_cache.py'
REFERENCE = Path('/home/henrytan/git/fowsearch-c/tools/export_moves.py')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(path):
    rows = {}
    with path.open() as handle:
        while header := handle.readline():
            tag, gid, white, black = header.split()
            assert tag == 'game' and gid not in rows
            rows[gid] = (white, black, handle.readline().strip())
    return rows


def main():
    os.chdir(ROOT)
    os.sched_setaffinity(0, {6})
    os.nice(10)
    BUILD.mkdir(exist_ok=False)
    OUT.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('exporter', EXPORTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows, snapshot = module.journal_snapshot(ROOT/'data/raw/accepted.jsonl', lambda: None)
    eligible, _ = module.eligible_rows(rows, '2026-10-19')
    selected = sorted(eligible, key=lambda gid: hashlib.sha256(('273:'+gid).encode()).digest())[:128]
    raw = BUILD/'raw'
    raw.mkdir()
    sources = {}
    with (raw/'accepted.jsonl').open('x') as journal:
        for gid in selected:
            journal.write(json.dumps(eligible[gid])+'\n')
            folder = raw/'games'/gid
            folder.mkdir(parents=True)
            for name in ('replay.json', 'listing.json'):
                source = ROOT/'data/raw/games'/gid/name
                shutil.copy2(source, folder/name)
                sources[f'{gid}/{name}'] = digest(folder/name)
    reference = BUILD/'reference'
    reference.mkdir()
    old_prefix = reference/'moves'
    at = time.monotonic()
    process = subprocess.run([sys.executable, str(REFERENCE), str(raw/'games'), str(old_prefix),
                              '--games', '1000000', '--since', '2026-10-19'],
                             capture_output=True, text=True, timeout=60)
    old_elapsed = time.monotonic()-at
    assert process.returncode == 0, process.stderr
    command = [sys.executable, str(EXPORTER), '--raw', str(raw), '--cache', str(BUILD/'cache.sqlite'),
               '--out-prefix', str(BUILD/'new/moves'), '--since', '2026-10-19', '--legacy-links']
    results = []
    for iteration in range(2):
        if iteration:
            # Only our throwaway fixture is removed; real raw files are untouched.
            shutil.rmtree(raw/'games')
        run = subprocess.run(command, capture_output=True, text=True, timeout=60)
        assert run.returncode == 0, run.stderr
        result = json.loads(run.stdout)
        assert result['replay_reads'] == (128 if not iteration else 0)
        generation = Path(result['generation'])
        for split in ('train', 'test'):
            assert records(generation/f'{split}.txt') == records(Path(str(old_prefix)+f'-{split}.txt'))
        results.append(result)
    report = dict(at=datetime.now(timezone.utc).isoformat(), passed=True, games=len(selected),
                  selected_ids=selected, source_snapshot=snapshot, source_files=sources,
                  reference_sha256=digest(REFERENCE), exporter_sha256=digest(EXPORTER),
                  verifier_sha256=digest(Path(__file__)), reference_seconds=old_elapsed,
                  runs=results, limitation='128-game real-data parity and no-replay warm-cache contract; '
                  'local fixture timing is not an external-drive throughput or playing-strength claim.')
    with (OUT/'real-parity.json').open('x') as handle:
        json.dump(report, handle, indent=2)
        handle.write('\n')
    print(json.dumps({k: report[k] for k in ('passed', 'games', 'reference_seconds', 'runs')}), flush=True)


if __name__ == '__main__':
    main()
