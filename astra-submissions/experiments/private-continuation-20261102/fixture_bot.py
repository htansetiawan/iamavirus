"""Deterministic protocol fixture for state-restoration tests, not a policy."""
import json
import sys

config=json.loads(sys.argv[1])
assert input()=='fow'
assert input().split()[0] in ('w','b')
print('ready',flush=True)
decision=views=0
for line in sys.stdin:
    line=line.strip()
    if len(line)==64:
        if views<len(config['views']):assert line==config['views'][views]
        views+=1
    else:
        clock=float(line)
        if decision<len(config['clocks']):assert abs(clock-config['clocks'][decision])<2e-6
        print('move '+config['moves'][decision],flush=True)
        decision+=1
