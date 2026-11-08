"""Check the actual adapter's protocol loop with a spy on every recorded turn.

The spy validates inputs and returns recorded own moves. It is a test double,
not a new game or Misty strength result. Real-engine smokes are separate.
"""
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import chess

ROOT = Path(__file__).resolve().parents[3]
GATE = ROOT/'astra-submissions/analysis/sf-opponent-20261108'
OUT = ROOT/'astra-submissions/analysis/obscuro-fidelity-20261108'
HERE = Path(__file__).resolve().parent
sys.path.insert(0, '/home/henrytan/git/fow-starter')
import referee


def main():
    results = []
    plan = json.loads((GATE/'plan.json').read_text())
    for job in plan['jobs']:
        path = GATE/'jobs'/job['id']/'replay.json'
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        side = 'black' if job['side']=='white' else 'white'
        color = side=='white'
        board = referee.FowBoard()
        feed = ['fow', ('w' if color else 'b')+' 180 2']
        expected = []
        for index, frame in enumerate(data['frames'][:-1]):
            if frame['move']:
                board.push_uci(frame['move'])
            feed.append(frame[side])
            if board.turn == color:
                feed.append(str(frame['clocks'][0 if color else 1]))
                expected.append((set(m.uci() for m in referee.fow_moves(board)),
                                 data['frames'][index+1]['move']))
        class Spy:
            def __init__(self): self.index=0
            def reset(self, given): assert given==color
            def observe_own_move(self,*args): pass
            def observe_opp_move(self,*args): pass
            def pick_move(self,view):
                legal, move = expected[self.index]
                assert {m.uci() for m in view.own_legal_moves} == legal, (job['id'],self.index)
                self.index+=1
                return chess.Move.from_uci(move)
        spy=Spy()
        modules={name:ModuleType(name) for name in ('fow_chess','fow_chess.engine_profile',
                 'fow_chess.observation','fow_chess.selfplay','fow_chess.engine_v2')}
        modules['fow_chess.engine_profile'].PROFILES={'v1.6':SimpleNamespace(build_strategy=lambda **kw:spy)}
        modules['fow_chess.observation'].Observation=SimpleNamespace
        modules['fow_chess.selfplay'].PerspectiveView=SimpleNamespace
        modules['fow_chess'].engine_v2=modules['fow_chess.engine_v2']
        stdout,stderr=io.StringIO(),io.StringIO()
        with patch.dict(sys.modules,modules), patch.object(sys,'stdin',io.StringIO('\n'.join(feed)+'\n')), \
                contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr), \
                patch.dict('os.environ',{'MISTY_PROFILE':'v1.6'}):
            spec=importlib.util.spec_from_file_location('adapter_under_test',HERE/'misty_adapter.py')
            adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
            adapter.main()
        assert spy.index==len(expected) and not stderr.getvalue()
        assert stdout.getvalue().splitlines()==['ready']+['move '+m for _,m in expected]
        results.append(dict(job=job['id'],turns=len(expected),passed=True))
    assert len(results)==29
    result=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,games=len(results),
                turns=sum(r['turns'] for r in results),rows=results,
                adapter_sha256=hashlib.sha256((HERE/'misty_adapter.py').read_bytes()).hexdigest(),
                scope='Actual adapter loop with spy policy, all completed Misty moves; '
                'one unanswered timeout turn omitted. No hidden state sent to adapter; '
                'truth legal sets used only by the test spy. Not an actor or strength test.')
    with (OUT/'adapter-integration.json').open('x') as f:
        json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__ == '__main__':
    main()
