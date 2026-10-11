#!/usr/bin/env python3
"""Build isolated experimental prior replay runner; shared C files untouched."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--c-root',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();args.out.mkdir(exist_ok=False)
    native=['board.c','belief.c','belief.h','front.c','front.h','fow.h','eval.c','eval.h','movemodel.c','movemodel.h','m4movefeatures.h']
    for name in native:shutil.copyfile(args.c_root/'src'/name,args.out/name)
    shutil.copyfile(Path(__file__).with_name('m4_intent_logits.c'),args.out/'intent.c')
    old=(args.c_root/'tools/m4_prior_replay.c').read_text()
    start=old.index('void __wrap_move_logits(');end=old.index('static Move parse_move(',start)
    replacement='''
void m4_intent_logits(const Position*,const MoveList*,Move,const float*,const float*,float*);
void __wrap_move_logits(const Position *p,const MoveList *l,Move previous,int full,float *out) {
    if(!full){++cheap_calls;__real_move_logits(p,l,previous,full,out);return;}
    ++full_calls;
    if(width!=26){fprintf(stderr,"intent runner requires26-feature base\\n");exit(3);}
    static int read_gate=0;static float gate[7];
    if(!read_gate){
        read_gate=1;const char *path=getenv("M4_INTENT_GATE");
        if(path){FILE *f=fopen(path,"r");int n=0;if(!f||fscanf(f,"%d",&n)!=1||n!=7)exit(3);
            for(int k=0;k<7;++k)if(fscanf(f,"%f",&gate[k])!=1||!isfinite(gate[k]))exit(3);
            fclose(f);}
    }
    m4_intent_logits(p,l,previous,theta,gate,out);
}
'''
    text=old[:start]+replacement+old[end:]
    text=text.replace('../src/m4movefeatures.h','m4movefeatures.h').replace('../src/front.h','front.h')
    (args.out/'runner.c').write_text(text)
    cmd=['cc','-O2','-std=c11','-Wall','-Wextra','-Wpedantic','-I',str(args.out),
         *[str(args.out/name) for name in ['board.c','belief.c','movemodel.c','eval.c','front.c','intent.c','runner.c']],
         '-Wl,--wrap=move_logits','-lm','-o',str(args.out/'runner')]
    subprocess.run(cmd,check=True)
    shared=['cc','-O2','-std=c11','-shared','-fPIC','-I',str(args.out),
            *[str(args.out/name) for name in ['board.c','movemodel.c','intent.c']],'-lm','-o',str(args.out/'intent.so')]
    subprocess.run(shared,check=True)
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in args.out.iterdir() if p.is_file()}
    (args.out/'manifest.json').write_text(json.dumps({'commands':[cmd,shared],'sha256':hashes,
        'source_runner_sha256':hashlib.sha256(old.encode()).hexdigest()},indent=2)+'\n')
    print(json.dumps({'runner':str(args.out/'runner'),'sha256':hashes['runner']}))


if __name__=='__main__':main()
