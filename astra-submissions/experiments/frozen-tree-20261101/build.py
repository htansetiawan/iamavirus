#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARCHIVE = ROOT / 'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'
EXPECTED = '41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def replace(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new)


def main():
    assert sha(ARCHIVE) == EXPECTED
    build = HERE / 'build'; build.mkdir(exist_ok=True)
    with zipfile.ZipFile(ARCHIVE) as z:
        z.extractall(build)
    source = (build / 'src/gtcfr.c').read_text()
    source = replace(source, 'int gtcfr_decide(', '#include "audit.h"\n\nint gtcfr_decide(')
    source = replace(source, '    game_finalize(&t.g);', '    game_finalize(&t.g);\n    AuditInitial *astra_initial = audit_initial(&t.g, ours.count);')
    anchor = '    free(x); free(idx); free(share); free(chance_kids); free(chance_p);'
    source = replace(source, anchor, '    audit_final(&t,b,idx,share,K,root_I,&ours,out,params,astra_initial,iteration);\n' + anchor)
    (build / 'src/gtcfr.c').write_text(source)
    shutil.copyfile(HERE / 'src/audit.h', build / 'src/audit.h')
    result = subprocess.run(['bash', 'build.sh'], cwd=build, capture_output=True, text=True, timeout=60)
    (HERE / 'build.log').write_text(result.stdout + result.stderr); result.check_returncode()
    (build / 'bin/stockfish').chmod(0o755)
    provenance = {'archive': str(ARCHIVE.relative_to(ROOT)), 'archive_sha256': EXPECTED,
                  'binary_sha256': sha(build / 'mist'), 'modified_gtcfr_sha256': sha(build / 'src/gtcfr.c'),
                  'audit_sha256': sha(HERE / 'src/audit.h'), 'builder_sha256': sha(Path(__file__)),
                  'status': 'offline diagnostics after original move choice; not a candidate',
                  'build_stdout': result.stdout, 'build_stderr': result.stderr}
    (HERE / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps(provenance, indent=2))


if __name__ == '__main__':
    main()
