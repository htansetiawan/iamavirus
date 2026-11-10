"""Re-read the four original protocol receipts; do not rerun their bots."""
import json
from pathlib import Path

from check import OUT, ROOT, SHIP, now, save, sha

def main():
    plan=json.loads((OUT/'plan.json').read_text())
    result=json.loads((OUT/'result.json').read_text())
    assert result['passed'] and result['cleanup_verified']
    assert result['plan_sha256']==sha(OUT/'plan.json')
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    assert [r['case'] for r in result['cases']]==plan['cases']
    root=Path(plan['private_store']);checked=[]
    for row in result['cases']:
        raw=root/row['case']/'game.json';assert sha(raw)==row['source_sha256']
        game=json.loads(raw.read_text());events=game['protocol']['events']
        assert game['localNativeStockfishReadiness']==row['checks']
        assert game['result']==row['result'] and len(game['frames'])-1==row['plies']
        assert game['frames'][0]['clocks']==[3.,3.] and not game['protocol']['truncated']
        obs=[e for e in events if e['direction']=='input' and len(e['text'])==64]
        moves=[e for e in events if e['direction']=='output' and e['text'].startswith('move ')]
        if row['case']=='healthy':
            # The freezer buffers Black's view until its turn, which never
            # starts in a one-ply smoke test.
            assert len(obs)==len(moves)==1
            assert obs[0]['side']==moves[0]['side']=='white'
            assert obs[0]['text']==game['frames'][0]['white']
            assert moves[0]['text']=='move '+game['frames'][1]['move']
        else:
            assert not obs and not moves and game['result']=='*' and not game.get('failedSide')
            assert all(e['text'] in ('fow','w 3 0','b 3 0','ready') for e in events)
        checked.append(dict(case=row['case'],observations=len(obs),moves=len(moves),sha256=sha(raw)))
    for name in ('mist','run.sh'):
        assert sha(root/'fallback'/name)==sha(root/'absent'/name)==sha(SHIP/name)
    assert (root/'fallback/bin/stockfish').read_text()=='#!/bin/sh\nexit 127\n'
    assert not (root/'absent/bin/stockfish').exists()
    lease=json.loads((ROOT/'chatroom/cores.json').read_text())
    assert not any(r['owner']=='astra-native-stockfish-precheck-20261110' for r in lease['allocation'])
    teacher=json.loads((OUT.parent/'prospective-quiet-teacher-20261110/plan.json').read_text())
    for p,h in teacher['dependencies'].items():assert sha(p)==h,p
    receipt=dict(at=now(),original_session=68524,terminal_exit_code=0,
        source_publication='5427b3f498df6e6b569afc87e539f6ab11c55b96',both_mirrors_verified_before_execution=True,
        smoke_cases=4,failed_backends_rejected_before_play=3,healthy_legal_plies=1,independent_receipts=checked,
        source_pins_unchanged=len(plan['dependencies']),teacher_pins_unchanged=len(teacher['dependencies']),
        cleanup_verified=True,plan_sha256=sha(OUT/'plan.json'),result_sha256=sha(OUT/'result.json'),
        audit_correction='Initial post-run audit expected both views delivered on ply zero; the pinned turn controller buffers Black until its turn. Verified one delivered White observation and no rerun.',
        scope='Native-v38 local startup acceptance only. No old attempt replay, root cause or playing-strength result.')
    save(OUT/'terminal-verification.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k!='independent_receipts'}),flush=True)

if __name__=='__main__':main()
