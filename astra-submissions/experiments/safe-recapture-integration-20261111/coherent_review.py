"""Read-only review of the coherent patch and its saved component results."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/safe-recapture-integration-20261111'
ENGINE=ROOT.parent/'fowsearch-c'


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    plan=json.loads((OUT/'coherent-plan.json').read_text())
    result=json.loads((OUT/'coherent-result.json').read_text())
    assert result['passed'] and sha((HERE/'coherent_check.py').read_bytes())==plan['runner_sha256']
    for p,v in plan['pins'].items():assert sha((ROOT/p).read_bytes())==v,p
    original=(ENGINE/'src/main.c').read_bytes()
    patchgzip=(HERE/'current-source-coherent.patch.gz').read_bytes();patch=gzip.decompress(patchgzip)
    assert sha(patch)==result['patch_sha256'] and sha(patchgzip)==result['gzip_sha256']
    with tempfile.TemporaryDirectory(dir=HERE/'build') as d:
        p=Path(d);(p/'src').mkdir();(p/'src/main.c').write_bytes(original)
        proc=subprocess.run(['patch','--batch','--fuzz=0','-p1'],input=patch,cwd=p,capture_output=True,timeout=10)
        assert proc.returncode==0 and b'fuzz' not in proc.stdout
        amended=(p/'src/main.c').read_bytes();assert sha(amended)==result['amended_main_sha256']
        helper=(ROOT/'astra-submissions/experiments/safe-recapture-20261111/safe_recapture.h').read_bytes().split(b'/* Independent native enumeration')[0].rstrip()+b'\n'
        assert amended.count(helper+b'\n')==1
        source=amended.replace(helper+b'\n',b'',1)
        a=b'if (is_attacked(&q, sq, us) && astra_safe_recapture(&q, sq)) gain -='
        b=b'if (is_attacked(&q, sq, us)) gain -='
        c=b'if (is_attacked(&q, sq, us) && (p->piece[sq] != QUEEN || astra_safe_recapture(&q, sq))) gain -='
        assert source.count(a)==source.count(c)==1
        assert source.replace(a,b,1).replace(c,b,1)==original
    tree=HERE/'build/coherent'
    for p,v in plan['engine_sources'].items():
        assert sha((ENGINE/p).read_bytes())==v
        assert sha((tree/p).read_bytes())==(result['amended_main_sha256'] if p=='src/main.c' else v)
    commands=[json.loads(l) for l in (OUT/'coherent-commands.jsonl').read_text().splitlines()]
    assert len(commands)==len({c['label'] for c in commands})==27 and all(c['exit_code']==0 for c in commands)
    assert commands[0]['stdout'].strip()=='build: done (gcc)'
    assert not any(Path(c['argv'][0]).name.startswith(('mist','stockfish')) for c in commands)
    baseline=json.loads((OUT/'result.json').read_text())['runs'][0]['rows']
    negative=json.loads((OUT/'partition-result.json').read_text())
    assert not negative['queen_only_patch_preserves_composite_partition'] and negative['rows'][0]['combined']>1
    for arm in result['outputs']:
        suffix=arm['compiler']
        actual=[json.loads(l) for l in next(c for c in commands if c['label']=='probe-'+suffix)['stdout'].splitlines()]
        pair=[json.loads(l) for l in next(c for c in commands if c['label']=='partition-'+suffix)['stdout'].splitlines()]
        assert actual==arm['rows']==baseline and len(actual)==26
        assert pair==arm['partition_rows'] and len(pair)==2
        assert [(p['queen_amended'],p['piece_unchanged']) for p in pair]==[(1,0),(0,1)]
        assert [p['combined'] for p in pair]==[.9,.758]
    # Source checks establish that every component input also exercised per-world
    # overlap rejection and nonqueen old/new net equality before printing a row.
    probe=(tree/'src/probe.c').read_text()
    assert 'if(q>0 && p>0)return 7;' in probe
    assert '!=astra_original_best_capture_net(' in probe and 'return 8;' in probe
    r=dict(passed=True,source_pins=len(plan['pins']),shared_native_sources_unchanged=len(plan['engine_sources']),
           strict_patch_application=True,production_difference='Unchanged helper plus two recapture predicates; queen targets only in generic helper.',
           compiler_paths=3,queen_case_results_checked=78,partition_results_checked=6,
           per_world_overlap_and_nonqueen_parity_checks_exercised=True,
           preserved_partial_counterexample=True,policy_or_backend_runs=0,
           source_sha256=sha(Path(__file__).read_bytes()),result_sha256=sha((OUT/'coherent-result.json').read_bytes()),
           scope='Component and source review; neither whole-engine strength nor broader material-risk correctness is established.')
    with (OUT/'coherent-review.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
    print(json.dumps(r))


if __name__=='__main__':main()
