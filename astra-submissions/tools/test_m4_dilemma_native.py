#!/usr/bin/env python3
"""Differential native motif-label checks against frozen Python referee data."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ap=argparse.ArgumentParser()
ap.add_argument('--binary',type=Path,required=True)
ap.add_argument('--corpus',type=Path,required=True)
ap.add_argument('--kit',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
ap.add_argument('--sanitized',action='store_true')
args=ap.parse_args()
sys.path.insert(0,str(args.kit))
import referee,chess
from m4_information_dilemma import analyze

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def compare(expected,actual):
    assert expected['move']==actual['move']
    if 'immediate_outcome' in expected:
        assert list(expected['immediate_outcome'])==actual['immediate_outcome'],(expected,actual)
        return
    for key in ['opponent_legal_replies','continuing_replies','observation_groups',
                'groups_with_no_universal_survival','uniform_reply_min_risk']:
        assert expected[key]==actual[key],(key,expected,actual)
    assert len(expected['terminal_replies'])==actual['terminal_reply_count']
    groups={g['observation']:g for g in actual['groups']}
    assert len(groups)==len(expected['groups'])
    for group in expected['groups']:
        result=groups[group['observation']]
        for key in ['worlds','responses','minimum_fatal_worlds']:
            assert group[key]==result[key],(key,group,result)
        assert len(group['universal_survival'])==result['universal_survival_count']

args.out.mkdir(exist_ok=False)
positions=[]
for path in sorted(args.corpus.glob('*.json.gz')):
    entry=json.loads(gzip.decompress(path.read_bytes()))
    positions.append((entry['position'],referee.FowBoard(entry['fen']),entry['moves'],'frozen'))
for name,fen in [
    ('ep','7k/8/8/3pP3/8/8/8/K7 w - d6 0 8'),
    ('castle','r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1'),
    ('promotion','7k/P7/8/8/8/8/8/K7 w - - 0 1'),
    ('fifty','7k/8/8/8/8/8/8/K7 w - - 99 1'),
    ('fifty_reply','7k/8/8/8/8/8/8/K7 w - - 98 1')]:
    for mirror in [False,True]:
        b=referee.FowBoard(fen)
        if mirror:b=b.mirror()
        labels=[analyze(b,m,referee,chess) for m in referee.fow_moves(b)]
        positions.append((name+('-mirror' if mirror else ''),b,labels,'fresh_reference'))
lines=[]
for name,b,_,_ in positions:
    text=''.join(b.piece_at(s).symbol() if b.piece_at(s) else '-' for s in range(64))
    lines.append(f'{name} {int(not b.turn)} {int(b.clean_castling_rights()):x} {b.ep_square if b.ep_square is not None else -1} {b.halfmove_clock} {text}')
input_text='\n'.join(lines)+'\n'
(args.out/'input.txt').write_text(input_text)
env=dict(os.environ)
if args.sanitized:env['ASAN_OPTIONS']='detect_leaks=0'
begin=time.perf_counter()
run=subprocess.run([str(args.binary.resolve())],input=input_text,text=True,capture_output=True,env=env,check=True)
elapsed=time.perf_counter()-begin
(args.out/'labels.jsonl').write_text(run.stdout)
(args.out/'stderr.txt').write_text(run.stderr)
actual={}
for row in map(json.loads,run.stdout.splitlines()):
    key=(row['position'],row['move']);assert key not in actual;actual[key]=row
count=0
for name,b,labels,source in positions:
    assert set(m.uci() for m in referee.fow_moves(b))==set(x['move'] for x in labels)
    for label in labels:compare(label,actual[(name,label['move'])]);count+=1
assert count==len(actual)
bad=subprocess.run([str(args.binary.resolve())],input='invalid\n',text=True,capture_output=True,env=env)
assert bad.returncode==2
report=dict(positions=len(positions),moves=count,group_fields='Exact observations, world counts, response counts, common-safe counts and minimum fatal counts',
    elapsed_seconds=elapsed,native_stderr=run.stderr.strip(),binary_sha256=sha(args.binary),
    python_chess_version=chess.__version__,referee_sha256=sha(Path(referee.__file__)),
    input_sha256=sha(args.out/'input.txt'),labels_sha256=sha(args.out/'labels.jsonl'),sanitized=args.sanitized,
    note='Offline rules parity and throughput; not playing strength. Repetition history not modeled.')
(args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
