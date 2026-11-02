"""One public version-list read plus immutable v37 archive/source checks."""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT))
from learning.api_client import ApiClient


def sha(data): return hashlib.sha256(data).hexdigest()


def main():
    archive = ROOT / 'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'
    expected = '41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c'
    assert sha(archive.read_bytes()) == expected
    engine = ROOT.parent / 'fowsearch-c'
    commit = subprocess.check_output(['git', '-C', str(engine), 'rev-parse', 'f76a09e^{commit}'], text=True).strip()
    sources = {}
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name in sorted(z.namelist()):
            if name.startswith('src/') and name.endswith(('.c', '.h')):
                data = z.read(name)
                original = subprocess.check_output(['git', '-C', str(engine), 'show', commit + ':' + name])
                assert data == original, name
                sources[name] = sha(data)
        assets = {name: sha(z.read(name)) for name in ('run.sh', 'build.sh', 'bin/stockfish', 'data/history.bin')}
    assert sources
    client = ApiClient(min_interval=1.2, timeout=30)
    payload, fetched = client.get_bytes('/api/leaderboard/a2c35173659545c99752376a70418438/versions')
    public = json.loads(payload)
    with (OUT / 'versions-response.json').open('xb') as f: f.write(payload)
    with (OUT / 'fetch.json').open('x') as f: json.dump(asdict(fetched), f, indent=2); f.write('\n')
    row = next(r for r in public['versions'] if r['version'] == 37)
    result = dict(at=datetime.now(timezone.utc).isoformat(), arena_version=37,
                  public_version_record=row, public_response_sha256=sha(payload),
                  archive=str(archive.relative_to(ROOT)), archive_sha256=expected,
                  source_commit=commit, archive_sources_match_commit=sources, assets=assets,
                  archive_association='Fable release note chatroom/192-fable-v37-allgames-refit.md identifies this archive as v37. Public API independently verifies version metadata, not uploaded file bytes.',
                  timestamp_semantics='createdAt is the API submission creation time, not an independently verified activation time.',
                  source_note_sha256=sha((ROOT / 'chatroom/192-fable-v37-allgames-refit.md').read_bytes()),
                  collector_sha256=sha(Path(__file__).read_bytes()), requests=client.requests_made)
    with (OUT / 'mapping.json').open('x') as f: json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps(dict(public_record=row, archive_sha256=expected, matching_source_files=len(sources), commit=commit, requests=client.requests_made)))


if __name__ == '__main__':
    main()
