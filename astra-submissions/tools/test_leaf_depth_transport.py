#!/usr/bin/env python3
"""Check actual UCI depth commands and latest-depth score parsing with a fake worker."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

FAKE = '''#!/usr/bin/env python3
import os
import sys
for line in sys.stdin:
    line = line.strip()
    if line == 'uci': print('uciok', flush=True)
    elif line == 'isready': print('readyok', flush=True)
    elif line.startswith('go depth '):
        depth = int(line.split()[-1])
        with open(os.environ['DEPTH_TEST_LOG'], 'a') as f: f.write(str(depth)+'\\n')
        for d in range(1, depth+1):
            print(f'info depth {d} multipv 1 score cp {d*17} pv e2e4', flush=True)
        print('bestmove e2e4', flush=True)
    elif line == 'quit': break
'''

HARNESS = '''#include "sfeval.h"
#include <assert.h>
#include <stdio.h>
int main(int argc, char **argv) {
    assert(argc == 2); fow_init(); Position p; pos_start(&p);
    MoveList moves; generate_moves(&p, &moves);
    assert(sf_start(argv[1]));
    int cp[256], found[256];
    assert(sf_children(&p, &moves, cp, found) == 1);
    for (int i=0; i<moves.count; ++i) if (found[i]) printf("%d\\n",cp[i]);
    sf_stop(); return 0;
}
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix='astra-depth-test-') as tmp:
        work = Path(tmp)
        fake = work/'fake-sf'; fake.write_text(FAKE); fake.chmod(0o755)
        harness = work/'test.c'; harness.write_text(HARNESS)
        binary = work/'test'
        subprocess.run(['gcc','-std=c11','-O2','-I',str(args.root/'src'),
                        str(harness),str(args.root/'src/board.c'),
                        str(args.root/'src/sfeval.c'),'-lm','-o',str(binary)],check=True)
        results=[]
        for setting, expected in [(None,1),('1',1),('3',3),('4',4),('0',1),('5',1),('junk',1),('',1),('3x',1)]:
            log=work/'depth.log'; log.write_text('')
            env={**os.environ,'DEPTH_TEST_LOG':str(log),'MIST_SF_WORKERS':'1'}
            env.pop('MIST_SF_DEPTH',None)
            if setting is not None: env['MIST_SF_DEPTH']=setting
            run=subprocess.run([str(binary),str(fake)],env=env,capture_output=True,text=True,timeout=10,check=True)
            assert log.read_text().strip()==str(expected), (setting,log.read_text())
            assert run.stdout.strip()==str(expected*17), (setting,run.stdout)
            results.append({'setting':setting,'sent_depth':expected,'last_score':int(run.stdout)})
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps({'passed':len(results),'cases':results},indent=2)+'\n')
    print(f'{len(results)} UCI depth/score transport cases passed')


if __name__ == '__main__':
    main()
