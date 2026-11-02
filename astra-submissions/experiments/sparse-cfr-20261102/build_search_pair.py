"""Link original and optimized search with separate Game layouts, shared belief."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis/sparse-cfr-20261102'
DEST = HERE/'build/diagnostic'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def replace(s, a, b):
    assert s.count(a) == 1, a
    return s.replace(a, b)


def main():
    frozen = json.loads((OUT/'plan.json').read_text())
    for p, h in frozen['build'].items(): assert sha(ROOT/p) == h, p
    assert json.loads((OUT/'summary.json').read_text())['gate_pass']
    assert not (OUT/'search-build.json').exists(), 'preserve a completed diagnostic build'
    DEST.mkdir(exist_ok=True)
    teacher = ROOT/'astra-submissions/analysis/deeprl-table-audit-20261025'
    for arm in ('base','fast'):
        src = DEST/arm
        shutil.copytree(HERE/'build'/arm/'src', src, dirs_exist_ok=True)
        for name in ('teacher_targets.c','teacher_targets.h','teacher_dump.c','teacher_dump.h'):
            shutil.copyfile(teacher/name, src/name)
        p = src/'gtcfr.c'
        s = replace(p.read_text(), '#include "cfr.h"', '#include "cfr.h"\n#include "teacher_dump.h"')
        anchor = '    free(x); free(idx); free(share); free(chance_kids); free(chance_p);'
        s = replace(s, anchor, '    astra_teacher_dump(&t.g,x,root_I,&ours,out,b,idx,share,K,params);\n'+anchor)
        p.write_text(s)
    p = DEST/'fast/main.c'
    s = replace(p.read_text(), '#include "gtcfr.h"', '#include "gtcfr.h"\nint astra_solver_pair(const Belief *, const GtcfrParams *, SearchResult *);')
    p.write_text(replace(s, 'gtcfr_decide(&b, &gp, &r)', 'astra_solver_pair(&b, &gp, &r)'))
    symbols = ['game_init','game_free','game_infoset','game_node','game_children','game_finalize',
               'game_grow','game_expand_leaf','game_start_on','pcfr_iteration','pcfr_current',
               'pcfr_infoset_strategy','pcfr_average','game_value','best_response_value','exploitability',
               'gtcfr_decide','teacher_targets','teacher_targets_free','astra_teacher_dump']
    flags = ['-std=c11','-O2','-pthread','-D_POSIX_C_SOURCE=200809L']
    records=[]; objects=[]
    def run(cmd):
        r = subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=120)
        records.append(dict(command=list(map(str,cmd)),exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
        assert r.returncode == 0, r.stderr
    for arm in ('base','fast'):
        names = ['cfr','gtcfr','teacher_targets','teacher_dump']
        if arm == 'fast': names += ['board','belief','movemodel','eval','search','front','sfeval','main']
        for name in names:
            obj = DEST/(arm+'-'+name+'.o'); objects.append(obj)
            rename = ['-D'+s+'=base_'+s for s in symbols] if arm == 'base' else []
            run(['gcc',*flags,*rename,'-I',DEST/arm,'-c',DEST/arm/(name+'.c'),'-o',obj])
    run(['gcc',*flags,'-I',DEST/'fast',HERE/'search_pair.c',*objects,'-lm','-o',DEST/'mist'])
    resource = HERE.parent/'queen-terminal-backport-20261102/build-r2/base'
    for name in ('bin','data'):
        (DEST/name).symlink_to(resource/name,target_is_directory=True)
    shutil.copyfile(resource/'run.sh',DEST/'run.sh')
    pins={str(p.relative_to(ROOT)):sha(p) for p in [*sorted((DEST/'base').glob('*')),
         *sorted((DEST/'fast').glob('*')),DEST/'mist',DEST/'run.sh',DEST/'bin/stockfish',DEST/'data/history.bin',HERE/'search_pair.c'] if p.is_file()}
    with (OUT/'search-build.json').open('x') as f:
        json.dump(dict(records=records,pins=pins),f,indent=2);f.write('\n')
    print(json.dumps(dict(binary_sha256=sha(DEST/'mist'),compiled=True)))


if __name__ == '__main__': main()
