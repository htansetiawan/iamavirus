#!/usr/bin/env python3
"""Compare the standalone C escape-set accumulator to the Python referee oracle.

Reads a replay_information_traps.py report and regenerates every represented
world. C receives complete boards in this OFFLINE check; this is not a bot.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('replay',type=Path)
    ap.add_argument('oracle',type=Path)
    ap.add_argument('--binary',type=Path,required=True)
    ap.add_argument('--kit',type=Path,default=Path.home()/'git/fow-starter')
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    sys.path.insert(0,str(args.kit))
    import chess
    import referee
    game=json.loads(args.replay.read_text());oracle=json.loads(args.oracle.read_text())
    if sha(args.replay)!=oracle['replay_sha256'] or sha(args.kit/'referee.py')!=oracle['referee_sha256']:
        raise ValueError('Changed replay or referee')
    board=referee.FowBoard();reps=Counter({referee.position_key(board):1})
    for f in game['frames'][1:oracle['ply']+1]:
        board.push_uci(f['move']);reps[referee.position_key(board)]+=1
    rows=[]
    for case in oracle['rows']:
        inputs=[]
        parent=board.copy();parent.push_uci(case['move'])
        after=reps.copy();after[referee.position_key(parent)]+=1
        for group in case['groups']:
            for w in group['worlds']:
                child=parent.copy();child.push_uci(w['reply'])
                counts=after.copy();counts[referee.position_key(child)]+=1
                if referee.outcome(child,counts):raise ValueError('Terminal world included')
                if referee.observation(child,child.turn)!=group['observation']:raise ValueError('Changed grouping')
                encoded=''.join(child.piece_at(s).symbol() if child.piece_at(s) else '-' for s in range(64))
                inputs.append(f"{0 if child.turn else 1} 0 {int(child.clean_castling_rights()):x} {child.ep_square if child.ep_square is not None else -1} {child.halfmove_clock} {encoded}")
        p=subprocess.run([str(args.binary.resolve())],input='\n'.join(inputs)+'\n' if inputs else '',
                         text=True,capture_output=True,timeout=10,check=True)
        actual=json.loads(p.stdout)
        if not actual['complete'] or actual['worlds']!=len(inputs):raise ValueError('Incomplete C audit')
        got={g['view']:g for g in actual['groups']}
        if len(got)!=len(actual['groups']) or len(got)!=len(case['groups']):raise ValueError('Group count mismatch')
        for g in case['groups']:
            c=got[g['observation']]
            if sorted(c['safe'])!=g['common_safe_replies']:raise ValueError('Escape intersection mismatch')
            if c['worlds']!=len(g['worlds']):raise ValueError('World count mismatch')
            if c['individually_dead']!=sum(not w['safe'] for w in g['worlds']):raise ValueError('Physical loss count mismatch')
        rows.append({'move':case['move'],'worlds':len(inputs),'groups':len(got),'matched':True})
    result={'at':datetime.now(timezone.utc).isoformat(),'classification':'C/referee conformance, not strength',
            'binary_sha256':sha(args.binary),'oracle_sha256':sha(args.oracle),'referee_sha256':oracle['referee_sha256'],
            'tool_sha256':sha(Path(__file__)),'replay_sha256':oracle['replay_sha256'],
            'candidates':len(rows),'worlds':sum(r['worlds'] for r in rows),'groups':sum(r['groups'] for r in rows),'rows':rows}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__=='__main__':main()
