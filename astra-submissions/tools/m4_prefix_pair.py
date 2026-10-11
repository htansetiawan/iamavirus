#!/usr/bin/env python3
"""Small, frozen cold/warm replay comparison at specified own decisions.

Uses recorded public/local protocol and referee-derived labels. Does not feed
truth to the bot. Full process outputs belong on the external data drive.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

from m4_gate_run import bounded_process, sha, validate, write_json, now
from m4_replay_probe import inputs


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--replay',type=Path,required=True)
    ap.add_argument('--run',type=Path,required=True)
    ap.add_argument('--binary',type=Path,required=True)
    ap.add_argument('--stockfish',type=Path,required=True)
    ap.add_argument('--side',choices=['white','black'],required=True)
    ap.add_argument('--decisions',type=int,nargs='+',required=True)
    ap.add_argument('--seeds',type=int,nargs='+',default=[11,12])
    flags=ap.add_mutually_exclusive_group()
    flags.add_argument('--tactical-closure',action='store_true')
    flags.add_argument('--compare-closure',action='store_true',help='Paired off/on runs, balanced order')
    ap.add_argument('--modes',nargs='+',choices=['cold','warm'],default=['cold','warm'])
    ap.add_argument('--seconds',type=float,default=.5)
    ap.add_argument('--kit',type=Path,default=Path.home()/'git/fow-starter')
    args=ap.parse_args()
    if args.run.exists():raise ValueError('Use a fresh run directory; existing attempts are not overwritten')
    if len(set(args.modes))!=len(args.modes):raise ValueError('Duplicate modes')
    if args.seconds<=0 or len(set(args.seeds))!=len(args.seeds) or len(set(args.decisions))!=len(args.decisions):
        raise ValueError('Invalid budget, duplicate seeds or duplicate decisions')
    sys.path.insert(0,str(args.kit))
    import chess
    import referee
    replay=json.loads(args.replay.read_text());cases=[]
    for requested in args.decisions:
        side,decision,played,_=inputs(replay,requested,args.side)
        ply=2*(decision-1)+(side=='black')
        board=referee.FowBoard();reps=Counter({referee.position_key(board):1})
        for f in replay['frames'][1:ply+1]:
            move=chess.Move.from_uci(f['move'])
            if referee.outcome(board,reps) or move not in referee.fow_moves(board):raise ValueError('Invalid prefix')
            board.push(move);reps[referee.position_key(board)]+=1
        encoded=''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64))
        if encoded!=replay['frames'][ply]['board'] or board.turn!=(side=='white') or referee.outcome(board,reps):raise ValueError('Target mismatch')
        legal=referee.fow_moves(board);safe=[]
        for move in legal:
            child=board.copy();child.push(move);counts=reps.copy();counts[referee.position_key(child)]+=1
            ending=referee.outcome(child,counts)
            if not ending or ending[0]!=('0-1' if side=='white' else '1-0'):safe.append(move.uci())
        cases.append({'game':replay['id'],'side':side,'decision':decision,'ply':ply,'played':played[decision-1],
                      'legal_moves':sorted(m.uci() for m in legal),'safe_moves':sorted(safe)})
    artifacts={k:{'source':str(p.resolve()),'sha256':sha(p)} for k,p in [
        ('binary',args.binary),('stockfish',args.stockfish),('replay',args.replay),
        ('probe',Path(__file__).with_name('m4_replay_probe.py')),
        ('helper',Path(__file__).with_name('m4_gate_run.py')),('runner',Path(__file__))]}
    config={'created_at':now(),'artifacts':artifacts,'python':sys.executable,'referee_sha256':sha(args.kit/'referee.py'),
            'cpu_affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),
            'seconds':args.seconds,'iterations':1000000,'parents':20000,'samples':128,'cases':cases,'seeds':args.seeds,'tactical_closure':args.tactical_closure,
            'compare_closure':args.compare_closure,'modes':args.modes}
    args.run.mkdir(parents=True)
    for name in ['binary','stockfish','probe','replay']:
        dst=args.run/name;shutil.copyfile(artifacts[name]['source'],dst)
        if name in ['binary','stockfish']:dst.chmod(0o755)
    write_json(args.run/'manifest.json',config)
    env={k:v for k,v in os.environ.items() if not k.startswith('MIST_') and k!='FOW_SEED'}
    rows=[];expected=len(cases)*len(args.seeds)*len(args.modes)*2*(2 if args.compare_closure else 1)
    for i,case in enumerate(cases):
        for j,seed in enumerate(args.seeds):
            for mode in args.modes:
                for variant in (['internal','stockfish'] if (i+j)%2==0 else ['stockfish','internal']):
                    toggles=([False,True] if (i+j)%2==0 else [True,False]) if args.compare_closure else [args.tactical_closure]
                    for closure in toggles:
                        name=f"d{case['decision']}-seed{seed}-{mode}-{variant}"+(f"-closure{int(closure)}" if args.compare_closure else "")
                        out=args.run/name;out.mkdir()
                        command=[sys.executable,str(args.run/'probe'),str(args.run/'replay'),'--binary',str(args.run/'binary'),
                            '--out',str(out),'--kit',str(args.kit),'--side',args.side,'--decision',str(case['decision']),
                            '--mode',mode,'--seconds',str(args.seconds),'--iterations','1000000','--parents','20000',
                            '--samples','128','--seed',str(seed),'--audit-belief']
                        if closure:command+=['--tactical-closure']
                        if variant=='stockfish':command+=['--stockfish',str(args.run/'stockfish')]
                        write_json(out/'command.json',{'argv':command,'at':now()})
                        result=bounded_process(command,out,env,max(90,case['decision']*args.seconds*3+30))
                        row={'decision':case['decision'],'mode':mode,'variant':variant,'seed':seed,'tactical_closure':closure,'status':'failed','process':result}
                        try:
                            if result['returncode'] or result['timed_out']:raise ValueError('Probe process failed')
                            report=json.loads((out/'results.json').read_text())
                            row.update(validate(report,case,dict(config,mode=mode,tactical_closure=closure),variant,seed));row['status']='ok'
                        except (ValueError,KeyError,TypeError,OSError) as error:row['error']=str(error)
                        row['file_hashes']={p.name:sha(p) for p in out.iterdir() if p.is_file()}
                        write_json(out/'receipt.json',row);rows.append(row)
                        summary={'updated_at':now(),'classification':'forced-prefix cold/warm diagnostic; no Elo inference',
                                 'completed':len(rows),'expected':expected,'complete':len(rows)==expected,'rows':rows}
                        write_json(args.run/'summary.json',summary)
                        print(json.dumps({k:row.get(k) for k in ['decision','mode','variant','seed','tactical_closure','status','chosen','immediate_loss']}),flush=True)


if __name__=='__main__':main()
