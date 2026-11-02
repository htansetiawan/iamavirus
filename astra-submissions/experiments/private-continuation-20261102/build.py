"""Isolated v37 replay continuation; no policy/search/weight changes."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/private-continuation-20261102'
BASE = HERE.parent / 'queen-terminal-backport-20261102/build-r2/base'
ZIP = ROOT / 'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=True)
    build = HERE / 'build'
    build.mkdir(exist_ok=False)
    with zipfile.ZipFile(ZIP) as z:
        sources = [n for n in z.namelist() if n.startswith('src/') and not n.endswith('/')]
        assert sources
        for name in sources:
            data = z.read(name)
            assert (BASE / name).read_bytes() == data, name
            p = build / name
            p.parent.mkdir(exist_ok=True)
            p.write_bytes(data)
        for name in ('bin/stockfish', 'data/history.bin'):
            assert z.read(name) == (BASE / name).read_bytes(), name
    mainfile = build / 'src/main.c'
    old = mainfile.read_text()
    new = old
    needle = '    const char *forced = getenv("MIST_FORCE_MOVES");'
    assert new.count(needle) == 1
    new = new.replace(needle, needle + '''
    const int prefix_continue = getenv("ASTRA_PREFIX_CONTINUE") &&
        strcmp(getenv("ASTRA_PREFIX_CONTINUE"), "1") == 0;
    const char *prefix_clocks = getenv("ASTRA_PREFIX_CLOCKS");
''')
    needle = '            clock_left = reported - (now_seconds() - view_at) + increment;'
    assert new.count(needle) == 1
    new = new.replace(needle, needle + '''
            if (prefix_continue) {
                char *clock_end = NULL;
                const double restored = prefix_clocks ? strtod(prefix_clocks, &clock_end) : -1;
                if (!prefix_clocks || clock_end == prefix_clocks || !isfinite(restored) ||
                    restored < 0 || (*clock_end && *clock_end != ',')) {
                    fprintf(stderr, "astra-prefix: invalid post-move clock\\n");
                    break;
                }
                prefix_clocks = *clock_end == ',' ? clock_end + 1 : clock_end;
                clock_left = restored;
                fprintf(stderr, "astra-prefix: decision=%d clock=%.9f\\n", decisions, clock_left);
            }
''')
    needle = '        if (forced) break;   /* decision replay: one searched decision */'
    assert new.count(needle) == 1
    new = new.replace(needle, '        if (forced && !prefix_continue) break;   /* default replay remains one decision */')
    mainfile.write_text(new)
    (OUT / 'continuation.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile='v37/src/main.c', tofile='continuation/src/main.c')))
    files = ['board', 'belief', 'movemodel', 'cfr', 'eval', 'search', 'gtcfr', 'front', 'sfeval', 'main']
    command = ['gcc', '-std=c11', '-O2', '-pthread', '-D_POSIX_C_SOURCE=199309L',
               *[str(build / f'src/{f}.c') for f in files], '-lm', '-o', str(build / 'mist')]
    p = subprocess.run(command, capture_output=True, text=True)
    (OUT / 'build.stdout').write_text(p.stdout)
    (OUT / 'build.stderr').write_text(p.stderr)
    assert p.returncode == 0, p.stderr
    report = dict(archive_sha256=sha(ZIP), source_matches_archive_except_main=True,
        command=command, exit=p.returncode, binary_sha256=sha(build/'mist'),
        sources={n:sha(build/n) for n in sources}, stockfish_sha256=sha(BASE/'bin/stockfish'),
        history_sha256=sha(BASE/'data/history.bin'), patch_sha256=sha(OUT/'continuation.patch'))
    (OUT/'build.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('exit','archive_sha256','binary_sha256')}))


if __name__ == '__main__':
    main()
