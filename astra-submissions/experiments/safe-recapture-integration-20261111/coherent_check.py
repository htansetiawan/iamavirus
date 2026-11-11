"""Keep queen-risk and piece-guard exclusion coherent; component tests only."""
from datetime import datetime, timezone
import difflib
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/safe-recapture-integration-20261111'
BASE=HERE/'build/corrected/tree'
TREE=HERE/'build/coherent'
ENGINE=ROOT.parent/'fowsearch-c'
NAMES=['board','belief','movemodel','cfr','eval','search','gtcfr','front','sfeval','main']
FLAGS=['-O2','-pthread','-D_POSIX_C_SOURCE=199309L']


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    plan=json.loads((OUT/'coherent-plan.json').read_text())
    assert sha(Path(__file__).read_bytes())==plan['runner_sha256']
    for p,v in plan['pins'].items():assert sha((ROOT/p).read_bytes())==v,p
    allocations=json.loads((ROOT/'chatroom/cores.json').read_text())['allocation']
    assert any(x.get('lease')=='422-coherent-components' and x.get('cores')==[2,3] for x in allocations)
    os.sched_setaffinity(0,{2,3})
    TREE.mkdir(exist_ok=False);shutil.copytree(ENGINE/'src',TREE/'src');shutil.copyfile(ENGINE/'arena/build.sh',TREE/'build.sh')
    original=(ENGINE/'src/main.c').read_text();partial=(BASE/'src/main.c').read_text()
    a=partial.index('static int best_capture_net(');b=partial.index('static void piece_risks(',a)
    old='if (is_attacked(&q, sq, us)) gain -= piece_pawns[p->piece[MOVE_FROM(l->moves[j])]];'
    new='if (is_attacked(&q, sq, us) && (p->piece[sq] != QUEEN || astra_safe_recapture(&q, sq))) gain -= piece_pawns[p->piece[MOVE_FROM(l->moves[j])]];'
    function=partial[a:b];assert function.count(old)==1
    coherent=partial[:a]+function.replace(old,new)+partial[b:]
    assert coherent.replace(new,old,1)==partial
    (TREE/'src/main.c').write_text(coherent)
    patch=''.join(difflib.unified_diff(original.splitlines(True),coherent.splitlines(True),fromfile='a/src/main.c',tofile='b/src/main.c')).encode()
    patchpath=HERE/'current-source-coherent.patch.gz'
    with patchpath.open('xb') as f:
        with gzip.GzipFile(filename='',mode='wb',fileobj=f,mtime=0) as z:z.write(patch)
    # Preserve the original helper only as an independent nonqueen parity control.
    old_a=original.index('static int best_capture_net(');old_b=original.index('static void piece_risks(',old_a)
    original_net=original[old_a:old_b].replace('static int best_capture_net(','static int astra_original_best_capture_net(',1)
    probe=(BASE/'src/probe.c').read_text()
    marker='int main(void) {';assert probe.count(marker)==1
    probe=probe.replace(marker,original_net+'\n'+marker,1)
    extra=r'''
        for(int i=0;i<count;++i){
            Belief one={0};one.items=&positions[i];one.count=1;one.us=positions[i].side;
            double q,qt,p,pt;queen_risks(&one,move,1,temp,threshold,&q,&qt,NULL);
            piece_risks(&one,move,1,temp,3,threshold,&p,&pt,NULL);
            if(q>0 && p>0)return 7;
            Position after=positions[i];Undo undo;make_move(&after,move,&undo);
            const int us=positions[i].side;
            for(int sq=0;sq<64;++sq){
                if(after.color[sq]!=us || after.piece[sq]==KING || after.piece[sq]==QUEEN)continue;
                MoveList x,y;int gx=0,gy=0;
                if(best_capture_net(&after,sq,us,&x,&gx)!=astra_original_best_capture_net(&after,sq,us,&y,&gy))return 8;
            }
        }
'''
    needle='        Belief b={0};b.items=positions;';assert probe.count(needle)==1
    probe=probe.replace(needle,extra+needle,1)
    (TREE/'src/probe.c').write_text(probe)
    shutil.copyfile(BASE/'src/partition-probe.c',TREE/'src/partition-probe.c')
    commands=[]
    def run(label,argv,inputs=None):
        p=subprocess.run(argv,cwd=TREE,input=inputs,capture_output=True,text=True,timeout=15)
        row=dict(label=label,argv=argv,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr)
        commands.append(row)
        with (OUT/'coherent-commands.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
        assert p.returncode==0,row
        return row
    run('production-gcc',['bash','build.sh'])
    production=['src/'+n+'.c' for n in NAMES]
    common=['src/'+n+'.c' for n in NAMES if n!='main']
    for p in ('probe','partition-probe'):run('gcc-'+p,['gcc','-std=c11',*FLAGS,*common,'src/'+p+'.c','-lm','-o',p+'-gcc'])
    objects=TREE/'objects';objects.mkdir()
    for n in NAMES+['probe','partition-probe']:
        run('g++-c-'+n,['g++','-x','c','-std=c11',*FLAGS,'-c','src/'+n+'.c','-o',str(objects/(n+'.o'))])
    for label,names in [('mist',NAMES),('probe',[n for n in NAMES if n!='main']+['probe']),('partition-probe',[n for n in NAMES if n!='main']+['partition-probe'])]:
        run(label+'-xc-link',['g++','-pthread',*[str(objects/(n+'.o')) for n in names],'-lm','-o',label+'-xc'])
    for label,names in [('mist',production),('probe',common+['src/probe.c']),('partition-probe',common+['src/partition-probe.c'])]:
        run(label+'-cpp-build',['g++','-x','c++','-std=c++20','-fpermissive','-w',*FLAGS,*names,'-lm','-o',label+'-cpp'])
    inputs=(OUT/'component-input.txt').read_text();baseline=json.loads((OUT/'result.json').read_text())['runs'][0]['rows']
    pair=json.loads((OUT/'partition-cases.json').read_text());pairinputs='\n'.join(p['board'] for p in pair)+'\n'
    outputs=[]
    for suffix in ('gcc','xc','cpp'):
        rows=[json.loads(l) for l in run('probe-'+suffix,[str(TREE/('probe-'+suffix))],inputs)['stdout'].splitlines()]
        assert rows==baseline
        partitions=[json.loads(l) for l in run('partition-'+suffix,[str(TREE/('partition-probe-'+suffix))],pairinputs)['stdout'].splitlines()]
        assert len(partitions)==2 and partitions[0]['queen_amended']==1 and partitions[0]['piece_unchanged']==0
        assert partitions[1]['queen_amended']==0 and partitions[1]['piece_unchanged']==1
        assert partitions[0]['combined']==.9 and partitions[1]['combined']==.758
        outputs.append(dict(compiler=suffix,rows=rows,partition_rows=partitions))
    for path,v in plan['engine_sources'].items():assert sha((ENGINE/path).read_bytes())==v
    result=dict(passed=True,at=datetime.now(timezone.utc).isoformat(),compiler_paths=3,queen_cases_per_path=26,
        partition_cases_per_path=2,queen_rows_match_partial=True,per_world_queen_piece_disjointness=True,
        nonqueen_capture_net_parity=True,policy_or_backend_runs=0,original_main_sha256=sha(original.encode()),
        amended_main_sha256=sha(coherent.encode()),patch_sha256=sha(patch),gzip_sha256=sha(patchpath.read_bytes()),outputs=outputs,
        scope='Three-compiler component acceptance for two coherent predicate amendments. No policy, playing strength or arena qualification.',
        preserved='Partial-patch overlap counterexample and original 26-case passes are retained, not relabeled as whole-system acceptance.')
    with (OUT/'coherent-result.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ('passed','compiler_paths','queen_cases_per_path','partition_cases_per_path','policy_or_backend_runs')}))


if __name__=='__main__':main()
