"""Check exact states, default averages, explicit API refusal and source scope."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
OUT=ROOT/'astra-submissions/analysis/last-only-cfr-20261110'
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    plan=json.loads((OUT/'plan.json').read_text());execution=json.loads((OUT/'execution.json').read_text())
    for path,value in plan['dependencies'].items():assert sha(path)==value,path
    assert execution['status']=='complete' and len(execution['calls'])==6 and execution['restarted'] is False
    records=[]
    for call in execution['calls']:
        name=call['name'];assert call['code']==call['expected']
        stdout=(OUT/f'{name}.stdout').read_text();stderr=(OUT/f'{name}.stderr').read_text()
        assert sha(OUT/f'{name}.stdout')==call['stdout_sha256'] and sha(OUT/f'{name}.stderr')==call['stderr_sha256']
        if name.startswith('check-'):
            result=json.loads(stdout);mode=int(name.split('-')[1]);assert result['last_only']==bool(mode) and result['passed']
            assert result['bit_identical_checkpoints']==9569 and result['iterations']==8193 and result['large_actions']==257
            assert result['growing_tree'] is result['pending_without_growth'] is True
            assert result['compared_doubles']==6263272
            clears=re.fullmatch(r'stale predictions cleared: (\d+)\n',stderr);assert clears and int(clears[1])>=496
            records.append(dict(name=name,checkpoints=9569,meaningful_compared_doubles=6263272 if not mode else 4697454,stale_prediction_clears=int(clears[1]),average_tested=not bool(mode),average_omitted=bool(mode)))
        elif name=='average-api-0':assert not stdout and not stderr
        else:assert not stdout and stderr=='pcfr_average is unavailable in a last-iterate-only build\n' and call['code']==-6
    for name in ('cfr.c','cfr.h'):
        assert (HERE/f'candidate-{name}').read_bytes()==(HERE/'build/fast'/name).read_bytes()
        assert (HERE/f'reference-{name}').read_bytes()==(HERE/'build/base'/name).read_bytes()
    # Last-iterate API check on the current deployed consumer, not only tests.
    ship=Path(plan['ship']);consumers=[]
    for path in sorted((ship/'src').glob('*.c')):
        if path.name!='cfr.c':assert 'strategy_sum' not in path.read_text() and 'pcfr_average' not in path.read_text()
        consumers.append(path.name)
    for name in ('prospective-quiet-teacher-20261110','move-metadata-recovery-20261110'):
        other=json.loads((ROOT/'astra-submissions/analysis'/name/'plan.json').read_text())
        for path,value in other['dependencies'].items():assert sha(path)==value,path
    report=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,checks=records,ndebug_average_api_default_passed=True,ndebug_last_only_misuse_rejected=True,consumer_files_checked=consumers,source_pins=len(plan['dependencies']),teacher_and_metadata_pins_unchanged=True,source_change='Reuse253/254 cached/selective solver; separate compile-time mode omits only unconsumed average buffer/allocation/scan. Generic averaging stays enabled by default.',scope='Correctness only. Last-only meaningful comparisons exclude the intentional dummy average quarter; regrets/predictions/current strategy remain bit-identical. No kernel/equal-clock timing, inferred node gain, playing test, model, ZIP/version or arena change.254 advancement failure remains failed.')
    (OUT/'independent-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
