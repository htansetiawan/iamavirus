#!/usr/bin/env python3
"""Exact rational certificates for small uniform mixtures in local loss games.

No LP solver or floating-point optimizer is needed. An attacker mixture supplies
a lower bound over every defender action; a defender mixture supplies an upper
bound over every hidden reply. Equality proves the local value. Failure to find
equal bounds is not proof that no equilibrium exists.
"""
import argparse
from fractions import Fraction
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path


def certificate(group,max_support=3):
    actions=sorted(group['fatal_matrix']);replies=group['replies'];matrix=group['fatal_matrix']
    # Identical payoff rows/columns are strategically interchangeable. Keep
    # representatives to make combination search depend on distinct patterns.
    ds={tuple(matrix[a]):a for a in actions}
    ats={tuple(matrix[a][i] for a in actions):r for i,r in enumerate(replies)}
    for k in range(1,max_support+1):
        low=(-1,None);high=(k+1,None)
        for support in combinations(ats,k):
            value=min(sum(v[a] for v in support) for a in range(len(actions)))
            if value>low[0]:low=(value,[ats[v] for v in support])
        for support in combinations(ds,k):
            value=max(sum(v[r] for v in support) for r in range(len(replies)))
            if value<high[0]:high=(value,[ds[v] for v in support])
        if low[1] and high[1] and low[0]==high[0]:
            result=dict(attacker_support=low[1],defender_support=high[1],uniform_denominator=k,
                        loss_numerator=low[0],loss_denominator=k,
                        scope='Conditional immediate-response game only; not full-game value or opponent-policy estimate.')
            verify(group,result)
            return result
    return None


def verify(group,proof):
    k=proof['uniform_denominator'];weight=Fraction(1,k)
    assert len(proof['attacker_support'])==len(proof['defender_support'])==k
    assert len(set(proof['attacker_support']))==len(set(proof['defender_support']))==k
    indices=[group['replies'].index(r) for r in proof['attacker_support']]
    matrix=group['fatal_matrix']
    lower=min(sum(weight*row[i] for i in indices) for row in matrix.values())
    upper=max(sum(weight*matrix[a][i] for a in proof['defender_support']) for i in range(len(group['replies'])))
    assert lower==upper==Fraction(proof['loss_numerator'],proof['loss_denominator'])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--corpus',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();results=[];eligible=0
    for path in sorted(args.corpus.glob('*.json.gz')):
        entry=json.loads(gzip.decompress(path.read_bytes()))
        if 'analysis' not in entry:continue
        for index,g in enumerate(entry['analysis']['groups']):
            if not g['minimum_fatal_worlds'] or not all(g['safe_by_reply'][r] for r in g['replies']):continue
            eligible+=1;proof=certificate(g)
            if proof:results.append(dict(position=entry['position'],setup=entry['analysis']['move'],group=index,
                observation=g['observation'],worlds=g['worlds'],proof=proof,source=path.name,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    report=dict(eligible_information_conflict_groups=eligible,certified_groups=len(results),certificates=results,
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='certificates'}))

if __name__=='__main__':main()
