"""Build isolated startup tracing; shipped engine and Fable sources stay fixed."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis/sf-startup-diagnosis-20261110'
SHIP = HERE.parent/'guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)

def instrument(text):
    text = replace_once(text, 'static void stop_worker(Worker *w) {',
        '#include "startup_trace.h"\n\nstatic void stop_worker(Worker *w) {')
    a, b = text.index('static int read_line('), text.index('static int wait_for(')
    part = text[a:b]
    part = replace_once(part, 'if (left <= 0) return 0;',
        'if (left <= 0) { astra_startup_event(w, "read-deadline", NULL, 1); return 0; }')
    part = replace_once(part,
        'if (r <= 0) { if (r < 0 && errno == EINTR) continue; return 0; }',
        'if (r <= 0) { if (r < 0 && errno == EINTR) continue; astra_startup_event(w, r == 0 ? "poll-timeout" : "poll-error", NULL, 1); return 0; }')
    part = replace_once(part,
        'if (got <= 0) { if (got < 0 && errno == EINTR) continue; return 0; }',
        'if (got <= 0) { if (got < 0 && errno == EINTR) continue; astra_startup_event(w, got == 0 ? "read-eof" : "read-error", NULL, 1); return 0; }')
    text = text[:a]+part+text[b:]
    text = replace_once(text,
        'if (strncmp(line, prefix, strlen(prefix)) == 0) return 1;',
        'if (astra_startup_lines++ < 64) astra_startup_event(w, "line", line, 0);\n'
        '        if (strncmp(line, prefix, strlen(prefix)) == 0) { astra_startup_event(w, "matched", prefix, 0); return 1; }')
    marker = 'w->to_fd = w->from_fd = -1; w->child = -1;\n    if (pipe(in) != 0) return 0;'
    text = replace_once(text, marker,
        'w->to_fd = w->from_fd = -1; w->child = -1;\n'
        '    astra_startup_active = 1; astra_startup_lines = 0; astra_startup_begin = now(); astra_startup_phase = "fork";\n'
        '    if (pipe(in) != 0) { astra_startup_event(w, "pipe-input-failed", NULL, 0); astra_startup_active = 0; return 0; }')
    text = replace_once(text,
        'if (pipe(out) != 0) { close(in[0]); close(in[1]); return 0; }',
        'if (pipe(out) != 0) { astra_startup_event(w, "pipe-output-failed", NULL, 0); astra_startup_active = 0; close(in[0]); close(in[1]); return 0; }')
    text = replace_once(text,
        'if (w->child < 0) { close(in[0]); close(in[1]); close(out[0]); close(out[1]); w->child = -1; return 0; }',
        'if (w->child < 0) { astra_startup_event(w, "fork-failed", NULL, 0); astra_startup_active = 0; close(in[0]); close(in[1]); close(out[0]); close(out[1]); w->child = -1; return 0; }')
    old = '''    if (!send_line(w, "uci\\n") || !wait_for(w, "uciok", 5000) ||
        !send_line(w, setup) ||
        !wait_for(w, "readyok", 5000)) {
        stop_worker(w);
        return 0;
    }
    return 1;'''
    new = '''    astra_startup_phase = "uci";
    astra_startup_event(w, "begin", NULL, 0);
    if (!send_line(w, "uci\\n") || !wait_for(w, "uciok", 5000)) goto startup_failed;
    astra_startup_phase = "ready";
    astra_startup_event(w, "begin", NULL, 0);
    if (!send_line(w, setup) || !wait_for(w, "readyok", 5000)) goto startup_failed;
    astra_startup_event(w, "success", NULL, 0);
    astra_startup_active = 0;
    return 1;
startup_failed:
    astra_startup_event(w, "failed", NULL, 1);
    astra_startup_active = 0;
    stop_worker(w);
    return 0;'''
    return replace_once(text, old, new)

def main():
    assert sha(SHIP/'mist') == '14ac30b34999a6a667e4dcdfb1b4606b184dbacbdc2fcfdf7f6b257513543fcd'
    build = HERE/'build'; build.mkdir(exist_ok=False)
    OUT.mkdir(parents=True, exist_ok=True)
    diag = build/'diagnostic'
    shutil.copytree(SHIP/'src', diag/'src')
    for name in ('run.sh','build.sh'): shutil.copyfile(SHIP/name, diag/name)
    for name in ('bin','data'): (diag/name).symlink_to(SHIP/name, target_is_directory=True)
    (diag/'src/sfeval.c').write_text(instrument((SHIP/'src/sfeval.c').read_text()))
    shutil.copyfile(HERE/'startup_trace.h', diag/'src/startup_trace.h')
    shutil.copyfile(ROOT.parent/'fow-starter/referee.py', build/'referee.py')
    (HERE/'fake_engine.py').chmod(0o755)
    commands=[]
    def run(command, cwd=None):
        result=subprocess.run(list(map(str,command)),cwd=cwd,capture_output=True,text=True,timeout=120)
        row=dict(command=list(map(str,command)),cwd=str(cwd) if cwd else None,code=result.returncode,stdout=result.stdout,stderr=result.stderr)
        commands.append(row)
        (OUT/'build-progress.json').write_text(json.dumps(commands,indent=2)+'\n')
        assert result.returncode == 0, result.stderr
    run(['bash','build.sh'], diag)
    for name,src in [('reference',SHIP/'src'),('diagnostic',diag/'src')]:
        run(['gcc','-std=c11','-O2','-pthread','-I',src,HERE/'driver.c',src/'board.c',src/'sfeval.c','-lm','-o',build/(name+'-driver')])
    names=['board','belief','movemodel','cfr','eval','search','gtcfr','front','sfeval','main']
    run(['g++','-x','c++','-std=c++20','-O2','-pthread','-fpermissive','-w',*[diag/'src'/(n+'.c') for n in names],'-lm','-o',build/'diagnostic-cpp'])
    changed=[p.name for p in (SHIP/'src').iterdir() if p.is_file() and p.read_bytes() != (diag/'src'/p.name).read_bytes()]
    assert changed==['sfeval.c'],changed
    dependencies={str(p):sha(p) for p in [*sorted((diag/'src').glob('*')),diag/'run.sh',diag/'build.sh',diag/'mist',build/'diagnostic-cpp',build/'reference-driver',build/'diagnostic-driver',build/'referee.py',SHIP/'mist',SHIP/'bin/stockfish',SHIP/'data/history.bin',HERE/'prepare.py',HERE/'driver.c',HERE/'fake_engine.py',HERE/'startup_trace.h']}
    result=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,changed_original_files=changed,new_source_files=['startup_trace.h'],unchanged_launchers=True,unchanged_handshake_deadlines_ms=5000,no_retry=True,commands=commands,dependencies=dependencies)
    (OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('commands','dependencies')}))

if __name__=='__main__': main()
