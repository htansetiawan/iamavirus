#!/usr/bin/env python3
"""Audit what was visible before committing to a recorded queen exchange."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'astra-submissions/tools')]
from learning import ingest
from fresh_taxonomy_gate import material


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('cases',type=Path);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();data=json.loads(args.cases.read_text());cache={};rows=[]
    provenance={g['game']:g for g in data['games']}
    for case in data['cases']:
        if not case['recorded_queen_captured_next_reply']:
            continue
        gid=case['game'];ply=case['ply'];key=case['side'];side=('white','black').index(key)
        if gid not in cache:
            path=ROOT/provenance[gid]['replay_path'];assert sha(path)==provenance[gid]['replay_sha256']
            replay=json.loads(path.read_text());states,errors=ingest.validate_replay(replay);assert not errors
            cache[gid]=(replay,states)
        replay,states=cache[gid];frames=replay['frames'];reply=frames[ply+2]['move']
        src=ord(reply[0])-97+8*(int(reply[1])-1);dst=ord(reply[2])-97+8*(int(reply[3])-1)
        assert frames[ply+1]['board'][dst]==('Q','q')[side]
        assert frames[ply]['board'][src]==frames[ply+1]['board'][src]
        initial=material(frames[ply]['board'],side);answers=[];losing=('0-1','1-0')[side]
        after=states[ply+2]
        if after.outcome() is None:
            for response in after.board.legal_moves():
                end=after.copy();end.push(response);outcome=end.outcome()
                if outcome and outcome[0]==losing:
                    continue
                answers.append(dict(move=response,net_loss=0 if outcome else initial-material(end.board.board_string(),side),terminal=outcome))
        best=min((a['net_loss'] for a in answers),default=None)
        rows.append(dict(game=gid,ply=ply,side=key,opponent=case['opponent'],played=case['played'],reply=reply,
            capturer=frames[ply+1]['board'][src],hidden_before=frames[ply][key][src]=='?',
            hidden_after_own_move=frames[ply+1][key][src]=='?',
            existing_queen_exposed_unseen_tag='queen_exposed_unseen' in case['tags'],
            recorded_net_loss=case['recorded_net_loss'],played_probe_queen_loss=case['played_probe']['queen_exchange_loss'],
            actual_reply_best_safe_net_loss=best,best_responses=[a for a in answers if a['net_loss']==best],
            recorded_response=frames[ply+3]['move'] if ply+3<len(frames) else None,
            cohort=case['cohort']))
    counts=Counter()
    for row in rows:
        counts['recorded_queen_captures']+=1
        counts['capturer_hidden_before_decision']+=row['hidden_before']
        counts['capturer_hidden_after_own_move']+=row['hidden_after_own_move']
        counts['capturer_hidden_before_revealed_after']+=row['hidden_before'] and not row['hidden_after_own_move']
        counts['existing_exposure_tag']+=row['existing_queen_exposed_unseen_tag']
    output=dict(source_sha256=sha(Path(__file__)),cases_sha256=sha(args.cases),counts=dict(counts),rows=rows,
        scope='Offline timing audit of actual queen capturers. Existing taxonomy definitions are unchanged. Future recorded replies and true boards are labels, never bot inputs.',
        limitations='A best one-response material recovery is not a complete strategic verdict. Declining it need not be an error; longer tactics and information are outside this probe.')
    with args.out.open('x') as f:json.dump(output,f,indent=2)
    print(json.dumps(counts,indent=2))


if __name__=='__main__':
    main()
