"""Freeze v38 priority-loss diagnostics; no playing rule or model changes."""
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis/priority-diagnosis-20261109'
BUILD = HERE/'build'
ARCHIVE = ROOT/'astra-submissions/iamavirus-v38-mist-c-allchildren.zip'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, value):
    with p.open('x') as f: json.dump(value, f, indent=2); f.write('\n')


def main():
    assert sha(ARCHIVE) == 'ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f'
    OUT.mkdir(exist_ok=False); BUILD.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((ROOT/'astra-submissions/v38-manifest.json').read_text())
    with zipfile.ZipFile(ARCHIVE) as z:
        for name in z.namelist():
            if not name.startswith(('src/', 'bin/', 'data/')) or name.endswith('/'): continue
            target = BUILD/name; target.parent.mkdir(parents=True, exist_ok=True)
            data = z.read(name)
            assert hashlib.sha256(data).hexdigest() == manifest['source_sha256'][name]
            target.write_bytes(data)
    (BUILD/'bin/stockfish').chmod(0o755)
    sources = ['board','belief','movemodel','cfr','eval','search','gtcfr','front','sfeval','main']
    command = ['gcc','-std=c11','-O2','-pthread','-D_POSIX_C_SOURCE=199309L']
    def compile_to(name, extra=()):
        cmd = command+[str(BUILD/'src'/f'{s}.c') for s in sources]+list(extra)+['-lm','-o',str(BUILD/name)]
        done = subprocess.run(cmd,capture_output=True,text=True,timeout=120)
        assert done.returncode == 0, done.stderr
        return dict(command=cmd,stdout=done.stdout,stderr=done.stderr,sha256=sha(BUILD/name))
    control = compile_to('mist-control')
    teacher = ROOT/'astra-submissions/analysis/deeprl-table-audit-20261025'
    for name in ('teacher_targets.c','teacher_targets.h','teacher_dump.c','teacher_dump.h'):
        shutil.copyfile(teacher/name,BUILD/'src'/name)
    p = BUILD/'src/gtcfr.c'; s = p.read_text()
    s = s.replace('#include "cfr.h"','#include "cfr.h"\n#include "teacher_dump.h"')
    anchor = '    free(x); free(idx); free(share); free(chance_kids); free(chance_p);'
    assert s.count(anchor) == 1
    s = s.replace(anchor,'    astra_teacher_dump(&t.g,x,root_I,&ours,out,b,idx,share,K,params);\n'+anchor)
    p.write_text(s)
    p = BUILD/'src/main.c'; s = p.read_text()
    anchor = '        printf("move %s\\n", uci); fflush(stdout);'
    assert s.count(anchor) == 1
    # No truth variable is read before the move has been emitted. No MIST_RISK
    # or MIST_TRUTH_SEQ is used: those old diagnostics add pre-decision work.
    post = r'''
        if (getenv("ASTRA_POST_READOUT")) {
            const char *tb = getenv("ASTRA_POST_TRUTH");
            double total = 0, mine = 0, highest = -1; size_t matches = 0, rank = 1;
            for (size_t i = 0; i < b.count; ++i) {
                const double w = b.logw ? exp((double)b.logw[i]) : 1.0;
                total += w;
                char placement[65]; pos_to_board_string(&b.items[i],placement);
                if (tb && strlen(tb) == 64 && memcmp(tb,placement,64) == 0) {
                    mine += w; if (w > highest) highest = w; ++matches;
                }
            }
            if (matches) for (size_t i = 0; i < b.count; ++i)
                if ((b.logw ? exp((double)b.logw[i]) : 1.0) > highest) ++rank;
            fprintf(stderr,"astra: placement count=%zu matches=%zu share=%.17g rank=%zu capped=%d\n",
                    b.count,matches,total > 0 ? mine/total : 0,rank,b.overflowed);
            for (int i = 0; i < allowed.count; ++i) {
                const Move m = allowed.moves[i]; double raw, sharp;
                king_risks(&b,m,20000,guard_temp,&raw,&sharp);
                int excluded = 0;
                for (int j = 0; j < gp.avoid_count; ++j) excluded |= gp.avoid[j] == m;
                char text[6]; move_to_uci(m,text);
                fprintf(stderr,"astra: action %s excluded=%d king=%.17g/%.17g queen=%.17g/%.17g chosen=%d\n",
                        text,excluded,raw,sharp,have_qrisk ? qrisk[i] : -1.0,
                        have_qrisk ? qriskt[i] : -1.0,m == r.move);
            }
        }
'''
    s = s.replace(anchor, anchor+post); p.write_text(s)
    diagnostic = compile_to('mist-diagnostic',[str(BUILD/'src/teacher_targets.c'),str(BUILD/'src/teacher_dump.c')])
    proof = ROOT/'astra-submissions/analysis/v38-arena-20261109/20261109T204526Z/priority-losses.json'
    rows = json.loads(proof.read_text())['rows']; cases = []
    for row in rows:
        p = ROOT/'data/raw/games'/row['game']/'replay.json'
        assert sha(p) == row['replay_sha256']
        game = json.loads(p.read_text()); target = row['plies']-1
        points = [('terminal',target)]
        if not row['truth_safe_reply_count']: points.append(('preceding',target-2))
        for kind,ply in points:
            cases.append(dict(game=row['game'],side=row['side'],opponent=row['opponent'],
                              kind=kind,ply=ply,replay_path=str(p),replay_sha256=sha(p),
                              id=f"{row['game']}-{ply}-{kind}"))
    cases.sort(key=lambda c:hashlib.sha256(c['id'].encode()).hexdigest())
    dependencies = [ARCHIVE, proof, HERE/'prepare.py', HERE/'run.py', HERE/'review.py',
                    ROOT/'astra-submissions/tools/fresh_taxonomy_gate.py',
                    Path('/home/henrytan/git/fow-starter/referee.py'),
                    *[p for p in (BUILD/'src').iterdir() if p.is_file()],
                    BUILD/'mist-control',BUILD/'mist-diagnostic',BUILD/'bin/stockfish',BUILD/'data/history.bin']
    write(OUT/'plan.json',dict(at=datetime.now(timezone.utc).isoformat(),control=control,diagnostic=diagnostic,
          cores=[0,1],seeds=[2691109,2691110],cases=cases,case_seconds=120,wall_seconds=1800,
          dependencies={str(p):sha(p) for p in dependencies},
          scope='Post-hoc diagnosis on all26 priority losses plus10 preceding decisions; no strength claim or candidate promotion.',
          original_clock_prompts=True,prefix_max_seconds=10,truth_read_only_after_emitted_move=True,
          caveats=['Forced-prefix replay and wall-clock thinning need not reconstruct arena belief exactly.',
                   'Placement matches ignore castling/en-passant rights; they are an upper bound on true full-state support.',
                   'Teacher export runs after solver selection; post-readout after protocol emission. Output can change total runtime.',
                   'Both seeds retained; no failed attempt replacement. Stop batch on technical failure or global wall cap.']))
    write(OUT/'build.json',dict(control=control,diagnostic=diagnostic))
    print(json.dumps(dict(cases=len(cases),runs=2*len(cases),plan_sha256=sha(OUT/'plan.json'))))


if __name__ == '__main__': main()
