"""Stage immutable release bytes; publish only after every recorded gate passes."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import zipfile

from prepare import HERE, ROOT, OLD, OUT, sha

ASTRA = ROOT / 'astra-submissions'
BASE = ROOT / 'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'
BASE_HASH = '41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c'
STAGED = HERE / 'build/v38-review.zip'
NAME = 'iamavirus-v38-mist-c-allchildren.zip'
spec = importlib.util.spec_from_file_location('astra_version_rule', ASTRA / 'tools/package_release.py')
version_rule = importlib.util.module_from_spec(spec)
spec.loader.exec_module(version_rule)

def write(p, value):
    with p.open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')

def stage():
    assert version_rule.next_version() == 38, 'Reconcile numbering with Fable before packaging'
    assert not (ASTRA / NAME).exists() and not (ASTRA / 'v38-manifest.json').exists()
    scorer = json.loads((OUT / 'scorer-validation.json').read_text())
    assert scorer['passed'] and scorer['state'] == 'completed'
    assert sha(BASE) == BASE_HASH
    source = json.loads((OUT / 'source.json').read_text())
    portable = HERE / 'build/stockfish/src/stockfish'
    assert sha(portable) == scorer['portable_sha256']
    with zipfile.ZipFile(BASE) as z:
        content = {n: z.read(n) for n in z.namelist() if not n.endswith('/')}
    original = {n: hashlib.sha256(b).hexdigest() for n, b in content.items()}
    run = content['run.sh'].decode()
    assert run.count('exec ./mist') == 1
    content['run.sh'] = run.replace('exec ./mist', 'export ASTRA_SF_ALLCHILDREN=1\nexec ./mist').encode()
    content['bin/stockfish'] = portable.read_bytes()
    for rel, h in source['source_files'].items():
        p = HERE / 'build/stockfish' / rel
        assert sha(p) == h, rel
        content['third_party/stockfish19/' + rel] = p.read_bytes()
    content['third_party/stockfish19/astra-allchildren.patch'] = (OLD / 'stockfish19-allchildren.patch').read_bytes()
    net_hash = source['network_sha256']
    content['third_party/stockfish19/rebuild.sh'] = f'''#!/bin/sh
set -eu
cd "$(dirname "$0")"
# The exact upstream network is embedded in the shipped binary. Exporting it
# avoids storing a duplicate 98 MB copy in the arena workspace.
net=src/nn-1a298aa575a0.nnue
if [ ! -f "$net" ]; then
    printf 'export_net %s/%s\\nquit\\n' "$PWD" "$net" | ../../bin/stockfish
fi
printf '%s  %s\\n' '{net_hash}' "$net" | sha256sum -c -
cd src
command -v hexdump >/dev/null
make -j"${{JOBS:-2}}" build ARCH=x86-64-universal COMP=gcc CXX="${{CXX:-g++-12}}"
strip stockfish
test "$(wc -c < stockfish)" -gt 98000000
# Result: third_party/stockfish19/src/stockfish; installed bot is untouched.
'''.encode()
    content['third_party/stockfish19/ASTRA-NOTICE.md'] = f'''# Modified Stockfish 19

Original: official-stockfish/Stockfish tag sf_19 (release commit edb0d9d).
Source archive SHA256: {source['source_archive_sha256']}.
Licence: GPL-3.0-or-later; see Copying.txt and AUTHORS.

Astra modified src/search.h and src/search.cpp on 2 November 2026. The patch
enables an opt-in, single full-window root pass for depth-1 full MultiPV,
one-thread searches. Disabled, deeper and restricted-MultiPV paths retain
upstream behavior. This is an approximation; see astra-allchildren.patch.
The already-patched complete source and upstream build scripts are included.

The unmodified NNUE is embedded in ../../bin/stockfish and can be exported
without network access by rebuild.sh. Network SHA256: {net_hash}.
Build used Ubuntu 22.04, g++ 12.3.0, non-PGO official x86-64-universal target
with static libstdc++/libgcc. Requires glibc no newer than 2.35. See the project
repository's astra-submissions/analysis/v38-package-20261108 for build receipts.

Rebuild (outside the timed arena startup): sh rebuild.sh. This invokes the
included Makefile and requires g++-12, make, binutils, gawk, Python 3 and
hexdump (bsdextrautils). Do not ignore an absent NNUE embedding helper.
'''.encode()
    content['ASTRA-RELEASE.md'] = b'''# Astra v38 candidate

Parent: exact Fable v37 mist-c v14 allfit archive. Native C source, learned
move model and empirical history table are unchanged. The only playing change
is the separate modified Stockfish 19 scorer and ASTRA_SF_ALLCHILDREN=1.

The approximation scores all legal children in one full-window root pass.
It retains tactical search/NNUE but changes pruning/history trajectories.
Earlier development gates show faster leaf scoring and more search nodes;
these do not establish arena Elo. Release evidence and the final gate receipt
are in the repository's v38-manifest.json and v38-release.md beside this ZIP.

Run build.sh, then run.sh. The arena compiles the native engine. Stockfish is
prebuilt with portable CPU dispatch; its modified source/licence and offline
rebuild recipe are under third_party/stockfish19/. No GPU or network required.

Repository publication is separate from a human arena upload. The archive
label is not evidence of an assigned arena version.
'''
    for n, h in original.items():
        if n not in ('run.sh', 'bin/stockfish'):
            assert hashlib.sha256(content[n]).hexdigest() == h
    manifest = dict(author='Astra', version=38, fable_version=37,
                    numbering_rule='highest Fable numbered archive major + 1; checked at staging and publication',
                    status='candidate awaiting final validation and opponent gate',
                    parent_archive=str(BASE.relative_to(ROOT)), parent_sha256=BASE_HASH,
                    parent_source_commit='f76a09e2f58b',
                    changed_playing_files=['run.sh', 'bin/stockfish'],
                    source_sha256={n: hashlib.sha256(b).hexdigest() for n, b in content.items()},
                    scorer_validation_sha256=sha(OUT / 'scorer-validation.json'),
                    experiment_scorer_sha256=scorer['measured_sha256'],
                    portable_scorer_sha256=scorer['portable_sha256'],
                    scope='Portable build has score/node/best-move parity on frozen panels; full-game experiments use laboratory bytes.')
    content['astra-release.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    with zipfile.ZipFile(STAGED, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(content.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 8, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if name.endswith('.sh') or name == 'bin/stockfish' else 0o644
            info.external_attr = (0o100000 | mode) << 16
            z.writestr(info, data, compresslevel=9)
    assert STAGED.stat().st_size < 100 * 1024 * 1024, 'GitHub single-file limit'
    assert sum(map(len, content.values())) < 768 * 1024 * 1024
    assert version_rule.next_version() == 38
    manifest.update(staged_archive=str(STAGED.relative_to(ROOT)), archive_sha256=sha(STAGED),
                    archive_bytes=STAGED.stat().st_size, files=len(content),
                    uncompressed_bytes=sum(map(len, content.values())))
    write(OUT / 'staged.json', manifest)
    print(json.dumps({k: manifest[k] for k in ('archive_sha256', 'archive_bytes', 'files')}), flush=True)

def publish():
    # This creates the immutable repository artifact; git publication is a
    # separate scoped operation with a second version recheck.
    assert version_rule.next_version() == 38
    opponent = ROOT / 'astra-submissions/analysis/sf-opponent-20261108/independent-review.json'
    gate = json.loads(opponent.read_text())
    assert gate['gate_pass'] and gate['completed'] == 32 and not gate['live_owned_processes']
    validation = json.loads((OUT / 'zip-validation.json').read_text())
    assert validation['passed']
    manifest = json.loads((OUT / 'staged.json').read_text())
    assert sha(STAGED) == validation['archive_sha256'] == manifest['archive_sha256']
    assert not (ASTRA / NAME).exists() and not (ASTRA / 'v38-manifest.json').exists()
    manifest.update(archive=NAME, status='validated repository release; not uploaded to arena',
                    published_at=datetime.now(timezone.utc).isoformat(),
                    opponent_gate_sha256=sha(opponent), zip_validation_sha256=sha(OUT / 'zip-validation.json'))
    os.link(STAGED, ASTRA / NAME)  # fails rather than replacing another release
    write(ASTRA / 'v38-manifest.json', manifest)
    print(json.dumps(dict(archive=NAME, sha256=sha(ASTRA / NAME), arena_uploaded=False)), flush=True)

if __name__ == '__main__':
    import sys
    {'stage': stage, 'publish': publish}[sys.argv[1]]()
