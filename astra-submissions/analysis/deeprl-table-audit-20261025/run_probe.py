"""Build a read-only probe against pinned archived solver sources, in a temp dir."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARCHIVE = ROOT / 'fable-submissions/iamavirus-v35-mist-c-v14.zip'
EXPECTED = '24791ca64a429f5ae931466ce3c1af36c6974e1295203e99a00a991976955b4c'

if __name__ == '__main__':
    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    if digest != EXPECTED:
        raise SystemExit('Archive differs from audited v35; inspect before running')
    with tempfile.TemporaryDirectory(prefix='astra-cfr-probe-') as directory:
        tmp = Path(directory)
        with zipfile.ZipFile(ARCHIVE) as z:
            for name in ('cfr.c', 'cfr.h'):
                (tmp/name).write_bytes(z.read('src/'+name))
        # Keep upstream source unchanged; apply strict warnings to our additions.
        subprocess.run(['cc', '-std=c11', '-O2', '-c', str(tmp/'cfr.c'),
                        '-o', str(tmp/'cfr.o')], check=True)
        subprocess.run(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                        '-I'+str(tmp), '-I'+str(HERE), str(tmp/'cfr.o'),
                        str(HERE/'teacher_targets.c'), str(HERE/'probe.c'),
                        '-lm', '-o', str(tmp/'probe')], check=True)
        result = json.loads(subprocess.check_output([str(tmp/'probe')], text=True))
    result['archive_sha256'] = digest
    result['scope'] = 'analytic target correctness; no playing-strength measurement'
    print(json.dumps(result, indent=2))
