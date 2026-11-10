"""Both-color protocol/legality checks for all compiler paths; no playing score."""
from datetime import datetime,timezone
import hashlib,importlib.util,json,os
from pathlib import Path
import subprocess,sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/last-only-pilot-20261110'

def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def main():
 build=json.loads((OUT/'build.json').read_text())
 for path,value in build['dependencies'].items():assert sha(path)==value,path
 sys.path.insert(0,str(HERE/'build'));import referee as ref
 os.sched_setaffinity(0,{0,1});rows=[];ship=HERE/'build/base'
 binaries=[('baseline',ship/'mist'),('candidate-gcc',HERE/'build/candidate/mist'),('candidate-gpp-c',HERE/'build/compiler-checks/gpp-c'),('candidate-gpp-cpp',HERE/'build/compiler-checks/gpp-cpp')]
 for name,binary in binaries:
  for side in (0,1):
   board=ref.FowBoard();key=side==0;feed=['fow',('w' if key else 'b')+' 180 2',ref.observation(board,key)]
   if side:board.push_uci('d2d4');feed.append(ref.observation(board,key))
   feed.append('180')
   env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_'))}
   env.update(MIST_STOCKFISH=str((ship/'bin/stockfish').resolve()),MIST_HISTORY_TABLE=str((ship/'data/history.bin').resolve()),ASTRA_SF_ALLCHILDREN='1',MIST_MAX_SECONDS='.1',FOW_SEED='3321110')
   result=subprocess.run([str(binary)],input='\n'.join(feed)+'\n',capture_output=True,text=True,env=env,timeout=60)
   rows.append(dict(name=name,side=side,code=result.returncode,stdout=result.stdout,stderr=result.stderr))
   assert result.returncode==0 and result.stdout.splitlines()[0]=='ready'
   moves=[line[5:] for line in result.stdout.splitlines() if line.startswith('move ')]
   assert len(moves)==1 and ref.chess.Move.from_uci(moves[0]) in ref.fow_moves(board)
   assert 'mist: stockfish ready' in result.stderr and 'astra-three' not in result.stderr and 'astra-solver-pair' not in result.stderr
 output=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,calls=8,compiler_paths=3,rows=rows,source_and_binary_pins_unchanged=True,no_game_score_or_strength_claim=True)
 (OUT/'preflight.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({k:v for k,v in output.items() if k!='rows'}))

if __name__=='__main__':main()
