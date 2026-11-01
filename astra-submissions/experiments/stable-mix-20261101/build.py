#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
ARCHIVE=ROOT/'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'
EXPECTED='41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(s,a,b):
    assert s.count(a)==1,a
    return s.replace(a,b)

def main():
    assert sha(ARCHIVE)==EXPECTED
    base=HERE/'build/base'; candidate=HERE/'build/candidate'
    base.mkdir(parents=True,exist_ok=True);candidate.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(ARCHIVE) as z:z.extractall(base)
    shutil.copytree(base/'src',candidate/'src',dirs_exist_ok=True)
    for name in ['build.sh','run.sh']:shutil.copyfile(base/name,candidate/name)
    for name in ['bin','data']:
        if not (candidate/name).exists():(candidate/name).symlink_to(base/name,target_is_directory=True)
    path=candidate/'src/gtcfr.c'; original=path.read_text();s=original
    s=replace(s,'#include "sfeval.h"','#include "sfeval.h"\n#include "root_mix.h"')
    s=replace(s,'    int iteration = 0, explorer = 0, grown = 0;',
              '''    int iteration = 0, explorer = 0, grown = 0;
    const int mix_mode = getenv("MIST_ROOT_MIX") ? atoi(getenv("MIST_ROOT_MIX")) : 0;
    assert(mix_mode >= 0 && mix_mode <= 2);
    RootMixTrack mix_track; memset(&mix_track,0,sizeof(mix_track));
#define ASTRA_ITERATE() do { \\
    pcfr_iteration(&t.g, ++iteration); \\
    if (mix_mode == 2) { double root_x[256]; pcfr_infoset_strategy(&t.g,root_I,root_x); \\
        root_mix_observe(&mix_track,root_x,ours.count,seconds_since(&t0),params->seconds); } \\
} while (0)''')
    # Four call sites plus the macro body. Keep the macro's own original call.
    needle='pcfr_iteration(&t.g, ++iteration);'; assert s.count(needle)==4
    start=s.index('#define ASTRA_ITERATE()'); end=s.index('} while (0)',start)+len('} while (0)')
    s=s[:end]+s[end:].replace(needle,'ASTRA_ITERATE();')
    s=replace(s,'    out->move = ours.moves[best];\n    out->probability = x[o + best];',
              '''    double executed_probability = x[o + best];
    if (mix_mode) best = root_mix_pick(&mix_track,x+o,ours.count,mix_mode,&executed_probability);
    out->move = ours.moves[best];
    out->probability = executed_probability;
#undef ASTRA_ITERATE''')
    path.write_text(s);shutil.copyfile(HERE/'root_mix.h',candidate/'src/root_mix.h')
    builds={}
    for label,d in [('base',base),('candidate',candidate)]:
        p=subprocess.run(['bash','build.sh'],cwd=d,capture_output=True,text=True,timeout=90)
        (HERE/(label+'-build.log')).write_text(p.stdout+p.stderr);p.check_returncode()
        builds[label]={'binary_sha256':sha(d/'mist'),'gtcfr_sha256':sha(d/'src/gtcfr.c')}
    unchanged={p.name:sha(p) for p in (base/'src').iterdir() if p.name!='gtcfr.c'}
    assert all(sha(candidate/'src'/name)==h for name,h in unchanged.items())
    result={'archive_sha256':EXPECTED,'builds':builds,'unchanged_source_hashes':unchanged,
            'header_sha256':sha(HERE/'root_mix.h'),'builder_sha256':sha(Path(__file__)),
            'stockfish_sha256':sha(base/'bin/stockfish'),'history_sha256':sha(base/'data/history.bin')}
    (HERE/'provenance.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(builds,indent=2))

if __name__=='__main__':main()
