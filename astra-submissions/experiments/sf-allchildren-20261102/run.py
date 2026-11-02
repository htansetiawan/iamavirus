from collections import defaultdict
from datetime import datetime, timezone
import gzip
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import select
import statistics
import subprocess
import sys
import time

from build import HERE, ROOT, OUT, RELEASE, sha, write

def now(): return datetime.now(timezone.utc).isoformat()
def salt(s):
    import hashlib
    return hashlib.sha256(s.encode()).hexdigest()
def binaries(): return {'shipped': RELEASE, 'base': HERE/'build/base/src/stockfish',
                        'off': HERE/'build/candidate/src/stockfish', 'on': HERE/'build/candidate/src/stockfish'}

class UCI:
    def __init__(self, arm, pv=256):
        e={k:v for k,v in os.environ.items() if not k.startswith(('ASTRA_', 'MIST_', 'FOW_'))}
        e['ASTRA_SF_ALLCHILDREN']='1' if arm=='on' else '0'
        self.p=subprocess.Popen([str(binaries()[arm])],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,env=e,bufsize=0)
        self.buf=b''; self.send('uci');self.until('uciok')
        self.send(f'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name MultiPV value {pv}\nisready')
        self.until('readyok')
    def send(self,s): self.p.stdin.write((s+'\n').encode());self.p.stdin.flush()
    def until(self,prefix):
        lines=[];end=time.monotonic()+15
        while True:
            while b'\n' in self.buf:
                s,self.buf=self.buf.split(b'\n',1);s=s.decode().strip();lines.append(s)
                if s.startswith(prefix):return lines
            left=end-time.monotonic()
            if left<=0 or not select.select([self.p.stdout],[],[],left)[0]:raise TimeoutError((prefix,lines))
            chunk=os.read(self.p.stdout.fileno(),65536)
            if not chunk:raise RuntimeError(('engine EOF',self.p.poll(),lines))
            self.buf+=chunk
    def reset(self): self.send('ucinewgame\nisready');self.until('readyok')
    def query(self,fen,depth=1):
        start=time.perf_counter();self.send('position fen '+fen+f'\ngo depth {depth}');lines=self.until('bestmove')
        elapsed=time.perf_counter()-start;scores={};nodes=0
        for s in lines:
            m=re.search(r'\bscore (cp|mate) (-?\d+).*?\bpv (\w+)',s)
            if m:
                kind,num,move=m.groups();num=int(num)
                cp=num if kind=='cp' else (30000 if num>0 else -30000)
                scores[move]=dict(kind=kind,raw=num,cp=cp,value=math.tanh(cp/400))
            n=re.search(r'\bnodes (\d+)',s)
            if n:nodes=int(n[1])
        return dict(scores=scores,best=lines[-1].split()[1],nodes=nodes,seconds=elapsed,lines=lines)
    def cpu(self):
        values=Path(f'/proc/{self.p.pid}/stat').read_text().split(') ',1)[1].split()
        return (int(values[11])+int(values[12]))/os.sysconf('SC_CLK_TCK')
    def close(self):
        if self.p.poll() is None:
            self.send('quit')
            try:self.p.wait(timeout=5)
            except subprocess.TimeoutExpired:self.p.kill();self.p.wait()
        assert self.p.returncode==0,self.p.returncode
        self.p.stdin.close();self.p.stdout.close()

SPECIAL={
 'start':'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
 'castle':'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1',
 'ep':'4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1',
 'promotion':'7k/P7/8/8/8/8/8/4K3 w - - 0 1',
 'check':'4r1k1/8/8/8/8/8/8/4K3 w - - 0 1',
 'mate_one':'7k/5Q2/6K1/8/8/8/8/8 w - - 0 1',
 'mate':'7k/6Q1/6K1/8/8/8/8/8 b - - 0 1',
 'stalemate':'7k/5Q2/6K1/8/8/8/8/8 b - - 0 1'}

def preflight():
    import chess
    os.sched_setaffinity(0,{0,1});records=[]
    try:
        for depth,pv in ((1,256),(2,256),(1,1)):
            engines={a:UCI(a,pv) for a in binaries()}
            try:
                for name,fen in SPECIAL.items():
                    board=chess.Board(fen);assert board.is_valid(),name
                    legal={m.uci() for m in board.legal_moves};case={}
                    for a,e in engines.items():
                        e.reset();r=e.query(fen,depth);case[a]=r
                        records.append(dict(case=name,depth=depth,multipv=pv,arm=a,**r))
                        if legal:
                            assert r['best'] in legal,(name,a,r)
                            assert set(r['scores']) <= legal
                            if pv==256:assert set(r['scores'])==legal,(name,a,legal-set(r['scores']))
                        else:
                            assert r['best']=='(none)' and not r['scores']
                            expected='score mate 0' if board.is_checkmate() else 'score cp 0'
                            assert any(expected in s for s in r['lines']),(name,a,r)
                        if name=='mate_one':assert r['scores'][r['best']]['kind']=='mate' and r['scores'][r['best']]['raw']>0
                    for a in ('shipped','off'):
                        assert all(case[a][k]==case['base'][k] for k in ('scores','best','nodes')),(name,depth,pv,a)
                    if depth!=1 or pv!=256:
                        assert all(case['on'][k]==case['base'][k] for k in ('scores','best','nodes')),(name,depth,pv,'flag leakage')
            finally:
                for e in engines.values():e.close()
        write(OUT/'preflight.json',dict(passed=True,python_chess=chess.__version__,records=records))
        print(json.dumps(dict(passed=True,calls=len(records))),flush=True)
    except BaseException as exc:
        write(OUT/'preflight-failure.json',dict(passed=False,error=repr(exc),records=records));raise

def prepare():
    import chess
    os.sched_setaffinity(0,{0,1})
    assert json.loads((OUT/'preflight.json').read_text())['passed']
    source=HERE.parent/'native-fow-value-20261102/work/dataset/rows.jsonl.gz'
    assert sha(source)==json.loads((ROOT/'astra-submissions/analysis/native-fow-value-20261102/dataset-receipt.json').read_text())['artifacts']['rows.jsonl.gz']
    by_game=defaultdict(list)
    with gzip.open(source,'rt') as f:
        for line in f:
            r=json.loads(line)
            if r['fold']=='validation':by_game[r['game']].append(r)
    path=ROOT.parent/'fow-starter/referee.py'
    spec=importlib.util.spec_from_file_location('allchild_referee',path);ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
    cases=[];skipped=[];frames=0;seen=set();pins={str(path):sha(path),str(source):sha(source)}
    for gid in sorted(by_game,key=lambda g:salt('256-game:'+g)):
        rp=ROOT/'data/raw/games'/gid/'replay.json';assert sha(rp)==by_game[gid][0]['replay_sha256']
        replay=json.loads(rp.read_text());board=ref.FowBoard();positions={}
        wanted={r['ply']-1 for r in by_game[gid]}
        for ply,frame in enumerate(replay['frames']):
            if ply:board.push_uci(frame['move'])
            actual=ref.make_frame(board,frame['clocks']);assert all(actual[k]==frame[k] for k in ('board','white','black'))
            frames+=1
            if ply in wanted:positions[ply]=board.fen(en_passant='fen')
        chosen=[]
        for r in sorted(by_game[gid],key=lambda r:salt('256-position:'+r['id'])):
            fen=positions[r['ply']-1];b=chess.Board(fen)
            if not b.is_valid() or b.legal_moves.count()<2 or fen in seen:
                skipped.append(dict(id=r['id'],fen=fen,status=int(b.status()),legal=b.legal_moves.count(),duplicate=fen in seen));continue
            chosen.append(dict(id=r['id'],game=gid,ply=r['ply']-1,fen=fen,legal=sorted(m.uci() for m in b.legal_moves),replay_sha256=sha(rp)))
            if len(chosen)==2:break
        if len(chosen)!=2:continue
        seen.update(c['fen'] for c in chosen);cases.extend(chosen);pins[str(rp)]=sha(rp)
        if len(cases)==256:break
    assert len(cases)==256 and len({c['game'] for c in cases})==128
    for p in [*HERE.glob('*.py'),HERE/'README.md',HERE/'stockfish19-allchildren.patch',OUT/'preflight.json',OUT/'provenance.json',OUT/'build.json',*binaries().values()]:pins[str(p)]=sha(p)
    write(OUT/'plan.json',dict(at=now(),cases=cases,skipped=skipped,referee_frames=frames,pins=pins,
          regimes=['cold','warm'],passes=3,arms=list(binaries()),seconds_limit=900,cores=[0,1],
          gates=dict(mae=.08,regret=.05,large_regret_rate=.01,speedup_base=1.5,speedup_shipped=1.2),
          scope='reused development played parents; all score comparison to shipped scorer, not FoW truth or strength'))
    print(json.dumps(dict(prepared=True,parents=len(cases),games=128,frames=frames,skipped=len(skipped))),flush=True)

def collect():
    plan=json.loads((OUT/'plan.json').read_text());os.sched_setaffinity(0,set(plan['cores']))
    for p,h in plan['pins'].items():assert sha(p)==h,p
    started=time.monotonic();receipt=dict(state='running',at=now(),plan_sha256=sha(OUT/'plan.json'),batches=[])
    write(OUT/'receipt.json',receipt)
    try:
        for regime in plan['regimes']:
            for rep in range(plan['passes']):
                engines={a:UCI(a) for a in plan['arms']}; rows=[]
                try:
                    for e in engines.values():e.query(SPECIAL['start']);e.reset()
                    start_cpu={a:e.cpu() for a,e in engines.items()}
                    for i,c in enumerate(plan['cases']):
                        shift=(i+rep)%4;order=plan['arms'][shift:]+plan['arms'][:shift]
                        for a in order:
                            assert time.monotonic()-started<plan['seconds_limit']
                            e=engines[a]
                            if regime=='cold':e.reset()
                            r=e.query(c['fen']);rows.append(dict(id=c['id'],game=c['game'],arm=a,**r))
                            assert set(r['scores'])==set(c['legal']) and r['best'] in c['legal'],(c['id'],a)
                        case={r['arm']:r for r in rows[-4:]}
                        for a in ('shipped','off'):
                            assert all(case[a][k]==case['base'][k] for k in ('scores','best','nodes')),(c['id'],regime,rep,a)
                    cpu={a:e.cpu()-start_cpu[a] for a,e in engines.items()}
                finally:
                    for e in engines.values():e.close()
                    # Preserve partial batches as well as successful first attempts.
                    write(OUT/f'{regime}-{rep}.json',dict(rows=rows))
                receipt['batches'].append(dict(regime=regime,rep=rep,parents=len(plan['cases']),cpu=cpu))
                print(json.dumps(receipt['batches'][-1]),flush=True)
        receipt['state']='completed'
    except BaseException as exc:receipt.update(state='failed',error=repr(exc));raise
    finally:
        receipt.update(ended_at=now(),seconds=time.monotonic()-started)
        (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')

if __name__=='__main__': {'preflight':preflight,'prepare':prepare,'collect':collect}[sys.argv[1]]()
