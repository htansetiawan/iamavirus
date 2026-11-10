"""Refresh existing oracle taxonomy on a sealed, already excluded cohort."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import uuid
from labels import ROOT,Native,terminal,ref,chess
from audit_top6_tactics import audit,summary

HERE=Path(__file__).resolve().parent
OUT=ROOT/'astra-submissions/analysis/terminal-motifs-20261110'


def now():return datetime.now(timezone.utc).isoformat()
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def lease(ident,remove=False):
    path=ROOT/'chatroom/cores.json'
    with Path('/tmp/iamavirus-cores-json.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);state=json.loads(path.read_text())
        if remove:state['allocation']=[r for r in state['allocation'] if r.get('lease')!=ident]
        else:
            assert not any(set(r.get('cores',[]))&{4,5} for r in state['allocation'])
            state['allocation'].append(dict(owner='astra',cores=[4,5],lease=ident,purpose='327 descriptive terminal-pattern curation on excluded307cohort; no inference/GPU/API'))
        state['updated']=now();temp=path.with_name('.cores-'+ident);temp.write_text(json.dumps(state,indent=2)+'\n');os.replace(temp,path)


def main():
    plan=json.loads((OUT/'plan.json').read_text())
    for path,expected in plan['dependencies'].items():assert sha(path)==expected,path
    assert not (OUT/'execution.json').exists();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('fixed15minute curation bound')));signal.alarm(900)
    cohort=json.loads(Path(plan['cohort']).read_text());denied={g['sequence_sha256'] for g in json.loads(Path(plan['future_exclusions']).read_text())['games']}
    assert len(cohort['games'])==300 and all(g['sequence_sha256'] in denied for g in cohort['games'])
    destination=Path(plan['private']);destination.mkdir(exist_ok=False)
    ident=uuid.uuid4().hex;lease(ident);started=time.monotonic();state=dict(status='running',started_at=now(),lease=ident)
    save(OUT/'started.json',state);os.sched_setaffinity(0,{4,5});native=Native();rows=[];frames=alternatives=0
    try:
        for index,g in enumerate(cohort['games']):
            path=Path(plan['raw'])/g['game']/'replay.json';assert sha(path)==g['replay_sha256'];replay=json.loads(path.read_bytes())
            b=ref.FowBoard();repetitions=Counter({ref.position_key(b):1});parent=None
            for ply,frame in enumerate(replay['frames']):
                if ply:
                    assert ref.outcome(b,repetitions) is None
                    move=b.parse_uci(frame['move']);parent=b.copy(stack=False)
                    if ply==len(replay['frames'])-1:parent_repetitions=repetitions.copy()
                    b.push(move);repetitions[ref.position_key(b)]+=1
                full=''.join(b.piece_at(s).symbol() if b.piece_at(s) else '-' for s in range(64))
                assert (frame['ply'],frame['board'],frame['white'],frame['black'])==(ply,full,ref.observation(b,True),ref.observation(b,False));frames+=1
            event=None
            if replay['reason']=='King capturable':
                event=terminal(parent,chess.Move.from_uci(replay['frames'][-1]['move']),native,parent_repetitions)
                alternatives+=len(ref.fow_moves(parent));n=len(replay['frames'])-1;mover='white' if n%2 else 'black'
                for killer in event['killers']:
                    sq=chess.parse_square(killer['square']);symbol=replay['frames'][-1]['board'][sq]
                    arrivals=[i for i in range(1,n) if replay['frames'][i]['board'][sq]==symbol and replay['frames'][i-1]['board'][sq]!=symbol]
                    arrival=max(arrivals,default=0);killer['last_arrival_ply']=arrival;killer['plies_since_arrival']=n-arrival
                    killer['hidden_at_every_frame_since_arrival']=all(f[mover][sq]=='?' for f in replay['frames'][arrival:n])
                dst=chess.parse_square(event['move'][2:4]);victim=replay['frames'][-2]['board'][dst]
                event['victim_arrived_on_previous_ply']=bool(event['kind']=='king_bait' and n>=2 and victim!='-' and replay['frames'][-3]['board'][dst]!=victim)
            # Side aliases avoid selecting the wrong seat if display names
            # coincide. Original IDs/names/versions remain reporting metadata.
            aliases=dict(replay,white='white-seat',black='black-seat')
            for side in ('white','black'):
                row=audit(aliases,side+'-seat',ref);row.update(team_id=replay[side+'PlayerId'],team=replay[side],version=replay[side+'Version'],
                    opponent=replay['black' if side=='white' else 'white'],source_sha256=g['replay_sha256'])
                if row['terminal'] is not None:
                    assert row['terminal']['move']==event['move']
                    assert sorted(row['terminal']['safe_moves'])==event['safe_moves'];row['terminal_motif']=event
                else:row['terminal_motif']=None
                rows.append(row)
            if (index+1)%50==0:print(json.dumps(dict(completed_games=index+1,total=300)),flush=True)
        save(destination/'rows.json',rows)
        groups=defaultdict(list)
        for row in rows:groups[(row['team_id'],row['version'])].append(row)
        panels=[]
        for (team,version),seats in sorted(groups.items(),key=lambda p:(p[0][0] or '',p[0][1] if p[0][1] is not None else -1)):
            terminal_rows=[r for r in seats if r['terminal_motif'] is not None]
            motifs=[r['terminal_motif'] for r in terminal_rows]
            panel=dict(team_id=team,name=seats[0]['team'],version=version,**summary(seats),
                motif_kinds=dict(Counter(t['kind'] for t in motifs)),terminal_games=len(motifs),
                one_ply_forced=sum(t['forced_one_ply_loss'] for t in motifs),
                hidden_nonforced=sum(t['all_killers_hidden'] and not t['forced_one_ply_loss'] for t in motifs),
                material_down3_before_fatal=sum(t['material_before']<=-3 for t in motifs),
                static_hidden_attacker=sum(any(k['plies_since_arrival']>=3 and k['hidden_at_every_frame_since_arrival'] for k in t['killers']) for t in motifs),
                recent_optional_bait=sum(t['kind']=='king_bait' and t['victim_arrived_on_previous_ply'] and not t['forced_one_ply_loss'] for t in motifs))
            panels.append(panel)
        result=dict(at=now(),games=300,seats=len(rows),course_frames=frames,native_checked_terminal_alternatives=alternatives,
            source_window=[min(g['created_at'] for g in cohort['games']),max(g['created_at'] for g in cohort['games'])],
            cohorts_sha256=sha(plan['cohort']),private_rows_sha256=sha(destination/'rows.json'),panels=panels,seconds=time.monotonic()-started,
            scope=plan['scope'])
        save(OUT/'result.json',result);state.update(status='complete')
        print(json.dumps({k:v for k,v in result.items() if k!='panels'},indent=2),flush=True)
    except BaseException as exc:state.update(status='failed',error=repr(exc));raise
    finally:
        lease(ident,remove=True);state.update(ended_at=now(),seconds=time.monotonic()-started,own_lease_released=True);save(OUT/'execution.json',state)


if __name__=='__main__':main()
