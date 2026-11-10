"""Final reply-risk operator: same check status is allowed; same dev data."""
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/private-reply-join-20261110';BUILD=HERE/'build'
FIRST=HERE.parent/'past-alias-20261110';PREVIOUS=HERE.parent/'private-action-join-20261110'
FIRSTOUT=ROOT/'astra-submissions/analysis/past-alias-20261110';PREVOUT=ROOT/'astra-submissions/analysis/private-action-join-20261110'
STORE=Path('/media/henrytan/seagate/iamavirus/astra/private-reply-join-20261110')
spec=importlib.util.spec_from_file_location('first_past_alias_helpers',FIRST/'prepare.py');first=importlib.util.module_from_spec(spec);spec.loader.exec_module(first)
sha,write,position,text,line=first.sha,first.write,first.position,first.text,first.line
sys.path.insert(0,str(ROOT.parent/'fow-starter'))
import referee as ref


def main():
    OUT.mkdir(exist_ok=False);BUILD.mkdir(exist_ok=False)
    prior=json.loads((PREVOUT/'plan.json').read_text());assert json.loads((PREVOUT/'audit.json').read_text())['validated_witnesses']==0
    source=Path(json.loads(first.PRIOR.read_text())['parent'])/'src';commands=[]
    for name,flags in [('mine',['-O2','-Wall','-Wextra']),('mine-sanitize',['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
        cmd=['gcc','-std=c11',*flags,'-I',str(source),str(HERE/'mine.c'),str(source/'board.c'),'-o',str(BUILD/name)]
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=60);assert r.returncode==0,r.stderr;commands.append(dict(command=cmd,stderr=r.stderr))
    toy=ref.FowBoard(None)
    for sq,piece in {'h1':'K','a1':'Q','c4':'B','e8':'k','e7':'p','a7':'p'}.items():
        toy.set_piece_at(ref.chess.parse_square(sq),ref.chess.Piece.from_symbol(piece))
    toy.turn=True;toy.castling_rights=0;fixture=line(position(toy),'a1e1','a7a6')+'\n';outputs=[]
    for binary in ['mine','mine-sanitize']:
        r=subprocess.run([str(BUILD/binary)],input=fixture,capture_output=True,text=True,timeout=20)
        assert r.returncode==0,r.stderr;outputs.append(r.stdout)
    assert outputs[0]==outputs[1]
    witness=[json.loads(s) for s in outputs[0].splitlines() if json.loads(s)['kind']=='witness']
    wanted=next(r for r in witness if r['alternative_previous']=='a1f1' and r['actual_current_move']=='c4f7'
                and r['alternative_current_move']=='c4f7' and r['actual_danger']==r['alternative_danger']==1)
    reply=next(r for r in wanted['replies'] if r['uci']=='e8f7');assert reply['actual_safe']==1 and reply['alternative_safe']==0
    (OUT/'fixture-input.txt').write_text(fixture);(OUT/'fixture-output.jsonl').write_text(outputs[0])
    (OUT/'input.txt').write_bytes((PREVOUT/'input.txt').read_bytes())
    write(OUT/'preflight.json',dict(at=datetime.now(timezone.utc).isoformat(),passed=True,commands=commands,
          sanitized_equal=True,same_check_bait_fixture=wanted,fixture_witnesses=len(witness),
          scope='Synthetic same visible bishop check; hidden queen changes king recapture safety. Not corpus evidence.'))
    deps=[Path(__file__),HERE/'mine.c',HERE/'run.py',HERE/'audit.py',FIRST/'mine.c',FIRST/'prepare.py',BUILD/'mine',
          PREVOUT/'plan.json',PREVOUT/'audit.json',PREVOUT/'input.txt',OUT/'input.txt',source/'board.c',source/'fow.h',Path(ref.__file__)]
    deps+=[Path(c['replay_path']) for c in prior['cases']]
    write(OUT/'plan.json',dict(at=datetime.now(timezone.utc).isoformat(),cases=prior['cases'],core=6,process_seconds=120,
          output_limit=512*1024*1024,bulk_store=str(STORE),dependencies={str(p):sha(p) for p in deps},
          method='Final OFFLINE ORACLE interface on288/289 reused development contexts. Same history/observation/legal-row '
                 'construction as289, but only differing reply-safety vectors are required: current check status may match. '
                 'This admits king-bait patterns which the earlier different-check filter excluded. Truth ancestors and '
                 'recorded hidden replies are oracle inputs; no runtime or playing behavior changes.',
          complexity='Children/reply safety computed once and exact consequence classes hashed; same-view legal-row join '
                     'is expected output-sensitive after reply evaluation. Canonical representatives serve this diagnostic '
                     'only; no playing-state merging or arbitrary-world probability is introduced.',
          criteria='Full prefix/path/private-view/reply audit and terminal draw exclusions. >=12 individually escapable '
                   'witnesses in4 games permits separate private-input ancestry design only. Record both check statuses, '
                   'king-recapture changed replies, representative actual-move hits and empty safe intersections.',
          stop='No fourth interface screen, larger corpus or match batch automatically if this fails. Both prior negative '
               'configurations remain negative; this development data never becomes a fresh test. No model fit, GPU, '
               'reach/value/strength claim, release or arena action.'))
    print(json.dumps(dict(prepared=True,contexts=len(prior['cases']),fixture_witnesses=len(witness))),flush=True)


if __name__=='__main__':main()
