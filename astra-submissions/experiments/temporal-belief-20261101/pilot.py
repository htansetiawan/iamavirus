#!/usr/bin/env python3
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
    out=Path(sys.argv[1]);plan=json.loads((out/'plan.json').read_text());case=plan['cases'][0];dest=out/'pilot';dest.mkdir(exist_ok=False)
    base={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
    base.update(MIST_MODEL_TEMP='2',MIST_THREADS='2',MIST_MODEL_FULL_BELOW='1000000000')
    report={'case':case['id'],'max_ply':16,'arms':{}}
    for arm,settings in plan['arms'].items():
        runs=[]
        for redact in [False,True]:
            path=dest/f'{arm}-{int(redact)}.json'
            cmd=[sys.executable,str(ROOT/'trace.py'),'--input',str(out/(case['id']+'.input.json')),
                 '--truth',str(out/(case['id']+'.truth.json')),'--out',str(path),'--max-ply','16']
            if redact:cmd.append('--redact-truth')
            r=subprocess.run(cmd,env=base|settings,capture_output=True,text=True,timeout=120)
            if r.returncode:raise RuntimeError(r.stderr)
            runs.append(json.loads(path.read_text()))
        a,b=runs
        assert [x['checksum'] for x in a['updates']]==[x['checksum'] for x in b['updates']]
        assert [x['king_risk'] for x in a['decisions']]==[x['king_risk'] for x in b['decisions']]
        assert all(x['truth_share']==0 for x in b['decisions'])
        report['arms'][arm]={'updates':len(a['updates']),'decisions':len(a['decisions']),
                             'seconds':a['total_update_seconds'],'max_worlds':max(x['worlds'] for x in a['decisions']),
                             'truth_redaction_checksums_identical':True,'truth_redaction_risks_identical':True,
                             'truth_present_on_all_pilot_decisions':all(x['truth_share']>0 for x in a['decisions'])}
    report['library_sha256']=hashlib.sha256((ROOT/'build/libtemporal.so').read_bytes()).hexdigest()
    (out/'private-input-pilot.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
