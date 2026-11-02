from pathlib import Path
import hashlib
import json
import shutil
import subprocess
from build import HERE, ROOT, OUT, replace


def main():
    dst=HERE/'build/diagnostic';shutil.copytree(HERE/'build/candidate',dst,dirs_exist_ok=True)
    source=ROOT/'astra-submissions/analysis/deeprl-table-audit-20261025'
    for name in ('teacher_targets.c','teacher_targets.h','teacher_dump.c','teacher_dump.h'):
        shutil.copyfile(source/name,dst/'src'/name)
    for name in ('expansion_pair.c','expansion_pair.h'):shutil.copyfile(HERE/name,dst/'src'/name)
    p=dst/'src/gtcfr.c';s=p.read_text();s=replace(s,'#include "cfr.h"','#include "cfr.h"\n#include "teacher_dump.h"')
    anchor='    free(x); free(idx); free(share); free(chance_kids); free(chance_p);'
    s=replace(s,anchor,'    astra_teacher_dump(&t.g,x,root_I,&ours,out,b,idx,share,K,params);\n'+anchor);p.write_text(s)
    p=dst/'src/main.c';s=p.read_text();s=replace(s,'#include <stdio.h>','#include <stdio.h>\n#include "expansion_pair.h"')
    p.write_text(replace(s,'gtcfr_decide(&b, &gp, &r)','astra_expansion_pair(&b, &gp, &r)'))
    p=dst/'build.sh';p.write_text(replace(p.read_text(),'src/expansion_values.c','src/expansion_values.c src/expansion_pair.c src/teacher_targets.c src/teacher_dump.c'))
    r=subprocess.run(['bash','build.sh'],cwd=dst,capture_output=True,text=True,timeout=120)
    (OUT/'build-diagnostic.log').write_text(r.stdout+r.stderr);r.check_returncode()
    pins={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*sorted((dst/'src').glob('*')),dst/'mist',dst/'build.sh'] if p.is_file()}
    (OUT/'diagnostic-pins.json').write_text(json.dumps(pins,indent=2)+'\n');print('diagnostic',pins[str((dst/'mist').relative_to(ROOT))])


if __name__=='__main__':main()
