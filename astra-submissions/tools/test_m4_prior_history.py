#!/usr/bin/env python3
"""A replayed en-passant action needs history, not the single-view move list."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

ap=argparse.ArgumentParser()
ap.add_argument('--runner',type=Path,required=True)
ap.add_argument('--input',type=Path,required=True)
args=ap.parse_args()
env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','M4SF_'))}
env['MIST_MODEL']='0'
with tempfile.TemporaryDirectory(prefix='m4-history-') as folder:
    root=Path(folder);model=root/'unused.txt';model.write_text('26\n'+' '.join(['0']*26)+'\n')
    def run(path):
        return subprocess.run([str(args.runner.resolve()),str(path.resolve()),str(model),'10000','41'],
                              capture_output=True,text=True,env=env,timeout=30)
    good=run(args.input);assert good.returncode==0,good.stderr
    rows=[json.loads(line) for line in good.stdout.splitlines()]
    assert rows[-1]['game']=='28ddn2g7' and rows[-1]['move']=='f5g6' and rows[-1]['ply']==12
    assert rows[-1]['worlds']==1576 and rows[-1]['truth_present']==1
    assert 'proven in all 1576 belief worlds' in good.stderr
    assert all(not r['inconsistent'] and not r['full_calls'] and not r['cheap_calls'] for r in rows)
    bad_path=root/'bad.txt';source=args.input.read_text();assert source.count('f5g6 ')==1
    bad_path.write_text(source.replace('f5g6 ','f5e6 '));bad=run(bad_path)
    assert bad.returncode==3 and 'not observation-legal' in bad.stderr
    print(json.dumps(dict(valid_history_move='f5g6',support=1576,invalid_move='f5e6',rejected=True,rows=len(rows))))
