#!/usr/bin/env python3
"""Extend the frozen integration checks to both root-loss utilities."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
BASE=HERE.with_name('calibrated-root-20261101')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
provenance=json.loads((BASE/'build-provenance.json').read_text())
for name,digest in provenance['modified_sources'].items():
    assert sha(BASE/'src'/name)==digest==sha(BASE/'build/src'/name)
assert sha(BASE/'build/mist')==provenance['binary_sha256']
(HERE/'build').mkdir(exist_ok=True)
env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_'))}
sources=[HERE/'tests/test_payoff.c',BASE/'src/cfr.c']
sources += [BASE/'build/src'/f'{n}.c' for n in ('board','belief','movemodel','eval','search','front','sfeval')]
report={'scope':'Additional correctness at L=-1 and L=-2, no strength claim',
        'previous_checks_sha256':sha(BASE/'correctness.json'),
        'test_sha256':sha(HERE/'tests/test_payoff.c'),
        'source_provenance_sha256':sha(BASE/'build-provenance.json'),'checks':[]}
for sanitizer in (False,True):
    binary=HERE/'build'/('test_payoff_san' if sanitizer else 'test_payoff')
    flags=['-O1','-g','-fno-omit-frame-pointer','-fsanitize=address,undefined'] if sanitizer else ['-O2']
    cmd=['gcc','-std=c11','-pthread','-D_POSIX_C_SOURCE=199309L','-I'+str(BASE/'build/src'),*flags,*map(str,sources),'-lm','-o',str(binary)]
    built=subprocess.run(cmd,text=True,capture_output=True,env=env)
    entry={'sanitized':sanitizer,'compile_exit':built.returncode,'compile_command':cmd,'compile_output':built.stdout+built.stderr}
    if built.returncode==0:
        run=subprocess.run(['taskset','-c','0,1',str(binary)],text=True,capture_output=True,env=env)
        entry.update(exit=run.returncode,output=run.stdout+run.stderr,binary_sha256=sha(binary))
    report['checks'].append(entry)
    (HERE/'correctness.json').write_text(json.dumps(report,indent=2)+'\n')
    print('sanitized' if sanitizer else 'optimized',entry.get('exit','compile failed'),flush=True)
    if entry.get('exit',1)!=0:raise SystemExit(1)
