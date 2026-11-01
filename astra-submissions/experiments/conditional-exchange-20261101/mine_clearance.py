#!/usr/bin/env python3
"""Curate replay examples of forcing clearance, with exact continuation checks.

The recorded three-ply sequence locates candidates. The proof then considers
EVERY immediate king-surviving reply, followed by the nominated slider capture
and every surviving response. Labels are hindsight only, never policy inputs.
"""
import hashlib
import json
from pathlib import Path
import sys
from collections import Counter
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import ingest,rules
from fresh_taxonomy_gate import material

OUT=ROOT/'astra-submissions/analysis/conditional-exchange-20261101'
TARGETS={'IAmAVirus','Instructors','duck','HYPOTHERMIA','Greek Gift','Knight Vision',
         'Strongly Invisible','Decent Chess Bot','Mist Opportunities','Crimson Fog'}

def sq(x):return rules.square_index(x)
def middle(origin,blocker,target,kind):
    x,y=origin%8,origin//8;dx,dy=target%8-x,target//8-y
    if kind=='r' and dx and dy:return False
    if kind=='b' and abs(dx)!=abs(dy):return False
    if dx and dy and abs(dx)!=abs(dy):return False
    sx=(dx>0)-(dx<0);sy=(dy>0)-(dy<0)
    x+=sx;y+=sy
    while (x,y)!=(target%8,target//8):
        if x+8*y==blocker:return True
        x+=sx;y+=sy
    return False

def candidates(rep):
    fs=rep['frames']
    for i in range(len(fs)-3):
        one,reply,two=(fs[i+k]['move'] for k in [1,2,3])
        if not all([one,reply,two]):continue
        b=fs[i]['board'];side=i%2;mine=str.isupper if side==0 else str.islower
        piece=b[sq(one[:2])];victim=b[sq(one[2:4])];slider=b[sq(two[:2])];target=b[sq(two[2:4])]
        if piece=='-' or not mine(piece) or victim=='-' or mine(victim):continue
        if slider.lower() not in 'rbq' or not mine(slider) or target.lower() not in 'nbrq' or mine(target):continue
        if fs[i+1]['board'][sq(reply[:2])].lower()!='k':continue
        if not middle(sq(two[:2]),sq(one[:2]),sq(two[2:4]),slider.lower()):continue
        if fs[i+2]['board'][sq(two[:2])]!=slider or fs[i+2]['board'][sq(two[2:4])]!=target:continue
        yield i,one,two

def prove(state,first,capture):
    side=state.board.side;lead=material(state.board.board_string(),side)
    child=state.copy();child.push(first)
    if child.outcome():return None
    king=child.board.king_square(side^1)
    if not child.board.is_attacked(king,side):return None
    # A real check: keeping the king fixed cannot be enough unless capturing
    # or blocking the attacker. Require every surviving reply to move it.
    safe=[m for m in child.board.legal_moves() if not child.board.move_loses_king(m)]
    if not safe or any(sq(m[:2])!=king for m in safe):return None
    branches=[]
    for reply in safe:
        after=child.copy();after.push(reply)
        if after.outcome() or capture not in after.board.legal_moves() or after.board.move_loses_king(capture):return None
        after.push(capture)
        if after.outcome():return None
        answers=[]
        for response in after.board.legal_moves():
            end=after.copy();end.push(response);outcome=end.outcome()
            if outcome:
                if outcome[0]==('0-1' if side==0 else '1-0') or outcome[0]=='1/2-1/2':return None
                continue
            answers.append((material(end.board.board_string(),side)-lead,response))
        if not answers:return None
        gain,response=min(answers)
        branches.append({'forced_king_reply':reply,'best_defender_response':response,'gain':gain})
    return {'minimum_gain':min(b['gain'] for b in branches),'branches':branches}

def main():
    raw=ROOT/'data/raw';accepted=(raw/'accepted.jsonl').read_bytes()
    byid={r['id']:r for r in map(json.loads,accepted.splitlines())}
    rows=[r for r in byid.values() if (r.get('createdAt') or '')>='2026-10-29' and
          (r.get('white') in TARGETS or r.get('black') in TARGETS)]
    rows=sorted(rows,key=lambda r:(r.get('createdAt',''),r['id']),reverse=True)[:5000]
    hits=[];near=[];candidates_seen=0;invalid=[];scanned=0
    for row in rows:
        path=raw/'games'/row['id']/'replay.json'
        if not path.exists():continue
        payload=path.read_bytes();rep=json.loads(payload);scanned+=1
        found=list(candidates(rep))
        if not found:continue
        states,errors=ingest.validate_replay(rep)
        if errors:invalid.append({'id':row['id'],'errors':errors});continue
        for ply,one,two in found:
            candidates_seen+=1;proof=prove(states[ply],one,two)
            if proof is None:continue
            side=ply%2;view=rep['frames'][ply][('black','white')[side]]
            entry={'game':row['id'],'ply':ply,'attacker':rep[('white','black')[side]],
                   'attacker_version':rep.get(('white','black')[side]+'Version'),
                   'defender':rep[('black','white')[side]],'first':one,'slider_capture':two,
                   'first_source_hidden':view[sq(one[:2])]=='?', 'slider_hidden':view[sq(two[:2])]=='?',
                   'replay_sha256':hashlib.sha256(payload).hexdigest(),**proof}
            (hits if proof['minimum_gain']>=2 else near).append(entry)
    result={'window_since':'2026-10-29','maximum_games':5000,'games_scanned':scanned,
            'initial_attempt_error':'Index contains explicit null createdAt; first attempt failed before scanning. Missing dates are now excluded.',
            'accepted_sha256':hashlib.sha256(accepted).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'candidate_sequences':candidates_seen,'validated_gain_ge2':len(hits),'hits':hits,'lesser_gains':near,
            'invalid_replays':invalid,'by_attacker':dict(Counter(h['attacker'] for h in hits)),
            'scope':'Pattern-selected, hindsight tactical corpus. Not a frequency or strength estimate; recorded continuation used for discovery only. Proof branches over all surviving replies.'}
    (OUT/'clearance-corpus.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['hits','lesser_gains']}))

if __name__=='__main__':main()
