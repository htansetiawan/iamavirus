"""Offline oracle feasibility data, not runtime/private-input reconstruction."""
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/past-alias-20261110';BUILD=HERE/'build'
PRIOR=ROOT/'astra-submissions/analysis/belief-sort-cost-20261110/plan.json'
STORE=Path('/media/henrytan/seagate/iamavirus/astra/past-alias-20261110')
sys.path.insert(0,str(ROOT.parent/'fow-starter'))
import referee as ref


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def text(board):return ''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64))
def position(board):return dict(board=text(board),side=0 if board.turn else 1,castle=f'{board.castling_rights:016x}',
                               ep=-1 if board.ep_square is None else board.ep_square,halfmove=board.halfmove_clock)
def line(p,a,b):return f"{p['board']} {p['side']} {p['castle']} {p['ep']} {p['halfmove']} {a} {b}"


def main():
    OUT.mkdir(exist_ok=False);BUILD.mkdir(exist_ok=False)
    prior=json.loads(PRIOR.read_text());source=Path(prior['parent'])/'src'
    commands=[]
    for name,flags in [('mine',['-O2','-Wall','-Wextra']),('mine-sanitize',['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
        cmd=['gcc','-std=c11',*flags,'-I',str(source),str(HERE/'mine.c'),str(source/'board.c'),'-o',str(BUILD/name)]
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=60);assert r.returncode==0,r.stderr
        commands.append(dict(command=cmd,stderr=r.stderr))
    toy=ref.FowBoard(None)
    for sq,piece in {'h1':'K','a1':'R','e2':'P','e8':'k','d3':'p','a7':'p'}.items():
        toy.set_piece_at(ref.chess.parse_square(sq),ref.chess.Piece.from_symbol(piece))
    toy.turn=True;toy.castling_rights=0
    fixture=line(position(toy),'a1e1','a7a6')+'\n'
    outputs=[]
    for binary in ('mine','mine-sanitize'):
        r=subprocess.run([str(BUILD/binary)],input=fixture,capture_output=True,text=True,timeout=20)
        assert r.returncode==0,r.stderr;outputs.append(r.stdout)
    assert outputs[0]==outputs[1]
    witness=[json.loads(s) for s in outputs[0].splitlines() if json.loads(s)['kind']=='witness']
    wanted=next(r for r in witness if r['alternative_previous']=='a1f1' and r['common_current_move']=='e2d3')
    assert wanted['actual_danger']==1 and wanted['alternative_danger']==0
    reply=next(r for r in wanted['replies'] if r['uci']=='a6a5');assert reply['actual_safe']==0 and reply['alternative_safe']==1
    (OUT/'fixture-input.txt').write_text(fixture);(OUT/'fixture-output.jsonl').write_text(outputs[0])
    cases=[];inputs=[]
    for old in prior['cases']:
        replay=json.loads(Path(old['replay_path']).read_text());assert sha(old['replay_path'])==old['replay_sha256']
        eligible=list(range(2,min(20,len(replay['frames'])-2)+1))
        selected=[]
        for side in (0,1):
            plies=[p for p in eligible if p%2==side]
            selected+=sorted(plies,key=lambda p:hashlib.sha256(f"288-past-{old['game']}-{p}".encode()).digest())[:2]
        assert len(selected)==4
        boards=[];board=ref.FowBoard()
        for frame in replay['frames'][:max(selected)+1]:
            if frame['move']:
                move=ref.chess.Move.from_uci(frame['move']);assert move in ref.fow_moves(board);board.push(move)
            assert text(board)==frame['board']
            boards.append(board.copy(stack=True))
        for ply in sorted(selected):
            ancestor=boards[ply-2];a=replay['frames'][ply-1]['move'];b=replay['frames'][ply]['move']
            record=dict(context=len(cases),game=old['game'],ply=ply,side='white' if ply%2==0 else 'black',
                        replay_path=old['replay_path'],replay_sha256=old['replay_sha256'],ancestor=position(ancestor),
                        actual_previous=a,same_opponent_move=b,recorded_current=replay['frames'][ply+1]['move'])
            cases.append(record);inputs.append(line(record['ancestor'],a,b))
    (OUT/'input.txt').write_text('\n'.join(inputs)+'\n')
    write(OUT/'preflight.json',dict(at=datetime.now(timezone.utc).isoformat(),passed=True,commands=commands,
          sanitized_equal=True,royal_alias_fixture=wanted,fixture_witnesses=len(witness),
          caveat='Synthetic board need not have a standard-opening prefix. Corpus witnesses separately use actual legal full prefixes.'))
    deps=[Path(__file__),HERE/'mine.c',HERE/'run.py',HERE/'audit.py',BUILD/'mine',source/'board.c',source/'fow.h',PRIOR,
          OUT/'input.txt',Path(ref.__file__)]+[Path(c['replay_path']) for c in cases]
    write(OUT/'plan.json',dict(at=datetime.now(timezone.utc).isoformat(),cases=cases,core=6,process_seconds=120,
          output_limit=512*1024*1024,bulk_store=str(STORE),dependencies={str(p):sha(p) for p in deps},
          selection='Eight existing outcome-independent control games. Two hash-selected plies per seat, current plies2–20. No result filter.',
          method='OFFLINE ORACLE: completed true ancestor plus actual previous own move and opponent reply enter the C miner. '
                 'Vary previous own move, hold opponent reply fixed only when BOTH intervening full opponent views match. '
                 'Require a distinct current physical world, then a common current move giving identical opponent view but '
                 'different royal danger and safe reply sets. Counterfactual reach weights are NULL. No actor sees this data.',
          criteria='Independent legal full-prefix/path/private-observation checks, with 50-move/repetition endings excluded '
                   'and counted by the referee audit. At least12 valid witnesses across4 games merits a separate private-input '
                   'ancestry-generator design; no playing/search promotion. Report actual-current-move hits, both danger directions '
                   'and empty/nonempty common safe-reply intersections. No world probabilities or Elo inferred.',
          prior_work='062 labels future opponent-action aliases;251 proves current-I history replication alone does not couple roots. '
                     'Existing M4 already carries off-I histories, but fresh roots have separate scopes. This tests reachability '
                     'of past-own-action alternatives, not a new KLUSS solver or rerun of old M4/DBR matches.'))
    print(json.dumps(dict(prepared=True,contexts=len(cases),games=len(prior['cases']),fixture_witnesses=len(witness))),flush=True)


if __name__=='__main__':main()
