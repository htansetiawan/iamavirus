#!/usr/bin/env python3
"""Observable clock and child-process invariants; no chess strength claims."""
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

from local_turn_control import ProcessGroupControl, cleanup_registry, group_members, run_controlled


def main():
    kit=Path.home()/'git/fow-starter'
    sys.path.insert(0,str(kit))
    import referee
    with tempfile.TemporaryDirectory(prefix='astra-turn-test-') as directory:
        root=Path(directory)
        ticker=root/'ticker.py'
        ticker.write_text('''import os,sys,time
from pathlib import Path
child=os.fork()
path=Path(sys.argv[1])/('child' if child==0 else 'parent')
n=0
while True:
 n+=1;path.write_text(str(n));time.sleep(.005)
''')
        proc=subprocess.Popen([sys.executable,str(ticker),str(root)],start_new_session=True)
        try:
            for _ in range(100):
                if (root/'child').exists() and (root/'parent').exists():break
                time.sleep(.01)
            else:raise AssertionError('Counter processes did not start')
            control=ProcessGroupControl(proc)
            control.freeze()
            counts=[(root/name).read_bytes() for name in ('parent','child')]
            time.sleep(.08)
            assert counts==[(root/name).read_bytes() for name in ('parent','child')]
            assert len([r for r in group_members(proc.pid) if r['state']=='T'])==2
            control.resume();time.sleep(.08)
            assert all((root/name).read_bytes()!=before for name,before in zip(('parent','child'),counts))
            control.freeze()
            # A referee can die after a bot leader exits but before its child.
            # The registry must clean an observed child, and reject stale IDs.
            registry=root/'orphan-registry.json'
            record=control.record()
            proc.kill();proc.wait(timeout=2)
            wrong=json.loads(json.dumps(record))
            for item in [wrong['leader'],*wrong['members']]:item['starttime']+=1
            registry.write_text(json.dumps([wrong]))
            assert cleanup_registry(registry)==[proc.pid]
            assert any(r['state']=='T' for r in group_members(proc.pid))
            registry.write_text(json.dumps([record]))
            assert cleanup_registry(registry)==[]
            for _ in range(100):
                if not [r for r in group_members(proc.pid) if r['state'] not in ('Z','X')]:break
                time.sleep(.005)
            else:raise AssertionError('Recorded child survived cleanup')
        finally:
            import os
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            proc.wait(timeout=2)
        bot=root/'bot.py'
        bot.write_text('''import sys,time
assert input()=='fow'
side=input().split()[0]
print('ready',flush=True)
for line in sys.stdin:
 if len(line.strip())==64:
  time.sleep(.06) # stand-in for observation/hidden-state processing
 else:
  print('move '+('e2e4' if side=='w' else 'e7e5'),flush=True)
''')
        argv=[sys.executable,str(bot)]
        game=run_controlled(referee,argv,argv,base=2,increment=0,max_plies=2,registry_path=root/'registry.json')
        assert game['reason']=='Move limit reached',game['reason']
        frames=game['frames']
        white=2-frames[1]['clocks'][0];black=2-frames[2]['clocks'][1]
        assert .055<=white<1.0,white
        assert .115<=black<1.0,black
        assert len(game['localTurnControl']['controls'])==2
        for c in game['localTurnControl']['controls']:
            assert sum(e['op']=='freeze' for e in c['events'])>=2
            assert not [r for r in group_members(c['pid']) if r['state'] not in ('Z','X')]
        assert referee.Bot.__name__=='Bot'
        plain=referee.run_match(argv,argv,base=2,increment=0,max_plies=2)
        plain_black=2-plain['frames'][2]['clocks'][1]
        assert black-plain_black>.04,(black,plain_black)
        negative={}
        for mode in ('exit','timeout'):
            bad=root/f'{mode}.py'
            bad.write_text('import sys,time\ninput();input();print("ready",flush=True)\n'
                           'for line in sys.stdin:\n'
                           ' if len(line.strip())!=64:\n'
                           +('  sys.exit(0)\n' if mode=='exit' else '  time.sleep(2)\n'))
            result=run_controlled(referee,[sys.executable,str(bad)],argv,
                                  base=.3,increment=0,max_plies=2,registry_path=root/'registry.json')
            assert result['result']=='0-1',result
            assert result['failedSide']=='white',result
            assert 'Infrastructure' not in result['reason'],result
            assert cleanup_registry(root/'registry.json')==[]
            for c in result['localTurnControl']['controls']:
                assert not [r for r in group_members(c['pid']) if r['state'] not in ('Z','X')]
            negative[mode]=result['reason']
        # More than the referee's default rolling tail, but under its budget.
        # Retaining diagnostics must not relax total-output/line warnings.
        capture_class=referee.StderrCapture
        noisy=root/'noisy.py'
        noisy.write_text('import sys\ninput();side=input().split()[0]\n'
                         'sys.stderr.write("BEGIN\\n"+"abcdefghij\\n"*2200+"END\\n");sys.stderr.flush()\n'
                         'print("ready",flush=True)\n'
                         'for line in sys.stdin:\n'
                         ' if len(line.strip())!=64:print("move "+("e2e4" if side=="w" else "e7e5"),flush=True)\n')
        bounded=run_controlled(referee,[sys.executable,str(noisy)],argv,
                              base=2,increment=0,max_plies=2,retain_stderr=True)
        captured=bounded['privateDiagnostics']['white']
        assert captured.startswith('BEGIN\n') and captured.endswith('END\n')
        assert len(captured)>16384 and not bounded.get('warnings')
        assert bounded['localTurnControl']['stderr_retained_bytes']==capture_class.LIMIT
        assert referee.StderrCapture is capture_class and referee.Bot.__name__=='Bot'
        # A line exceeding the original line budget still causes a warning.
        noisy.write_text(noisy.read_text().replace('"abcdefghij\\n"*2200','"x"*5000'))
        excess=run_controlled(referee,[sys.executable,str(noisy)],argv,
                             base=2,increment=0,max_plies=2,retain_stderr=True)
        assert {'side':'white','code':'stderr_limit'} in excess['warnings']
        print(json.dumps({'result':'passed','child_and_parent_counters_frozen':True,
            'leaderless_child_cleaned':True,'stale_registry_refused':True,
            'white_charged_one_observation_seconds':white,'black_charged_two_observations_seconds':black,
            'uncontrolled_black_clock_seconds':plain_black,'negative_cases':negative,
            'bot_groups_cleaned':True,'complete_bounded_stderr_bytes':len(captured),
            'original_line_limit_preserved':True,'capture_class_restored':True,
            'referee_sha_scope':'unmodified imported referee'}))


if __name__=='__main__':main()
