"""Verify the preserved first21 native rows; never compile or invoke the probe."""
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/promotion-ledger-20261110'
spec=importlib.util.spec_from_file_location('ledger_reference',HERE/'check.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    reporter=json.loads((OUT/'reporter-failure.json').read_text())
    assert sha(OUT/'probe.stdout')==reporter['native_stdout_sha256']
    fixtures=json.loads((OUT/'fixtures.json').read_text())
    native=[json.loads(s) for s in (OUT/'probe.stdout').read_text().splitlines()]
    assert len(native)==len(fixtures['cases'])==21 and fixtures['threshold']==4
    results=[]
    for i,(f,n) in enumerate(zip(fixtures['cases'],native)):
        us=f['board'][m.ref.chess.parse_square(f['move'][:2])].isupper()
        pieces={m.ref.chess.square_name(s):c for s,c in enumerate(f['board']) if c!='-'}
        board=m.position(pieces,us)
        assert m.reference(board,f['move'])==f['reference']
        assert n['case']==i and n['ledger']==[f['reference']['risk']]*2
        results.append(dict(**f,**n))
    mismatches=lambda key:[r['name'] for r in results if r[key]!=[r['reference']['risk']]*2]
    assert set(mismatches('root_credit'))=={'both-promotions-without-recapture','opponent-promotion-after-our-queen-capture'}
    assert len(mismatches('old'))==7
    ordinary=[r for r in results if r['name'].startswith('ordinary-')]
    assert all(r['old']==r['ledger']==[1.,1.] for r in ordinary)
    fp=[r['name'] for r in results if r['old']==[1.,1.] and r['ledger']==[0.,0.]]
    fn=[r['name'] for r in results if r['old']==[0.,0.] and r['ledger']==[1.,1.]]
    result=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,cases=21,
        all_corrected_risks_match_exact_course_material_ledger=True,ordinary_queen_loss_controls_stay_positive=True,
        original_false_positives=fp,original_false_negatives=fn,root_credit_mismatches=mismatches('root_credit'),
        native_probe_runs=1,review_only_after_reporter_field_fix=True,results=results,
        scope='Promotion material bookkeeping correctness on21 fixtures. No policy, learning, posterior, replay-strength or global guard-correctness claim.',
        limitations=['Original terminal/recapture feasibility approximations stay unchanged.','The incomplete root-only correction is rejected for use; both promotion increments and recapture value are required.','Queen promotion still permits the recorded guarded Qg8 net; this is not a fix for that loss or an arena-strength result.'],
        source_hashes={str(p):sha(p) for p in [Path(__file__),HERE/'check.py',HERE/'bridge.c',HERE/'promotion-ledger.patch.gz',HERE/'build/probe',OUT/'probe.stdout',OUT/'fixtures.json',m.ROOT.parent/'fow-starter/referee.py']})
    with (OUT/'result.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['results','source_hashes']},indent=2))


if __name__=='__main__':main()
