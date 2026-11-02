"""Isolated Stockfish 19 all-child prototype; never edits the playing source."""
from datetime import datetime, timezone
import difflib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/sf-allchildren-20261102'
LOCAL = Path('/home/henrytan/fable-persist/scratchpad/misty/sf/stockfish')
RELEASE = ROOT / 'astra-submissions/experiments/queen-terminal-backport-20261102/build-r2/base/bin/stockfish'
URL = 'https://codeload.github.com/official-stockfish/Stockfish/tar.gz/refs/tags/sf_19'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p, x):
    with Path(p).open('x') as f: json.dump(x, f, indent=2); f.write('\n')
def replace(s, old, new):
    assert s.count(old) == 1, (old[:120], s.count(old))
    return s.replace(old, new)

def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    build = HERE / 'build'; build.mkdir(exist_ok=True)
    assert not (OUT / 'provenance.json').exists() and not (build / 'candidate').exists()
    assert sha(RELEASE) == sha(LOCAL / 'stockfish-linux-x86-64-universal')
    if (build / 'upstream.tar.gz').exists(): archive = (build / 'upstream.tar.gz').read_bytes()
    else:
        with urllib.request.urlopen(URL, timeout=60) as response: archive = response.read()
        (build / 'upstream.tar.gz').write_bytes(archive)
    pins = {}; differences = []
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as t:
        for member in t.getmembers():
            if not member.isfile(): continue
            rel = Path(*Path(member.name).parts[1:])
            if rel.parts[0] not in ('src', 'scripts') and str(rel) not in ('Copying.txt', 'AUTHORS'): continue
            assert '..' not in rel.parts and not rel.is_absolute()
            data = t.extractfile(member).read()
            original = LOCAL / rel
            if not original.is_file() or original.read_bytes() != data: differences.append(str(rel))
            target = build / 'base' / rel; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data); target.chmod(member.mode & 0o777)
            pins[str(rel)] = hashlib.sha256(data).hexdigest()
    # Release source may have generated build metadata; every upstream source
    # file we compile must nevertheless match the local release distribution.
    assert differences in ([], ['scripts/.gitattributes']), differences
    shutil.copytree(build / 'base', build / 'candidate')
    src = build / 'candidate/src'; p = src / 'search.h'; old = p.read_text()
    new = replace(old, '    usize              pvIdx, pvLast;',
                  '    bool astraAllChildren = false;  // experimental, depth-1 full MultiPV only\n    usize              pvIdx, pvLast;')
    p.write_text(new); patch = ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), 'a/src/search.h', 'b/src/search.h'))
    p = src / 'search.cpp'; old = p.read_text(); new = old
    new = replace(new, '    multiPV = std::min(multiPV, rootMoves.size());', '''    multiPV = std::min(multiPV, rootMoves.size());

    // Astra experiment 256: evaluate every legal root child with a full PV
    // window in a single root pass. All deeper search machinery is unchanged.
    // This is a different approximation, not bit-exact MultiPV acceleration.
    const char* allChildren = std::getenv("ASTRA_SF_ALLCHILDREN");
    astraAllChildren = allChildren && std::string(allChildren) == "1"
                    && limits.depth == 1 && int(options["Threads"]) == 1
                    && !skill.enabled() && !tbConfig.rootInTB
                    && multiPV == rootMoves.size();''')
    new = replace(new, '            // Adjust optimism based on root move\'s averageScore', '''            if (astraAllChildren)
            {
                alpha = -VALUE_INFINITE;
                beta  = VALUE_INFINITE;
                pvLast = rootMoves.size();
            }

            // Adjust optimism based on root move's averageScore''')
    new = replace(new, '            if (threads.stop && pvIdx)\n', '''            if (astraAllChildren)
            {
                if (mainThread && !threads.stop)
                {
                    main_manager()->output_pv(*this, threads, tt, rootDepth);
                    uciPvSent = true;
                }
                break;
            }

            if (threads.stop && pvIdx)
''')
    new = replace(new, '        else if (!PvNode || moveCount > 1)',
                  '        else if ((!PvNode || moveCount > 1) && !(rootNode && astraAllChildren))')
    new = replace(new, '        if (PvNode && (moveCount == 1 || value > alpha))',
                  '        if (PvNode && (moveCount == 1 || value > alpha || (rootNode && astraAllChildren)))')
    new = replace(new, '                alpha = value;  // Update alpha! Always alpha < beta',
                  '                if (!(rootNode && astraAllChildren))\n                    alpha = value;  // Keep a full window for every experimental root child')
    p.write_text(new); patch += ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), 'a/src/search.cpp', 'b/src/search.cpp'))
    (HERE / 'stockfish19-allchildren.patch').write_text(patch)
    network = build / 'base/src/nn-1a298aa575a0.nnue'
    r = subprocess.run([str(RELEASE)], input=f'export_net {network}\nquit\n', text=True, capture_output=True, timeout=30)
    assert r.returncode == 0 and network.is_file(), r.stdout + r.stderr
    assert sha(network).startswith('1a298aa575a0')
    shutil.copyfile(network, src / network.name)
    write(OUT / 'provenance.json', dict(at=datetime.now(timezone.utc).isoformat(), url=URL,
          archive_sha256=hashlib.sha256(archive).hexdigest(), upstream_files=pins,
          all_compiled_sources_match_local_release=True, release_metadata_differences=differences,
          release_binary=str(RELEASE),
          release_sha256=sha(RELEASE), network_sha256=sha(network),
          patch_sha256=sha(HERE / 'stockfish19-allchildren.patch'), export_stdout=r.stdout,
          source_scope='Official Stockfish only; no Misty implementation read. GPL-3.0-or-later preserved.'))
    print(json.dumps(dict(prepared=True, upstream_files=len(pins), network_bytes=network.stat().st_size)), flush=True)

def compile_all():
    os.sched_setaffinity(0, {0, 1})
    records = []
    for name in ('base', 'candidate'):
        src = HERE / 'build' / name / 'src'
        args = ['make', '-j2', 'build', 'ARCH=x86-64-avx2', 'COMP=gcc']
        with (OUT / (name + '-build.log')).open('x') as f:
            r = subprocess.run(args, cwd=src, stdout=f, stderr=subprocess.STDOUT, timeout=300)
        assert r.returncode == 0, (name, r.returncode)
        records.append(dict(arm=name, args=args, binary_sha256=sha(src / 'stockfish')))
        print(json.dumps(records[-1]), flush=True)
    write(OUT / 'build.json', dict(records=records, compiler=subprocess.check_output(['g++', '--version'], text=True),
          provenance_sha256=sha(OUT / 'provenance.json'), same_compile_flags=True, release_is_universal_pgo=True,
          limitation='Rebuilt AVX2 non-PGO controls isolate algorithm; shipped universal PGO binary is a separate comparator.'))

if __name__ == '__main__':
    import sys
    {'prepare': prepare, 'compile': compile_all}[sys.argv[1]]()
