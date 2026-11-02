#!/usr/bin/env python3
"""Compare the paired-bootstrap convolution with exhaustive small resamples."""
import hashlib
import itertools
import json
import math
from pathlib import Path
from run import OUT, pair_interval


def brute(panels):
    totals=[0.]
    for panel in panels:
        draws=[sum(x) for x in itertools.product(panel,repeat=len(panel))]
        totals=[a+b for a in totals for b in draws]
    games=2*sum(map(len,panels));scores=sorted(x/games for x in totals)
    return [scores[math.ceil(q*len(scores))-1] for q in (.025,.975)]


if __name__=='__main__':
    cases=[[[0,0],[0,0]],[[2,2],[2,2]],[[1,1],[1,1]],
           [[0,2],[.5,1.5]],[[0,1,2],[.5,1.5]],[[2,2,1],[0,.5,1]],
           [[.5,1,1.5],[0,2]],[[1.5],[.5]]]
    rows=[]
    for panels in cases:
        expected=brute(panels);actual=pair_interval(panels)
        assert actual==expected,(panels,actual,expected)
        rows.append(dict(pair_points=panels,expected=expected,actual=actual))
    # A deterministic one-win/one-loss pair resamples to exactly 50%, not
    # the wide interval produced by treating its two games independently.
    assert pair_interval([[1]*16,[1]*16])==[.5,.5]
    result=dict(scope='Arithmetic checks only; no playing-strength evidence',
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                runner_sha256=hashlib.sha256(Path(__file__).with_name('run.py').read_bytes()).hexdigest(),
                exhaustive_cases=rows,perfect_anticorrelation_check=True)
    with (OUT/'arithmetic-check.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps({'exhaustive_bootstrap_checks':len(rows),'pair_dependence_check':True}))
