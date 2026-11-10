"""Separate private-action observation join, reusing288 as development only."""
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/private-action-join-20261110';BUILD=HERE/'build'
OLD=HERE.parent/'past-alias-20261110';OLDOUT=ROOT/'astra-submissions/analysis/past-alias-20261110'
STORE=Path('/media/henrytan/seagate/iamavirus/astra/private-action-join-20261110')
spec=importlib.util.spec_from_file_location('old_past_alias_helpers',OLD/'prepare.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
sha,write,position,text,line=old.sha,old.write,old.position,old.text,old.line
sys.path.insert(0,str(ROOT.parent/'fow-starter'))
import referee as ref


def main():
    OUT.mkdir(exist_ok=False);BUILD.mkdir(exist_ok=False)
    prior=json.loads((OLDOUT/'plan.json').read_text());assert json.loads((OLDOUT/'audit.json').read_text())['validated_witnesses']==0
    source=Path(json.loads(old.PRIOR.read_text())['parent'])/'src'
    commands=[]
    for name,flags in [('mine',['-O2','-Wall','-Wextra']),('mine-sanitize',['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
        cmd=['gcc','-std=c11',*flags,'-I',str(source),str(HERE/'mine.c'),str(source/'board.c'),'-o',str(BUILD/name)]
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=60);assert r.returncode==0,r.stderr
        commands.append(dict(command=cmd,stderr=r.stderr))
    toy=ref.FowBoard(None)
    for sq,piece in {'h1':'K','a1':'R','e2':'B','e8':'k','a7':'p'}.items():
        toy.set_piece_at(ref.chess.parse_square(sq),ref.chess.Piece.from_symbol(piece))
    toy.turn=True;toy.castling_rights=0
    fixture=line(position(toy),'a1e1','a7a6')+'\n';outputs=[]
    for binary in ['mine','mine-sanitize']:
        r=subprocess.run([str(BUILD/binary)],input=fixture,capture_output=True,text=True,timeout=20)
        assert r.returncode==0,r.stderr;outputs.append(r.stdout)
    assert outputs[0]==outputs[1]
    witness=[json.loads(s) for s in outputs[0].splitlines() if json.loads(s)['kind']=='witness']
    wanted=next(r for r in witness if r['alternative_previous']=='a1f1' and r['actual_danger']==1 and r['alternative_danger']==0
                and r['actual_current_move']!=r['alternative_current_move'])
    reply=next(r for r in wanted['replies'] if r['uci']=='a6a5');assert reply['actual_safe']==0 and reply['alternative_safe']==1
    (OUT/'fixture-input.txt').write_text(fixture);(OUT/'fixture-output.jsonl').write_text(outputs[0])
    (OUT/'input.txt').write_bytes((OLDOUT/'input.txt').read_bytes())
    write(OUT/'preflight.json',dict(at=datetime.now(timezone.utc).isoformat(),passed=True,commands=commands,
          sanitized_equal=True,different_current_action_fixture=wanted,fixture_witnesses=len(witness),
          scope='Synthetic oracle fixture; current action equality is NOT required. Not a corpus or playing result.'))
    deps=[Path(__file__),HERE/'mine.c',HERE/'run.py',HERE/'audit.py',OLD/'mine.c',OLD/'prepare.py',BUILD/'mine',
          OLDOUT/'plan.json',OLDOUT/'audit.json',OLDOUT/'input.txt',OUT/'input.txt',source/'board.c',source/'fow.h',Path(ref.__file__)]
    deps+=[Path(c['replay_path']) for c in prior['cases']]
    write(OUT/'plan.json',dict(at=datetime.now(timezone.utc).isoformat(),cases=prior['cases'],core=6,process_seconds=120,
          output_limit=512*1024*1024,bulk_store=str(STORE),dependencies={str(p):sha(p) for p in deps},
          method='OFFLINE ORACLE on288 reused development contexts. Past own-action alternatives keep both opponent views '
                 'and its recorded own reply equal. Current actions may differ, including hidden moving piece type; join by '
                 'opponent observation and equal reply-action row, then require different king danger and reply safety. '
                 'Canonical immediate-royal-consequence classes compress diagnostic output only, not a playing game tree.',
          complexity='Compute each child/reply-safety row once. Hash observation/legal-row/signature classes; opposite-danger '
                     'join is expected output-sensitive O(A+B+M), after O((A+B)*reply tests), not a claimed worst-case linear '
                     'enumeration of all state/action pairs. Full equality checks resolve hash collisions.',
          criteria='Independent complete-prefix/path/view and all-reply validation; draw/repetition exclusions recorded. '
                   'At least12 individually escapable witnesses across4 games permits a private-input producer design only. '
                   'Report local empty-safe-intersection cases, actual representative action hits and all exclusions. '
                   'No reach weights, current belief coverage, value gain or Elo are established.',
          comparison='288 remains negative: requiring the same next UCI token and piece type found zero royal witnesses. '
                     'This is a changed private-action interface on the same DEVELOPMENT data, never a new test/pass of288. '
                     'Prior M4 and062/251/DBR results remain unchanged; no match, model fit or arena action.'))
    print(json.dumps(dict(prepared=True,contexts=len(prior['cases']),fixture_witnesses=len(witness))),flush=True)


if __name__=='__main__':main()
