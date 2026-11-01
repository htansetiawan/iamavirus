#!/usr/bin/env python3
"""Freeze new Nov1 games, with permitted observations separate from truth labels."""
import argparse,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];sys.path.insert(0,str(ROOT))
from learning import ingest,rules
OPPONENTS=['Instructors','duck','HYPOTHERMIA','Greek Gift','Knight Vision','Strongly Invisible','Decent Chess Bot','Crimson Fog','Mist Opportunities']
def sha(b):return hashlib.sha256(b).hexdigest()
def index(s):return (ord(s[1])-49)*8+ord(s[0])-97
def advance_context(old,before,after,uci):
    src,dst=index(uci[:2]),index(uci[2:4]);piece=before[src].lower();type_='pnbrqk'.index(after[dst].lower())
    captured=before[dst].lower()
    value={'-':0,'p':1,'n':3,'b':3,'r':5,'q':9,'k':0}[captured]
    if piece=='p' and src%8!=dst%8 and captured=='-':value=1
    known=(old>>23)&1;last_to=(old>>6)&63;last_type=(old>>16)&7
    continued=bool(known and last_to==src and last_type=='pnbrqk'.index(piece))
    promo='pnbrqk'.index(uci[4]) if len(uci)==5 else 6
    move=src|(dst<<6)|(promo<<12)
    return move|(type_<<16)|(value<<19)|(1<<23)|(int(continued)<<24)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    raw=ROOT/'data/raw';rows={r['id']:r for r in map(json.loads,(raw/'accepted.jsonl').read_text().splitlines())}
    excluded=set();signatures=set()
    for p,key in [(ROOT/'astra-submissions/analysis/king-event-calibration-20261101/plan.json','game'),
                  (ROOT/'astra-submissions/analysis/temporal-prior-20261101/data-v2/manifest.json','id'),
                  (ROOT/'astra-submissions/analysis/fresh-taxonomy-20261101/cases.json','game')]:
        for row in json.loads(p.read_text())['games']:
            excluded.add(row[key]);seq=row.get('sequence_sha256')
            if seq:signatures.add(seq)
    cases=[];seen=set(excluded)
    for opponent in OPPONENTS:
        for us in [0,1]:
            observer,other=('white','black')[us],('black','white')[us]
            pool=[r for r in rows.values() if '2026-11-01'<=(r.get('createdAt') or '')<'2026-11-02'
                  and r.get(other)==opponent and r.get(observer) not in ['Uniform','Baseline','baseline.py'] and r['id'] not in seen]
            pool.sort(key=lambda r:(r.get(observer)!='IAmAVirus',sha(('temporal-belief-1101:'+r['id']).encode())))
            for row in pool:
                payload=(raw/'games'/row['id']/'replay.json').read_bytes();rp=json.loads(payload)
                sig=ingest.replay_hash(rp)
                if sig in signatures:continue
                states,errors=ingest.validate_replay(rp)
                if errors:raise ValueError((row['id'],errors))
                seen.add(row['id']);signatures.add(sig);break
            else:raise ValueError(('no uninspected games',opponent,us))
            case={'id':rp['id'],'us':us,'observer':rp[observer],'opponent':opponent,'createdAt':rp['createdAt'],
                  'observer_version':rp.get(observer+'Version'),'opponent_version':rp.get(other+'Version'),
                  'replay_sha256':sha(payload),'sequence_sha256':sig,'frames_validated':len(states),'decisions':0}
            steps=[];truth=[];contexts=[0,0];end=min(80,len(states)-2)
            for ply in range(end+1):
                fr=rp['frames'][ply];st=states[ply]
                if ply:
                    mover=(ply-1)%2;contexts[mover]=advance_context(contexts[mover],rp['frames'][ply-1]['board'],fr['board'],fr['move'])
                step={'ply':ply,'view':fr[observer],'own_move':fr['move'] if ply and (ply-1)%2==us else None}
                if ply%2==us:
                    played=rp['frames'][ply+1]['move'];step['next_own_move']=played
                    case['decisions']+=1
                    truth.append({'ply':ply,'board':fr['board'],'side':st.board.side,'castle':st.board.castling,'ep':st.board.en_passant,
                                  'opponent_context':contexts[us^1],'fatal':bool(states[ply+1].board.mover_lost())})
                steps.append(step)
            feed={'id':rp['id'],'us':us,'steps':steps};truth={'id':rp['id'],'rows':truth}
            for name,obj in [('input',feed),('truth',truth)]:
                data=(json.dumps(obj,indent=2)+'\n').encode();path=args.out/f"{rp['id']}.{name}.json";path.write_bytes(data);case[name+'_sha256']=sha(data)
            cases.append(case)
    plan={'cases':cases,'cap':20000,'seed':11012026,'max_ply':80,'model_temperature':2,'history_table':None,
          'arms':{'static_merged':{'ASTRA_TEMPORAL_MODEL':'0','ASTRA_CONTEXT_MERGE':'0'},'static_context':{'ASTRA_TEMPORAL_MODEL':'0','ASTRA_CONTEXT_MERGE':'1'},'temporal_context':{'ASTRA_TEMPORAL_MODEL':'1','ASTRA_CONTEXT_MERGE':'1'}},
          'selection':'One new Nov1 game per opponent and observer colour; prefer our actual seats, then deterministic hash; no outcome selection; earlier experiments excluded.',
          'gate':'Development screen: >=0.1 nat less mean clipped truth-board NLL, <=2 percentage-point support regression, common-covered king Brier increase <=.002 versus BOTH controls; <=2x update time. Positive earns larger/cap-and-clock validation, not a ZIP.',
          'no_rebuild':'First-mechanism test stops expanding after empty belief. Missing truth remains zero on all later planned decisions; coverage is reported. Rebuild reset is unit tested, not claimed live here.',
          'privacy':'Updates receive only own moves and own views. Truth is supplied solely to const probe after update; checksums must remain identical under truth redaction.',
          'source_sha256':sha(Path(__file__).read_bytes())}
    (args.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps({'games':len(cases),'decisions':sum(c['decisions'] for c in cases),'our_seats':sum(c['observer']=='IAmAVirus' for c in cases),'frames_validated':sum(c['frames_validated'] for c in cases)}))
if __name__=='__main__':main()
