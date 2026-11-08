"""Two own turns per color with real Misty, after wrapper-loop conformance."""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'astra-submissions/analysis/obscuro-fidelity-20261108'
PY=Path('/home/henrytan/fable-persist/scratchpad/misty/venv/bin/python')
SF=Path('/home/henrytan/fable-persist/scratchpad/misty/bin')
sys.path[:0]=['/home/henrytan/git/fow-starter',str(ROOT/'astra-submissions/tools')]
import referee
from local_turn_control import group_members


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    os.sched_setaffinity(0,{0,1})
    for key in list(os.environ):
        if key.startswith(('MIST_','MISTY_','FOW_','ASTRA_')):
            del os.environ[key]
    os.environ.update(FOW_REQUIRE_RUST='1',FOW_V2_CLOCK_TIME='0',MISTY_BUDGET='.05',
                      MISTY_PROFILE='v1.6',FOW_SEED='2671108',OMP_NUM_THREADS='1',
                      OPENBLAS_NUM_THREADS='1',PATH=str(SF)+':'+os.environ['PATH'])
    validation=json.loads((OUT/'adapter-integration.json').read_text())
    assert validation['passed'] and validation['adapter_sha256']==sha(HERE/'misty_adapter.py')
    packages=PY.parent.parent/'lib/python3.13/site-packages'
    pins={str(p):sha(p) for p in (packages/'fow_chess').rglob('*.py')}
    pins.update({str(p):sha(p) for p in (packages/'fow_rust').rglob('*.so')})
    for p in (HERE/'misty_adapter.py',Path(referee.__file__),Path('/home/henrytan/git/fow-starter/uniform_random.py'),
              Path('/home/henrytan/fable-persist/scratchpad/misty/sf/stockfish/stockfish-linux-x86-64-universal')):
        pins[str(p)]=sha(p)
    records=[];error=None
    try:
        for side in (True,False):
            start=time.monotonic()
            bot=referee.Bot([str(PY),'-u',str(HERE/'misty_adapter.py')],side,180,2,initialization_timeout=15)
            row=dict(side='white' if side else 'black',startup_seconds=time.monotonic()-start,turns=[])
            try:
                board=referee.FowBoard();bot.observe(referee.observation(board,side),0)
                for _ in range(2):
                    if board.turn!=side:
                        moves=list(referee.fow_moves(board))
                        preferred='e2e4' if board.turn else 'e7e5'
                        other=next((m for m in moves if m.uci()==preferred),moves[0])
                        board.push(other);bot.observe(referee.observation(board,side),len(board.move_stack))
                    move,elapsed=bot.move(2)
                    assert move in {m.uci() for m in referee.fow_moves(board)} and elapsed<2
                    row['turns'].append(dict(move=move,elapsed_seconds=elapsed))
                    board.push_uci(move);bot.observe(referee.observation(board,side),len(board.move_stack))
            finally:
                bot.close()
                row.update(stderr=bot.stderr_excerpt.decode(),failure=bot.failure,
                           live_members=[r for r in group_members(bot.proc.pid) if r['state'] not in ('Z','X')])
                records.append(row)
            assert not row['live_members'] and row['failure'] is None
            assert 'inadmissible engine move' not in row['stderr']
        for path,value in pins.items():assert sha(path)==value,path
    except BaseException as exc:
        error=repr(exc);raise
    finally:
        result=dict(at=datetime.now(timezone.utc).isoformat(),passed=error is None,
                    error=error,records=records,dependencies=pins,
                    scope='Real installed Misty 0.1.3, v1.6 profile; strict Rust requirement, '
                    '50ms configured search, two-second turn probes, both colors. '
                    'Protocol and wrapper integration only, not strength or Obscuro.')
        with (OUT/'adapter-smoke.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
        print(json.dumps({k:v for k,v in result.items() if k!='dependencies'}),flush=True)


if __name__=='__main__': main()
