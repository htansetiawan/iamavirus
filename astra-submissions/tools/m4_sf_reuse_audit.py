#!/usr/bin/env python3
"""Audit native Stockfish logs for exact-FEN reuse and context-dependent scores.

This is an instrumented offline request-stream measurement. It does not measure
unlogged search speed or imply that reusing scores preserves the search policy.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def requests(lines):
    fen=None;pending=None
    for number,line in enumerate(lines,1):
        line=line.rstrip('\r\n')
        if line.startswith('>> position fen '):
            if pending is not None:raise ValueError(f'New position before bestmove at line {number}')
            fen=line[len('>> position fen '):]
            if len(fen.split())!=6:raise ValueError(f'Invalid FEN at line {number}')
        elif line.startswith('>> go '):
            if pending is not None or fen is None:raise ValueError(f'Unpaired go at line {number}')
            if line!='>> go depth 1':raise ValueError('Unexpected search configuration')
            pending={'fen':fen,'scores':{},'line':number,'engine_ms':0}
        elif line.startswith('<< info ') and pending is not None:
            if ' multipv ' not in line or 'lowerbound' in line or 'upperbound' in line:continue
            match=re.search(r' score (cp|mate) (-?\d+) .*?\bpv ([a-h][1-8][a-h][1-8][qrbn]?)\b',line)
            if not match:continue
            kind,raw,move=match.groups();value=int(raw)
            cp=value if kind=='cp' else (1 if value>0 else -1)*(20000-min(100,abs(value))*100)
            pending['scores'][move]=cp
            timing=re.search(r' time (\d+) ',line)
            if timing:pending['engine_ms']=max(pending['engine_ms'],int(timing[1]))
        elif line.startswith('<< bestmove '):
            if pending is None:raise ValueError(f'Unpaired bestmove at line {number}')
            pending['bestmove']=line.split()[2];yield pending;pending=None
    if pending is not None:raise ValueError('Incomplete final evaluator request')


def percentile(xs,q):
    if not xs:return None
    xs=sorted(xs);p=(len(xs)-1)*q;lo=math.floor(p);hi=math.ceil(p)
    return xs[lo]*(hi-p)+xs[hi]*(p-lo) if hi!=lo else xs[lo]


def summarize(rows):
    first={};counts=Counter();n=repeat=identical=best_changed=coverage_changed=0
    differences=[];maxima=[];examples=[];total_ms=repeat_ms=0
    for row in rows:
        n+=1;key=row['fen'];counts[key]+=1;total_ms+=row['engine_ms']
        if key not in first:first[key]=row;continue
        repeat+=1;repeat_ms+=row['engine_ms'];old=first[key]
        identical+=row['scores']==old['scores'];best_changed+=row['bestmove']!=old['bestmove']
        coverage_changed+=set(row['scores'])!=set(old['scores'])
        common=set(row['scores'])&set(old['scores'])
        delta={move:abs(row['scores'][move]-old['scores'][move]) for move in common}
        differences.extend(delta.values());maxima.append(max(delta.values(),default=0))
        if delta:
            move=max(delta,key=delta.get)
            examples.append({'max_abs_cp_change':delta[move],'move':move,'first_cp':old['scores'][move],
                'repeat_cp':row['scores'][move],'first_line':old['line'],'repeat_line':row['line'],
                'fen':key,'first_best':old['bestmove'],'repeat_best':row['bestmove']})
    examples.sort(key=lambda r:r['max_abs_cp_change'],reverse=True)
    return {'requests':n,'unique_exact_fens':len(first),'repeated_requests':repeat,
        'repeat_share':repeat/n if n else 0,'identical_score_maps_on_repeat':identical,
        'changed_score_maps_on_repeat':repeat-identical,'bestmove_changed_on_repeat':best_changed,
        'move_coverage_changed_on_repeat':coverage_changed,'compared_move_scores':len(differences),
        'absolute_cp_change_vs_first':{name:percentile(differences,q) for name,q in [('median',.5),('p95',.95),('max',1)]},
        'repeat_max_cp_change_vs_first':{name:percentile(maxima,q) for name,q in [('median',.5),('p95',.95),('max',1)]},
        'engine_reported_ms':total_ms,'engine_reported_ms_on_repeats':repeat_ms,
        'engine_reported_repeat_time_share':repeat_ms/total_ms if total_ms else None,
        'request_multiplicity_histogram':dict(sorted(Counter(counts.values()).items())),
        'largest_changes':examples[:8]}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    r=args.run;manifest=json.loads((r/'manifest.json').read_text())
    for name,data in manifest['files'].items():assert sha(r/name)==data['sha256'],name
    receipt=json.loads((r/'receipt.json').read_text());assert receipt['returncode']==0
    probe=json.loads((r/'probe/results.json').read_text());assert len(probe['rows'])==1
    p=probe['rows'][0];assert p['returncode']==0 and p['prefix_exact'] and p['outputs']==p['decision']
    assert all(m['ok']==1 and m['snapshot']==1 and m.get('over',0)==0 for m in p['metrics'])
    evaluations=p['prefix_evaluation']+[p['evaluation']]
    assert all(e['ready']==1 and e['failed']==0 for e in evaluations)
    log=r/'stockfish.log'
    with log.open() as f:rows=list(requests(f))
    expected=sum(int(e['calls']) for e in evaluations)
    assert len(rows)==expected,('incomplete evaluator capture',len(rows),expected)
    per_decision=[];offset=0
    for i,e in enumerate(evaluations):
        count=int(e['calls']);part=rows[offset:offset+count];offset+=count
        per_decision.append({'own_decision':i+1,'external_seconds':e['seconds'],**summarize(part)})
    result={'classification':'exact-FEN request reuse diagnostic, not a cache correctness or playing-strength claim',
        'manifest_sha256':sha(r/'manifest.json'),'log_sha256':sha(log),'probe_sha256':sha(r/'probe/results.json'),
        'tool_sha256':sha(Path(__file__)),'source':str(r.resolve()),'selected_move':p['chosen'],
        'capture_complete_against_transport_calls':True,'all_requests':summarize(rows),'per_decision':per_decision,
        'limits':['Native logging changes wall-clock timing and therefore the searched tree.',
            'Engine time is integer-millisecond UCI search time, not transport or total move time.',
            'Repeated FEN includes side, castling, en passant and halfmove clock; engine hash/search history is not part of the key.',
            'Scores are compared to the first occurrence, which models a persistent first-result cache; no cache has been enabled.',
            'Mate scores use the adapter conversion and are not ordinary centipawn distances.']}
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result['all_requests'].items() if k not in ['largest_changes','request_multiplicity_histogram']},indent=2))


if __name__=='__main__':main()
