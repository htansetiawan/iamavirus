"""Independent referee audit of a fixed sample from the existing attack census.

Labels full histories with python-chess/referee, compares both the scanner and
its saved census, and distinguishes missed escapes from positions with none.
No bot is run. All true-board labels are offline-only.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import sys

from scan_hidden_king_arrivals import analyze, attackers

ROOT=Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(path, referee):
    import chess
    FowBoard, make_frame, outcome, position_key = referee
    game=json.loads(path.read_bytes())
    board=FowBoard()
    repetitions=Counter({position_key(board):1})
    snapshots=[]
    ended=None
    for i,frame in enumerate(game['frames']):
        if i:
            assert ended is None, ('move after terminal',i)
            board.push(board.parse_uci(frame['move']))
            repetitions[position_key(board)]+=1
        # Clock metadata is not an input to attack/observation validation.
        # Some older corpus exports omit it; record that instead of excluding
        # otherwise complete games from the board-label audit.
        expected=make_frame(board,[0,0],frame['move'])
        for key in ('ply','board','white','black'):
            assert frame[key]==expected[key], ('frame mismatch',i,key)
        for color,name in ((chess.WHITE,'white'),(chess.BLACK,'black')):
            king=board.king(color)
            oracle=sorted(board.attackers(not color,king)) if king is not None else []
            assert attackers(frame['board'],name)==oracle, ('attacker mismatch',i,name)
        snapshots.append(board.copy(stack=False))
        ended=outcome(board,repetitions)

    rows=[]
    for i in range(1,len(snapshots)):
        before,after=snapshots[i-1:i+1]
        victim=after.turn
        victim_name='white' if victim else 'black'
        mover=not victim
        king=after.king(victim)
        previous_king=before.king(victim)
        old=sorted(before.attackers(mover,previous_king)) if previous_king is not None else []
        new=sorted(after.attackers(mover,king)) if king is not None else []
        if old or not new:
            continue
        view=game['frames'][i][victim_name]
        hidden=[sq for sq in new if view[sq]=='?']
        visible=[sq for sq in new if view[sq]!='?']
        visibility='fully_hidden' if not visible else 'visible' if not hidden else 'mixed'
        remaining=None
        response_move=None
        safe=[]
        if i+1<len(snapshots):
            reply=snapshots[i+1]
            rk=reply.king(victim)
            remaining=sorted(reply.attackers(mover,rk)) if rk is not None else []
            response='attack_survived_reply' if remaining else 'defender_escaped'
            response_move=game['frames'][i+1]['move']
            for move in after.generate_pseudo_legal_moves():
                q=after.copy(stack=False)
                q.push(move)
                k=q.king(victim)
                if k is not None and not q.is_attacked_by(mover,k):
                    safe.append(move.uci())
        else:
            response='no_recorded_reply'
        rows.append({'game':game.get('id',path.parent.name),
                     'ply':game['frames'][i]['ply'],'move':game['frames'][i]['move'],
                     'victim_side':victim_name,'visibility':visibility,
                     'attacking_squares':new,'hidden_attacking_squares':hidden,
                     'visible_attacking_squares':visible,
                     'response':response,'response_move':response_move,
                     'attackers_after_response':remaining,
                     'safe_replies':safe if response_move is not None else None})
    original=analyze(path)
    assert len(original)==len(rows), ('event count mismatch',len(original),len(rows))
    for row,computed in zip(rows,original):
        for key,value in row.items():
            if key!='safe_replies':
                assert computed[key]==value, ('event mismatch',row['ply'],key)
    return game,rows


def summary(rows,game_ids,avoidable_only):
    totals=defaultdict(Counter)
    grouped=defaultdict(lambda:defaultdict(Counter))
    for row in rows:
        if row['response']=='no_recorded_reply':
            continue
        if avoidable_only and not row['safe_replies']:
            continue
        vis=row['visibility']
        survived=int(row['response']=='attack_survived_reply')
        for c in (totals[vis],grouped[row['game']][vis]):
            c['answered']+=1
            c['attack_survived']+=survived
    rates={k:v['attack_survived']/v['answered'] for k,v in totals.items()}
    gap=None
    if 'fully_hidden' in rates and 'visible' in rates:
        delta=rates['fully_hidden']-rates['visible']
        influences=[]
        for game in game_ids:
            z=0
            for vis,sign in [('fully_hidden',1),('visible',-1)]:
                c=grouped[game][vis]
                z+=sign*(c['attack_survived']-rates[vis]*c['answered'])/totals[vis]['answered']
            influences.append(z)
        n=len(game_ids)
        se=math.sqrt(n/(n-1)*sum(z*z for z in influences)) if n>1 else None
        gap={'hidden_minus_visible':delta,'cluster_standard_error':se,
             'approximate_95_percent_interval':[delta-1.96*se,delta+1.96*se] if se is not None else None,
             'clusters':n}
    return {'rates':rates,'counts':{k:dict(v) for k,v in totals.items()},'difference':gap}


def make_panel(rows,games,seed):
    """Freeze composable diagnostic slices, one decision per game, no bot run."""
    categories=defaultdict(list)
    for row in rows:
        if not row['safe_replies'] or row['visibility']=='mixed':
            continue
        if any('clocks' not in f for f in games[row['game']][1]['frames']):
            continue
        missed=row['response']=='attack_survived_reply'
        visibility='hidden' if row['visibility']=='fully_hidden' else 'visible'
        categories[visibility+('_missed_escape' if missed else '_escaped')].append(row)
    def order(row):
        return hashlib.sha256(f"{seed}:{row['game']}:{row['ply']}".encode()).hexdigest()
    used=set()
    panel=[]
    for label in ['hidden_missed_escape','visible_missed_escape','hidden_escaped','visible_escaped']:
        count=0
        for row in sorted(categories[label],key=order):
            if row['game'] in used:
                continue
            record,_=games[row['game']]
            panel.append({'game':row['game'],'replay':record['path'],
                          'replay_sha256':record['sha256'],'frame':row['ply'],
                          'side':row['victim_side'],'slice':label,
                          'safe_replies_offline_only':row['safe_replies']})
            used.add(row['game']);count+=1
            if count==16:
                break
    controls=[]
    for game_id,(record,game) in games.items():
        if game_id in used or any('clocks' not in f for f in game['frames']):
            continue
        for frame in game['frames'][8:-1]:
            side='white' if frame['ply']%2==0 else 'black'
            if not attackers(frame['board'],side):
                controls.append({'game':game_id,'ply':frame['ply'],'side':side})
    count=0
    for row in sorted(controls,key=order):
        if row['game'] in used:
            continue
        record,_=games[row['game']]
        panel.append({'game':row['game'],'replay':record['path'],
                      'replay_sha256':record['sha256'],'frame':row['ply'],
                      'side':row['side'],'slice':'ordinary_no_current_king_attack',
                      'safe_replies_offline_only':None})
        used.add(row['game']);count+=1
        if count==16:
            break
    return {'classification':'fixed diagnostic panel, not guaranteed unseen by prior models',
            'selection':'16 per slice when available; one decision per game; complete clock metadata',
            'seed':seed,'counts':dict(Counter(p['slice'] for p in panel)),
            'actor_input':'only side-specific observation/action prefix through frame; never offline safety labels',
            'cases':panel}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--path-list',type=Path,required=True)
    p.add_argument('--referee-dir',type=Path,required=True)
    p.add_argument('--census',type=Path,required=True)
    p.add_argument('--out-dir',type=Path,required=True)
    p.add_argument('--games',type=int,default=512)
    p.add_argument('--seed',type=int,default=20261025)
    a=p.parse_args()
    sys.path.insert(0,str(a.referee_dir))
    from referee import FowBoard, make_frame, outcome, position_key
    paths=sorted(set(Path(line.strip()).resolve() for line in a.path_list.read_text().splitlines() if line.strip()))
    selected=sorted(random.Random(a.seed).sample(paths,min(a.games,len(paths))))
    records=[]
    all_rows=[]
    games={}
    failures=[]
    frames=0
    for path in selected:
        record={'path':str(path.relative_to(ROOT)),'sha256':sha(path)}
        try:
            game,rows=audit(path,(FowBoard,make_frame,outcome,position_key))
        except (AssertionError,ValueError,KeyError,IndexError) as e:
            failures.append({**record,'error':str(e)})
            records.append(record)
            continue
        game_id=game.get('id',path.parent.name)
        games[game_id]=(record,game)
        frames+=len(game['frames'])
        records.append({**record,'game':game_id,'frames':len(game['frames']),
                        'events':len(rows),'rulesVersion':game.get('rulesVersion'),
                        'source':game.get('source'),
                        'frames_without_clock_metadata':sum('clocks' not in f for f in game['frames'])})
        all_rows.extend(rows)
    cached=defaultdict(list)
    with gzip.open(a.census,'rt') as f:
        for line in f:
            row=json.loads(line)
            if row['game'] in games:
                cached[row['game']].append(row)
    fresh=defaultdict(list)
    for row in all_rows:
        fresh[row['game']].append(row)
    for game_id in games:
        assert len(cached[game_id])==len(fresh[game_id]), ('cached count',game_id)
        for old,new in zip(cached[game_id],fresh[game_id]):
            for key,value in new.items():
                if key!='safe_replies':
                    assert old[key]==value, ('cached mismatch',game_id,new['ply'],key)
    forced=Counter(r['visibility'] for r in all_rows if r['safe_replies']==[])
    report={'classification':'independent sample audit and descriptive analysis, not an Elo estimate',
            'path_list_sha256':sha(a.path_list),'census_sha256':sha(a.census),
            'referee_sha256':sha(a.referee_dir/'referee.py'),
            'scanner_sha256':sha(Path(__file__).with_name('scan_hidden_king_arrivals.py')),
            'seed':a.seed,'population_games':len(paths),'sampled_games':len(selected),
            'validated_games':len(games),'validated_frames':frames,
            'games_without_complete_clock_metadata':sum(
                any('clocks' not in f for f in game['frames']) for _,game in games.values()),
            'attacker_set_comparisons':frames*2,'validated_events':len(all_rows),
            'failures':failures,'answered_events_without_safe_reply':dict(forced),
            'all_answered_events':summary(all_rows,list(games),False),
            'events_with_at_least_one_safe_reply':summary(all_rows,list(games),True),
            'limitations':['Random sample of an existing top-name-filtered corpus, not all arena games.',
                          'Cluster intervals are approximate and do not remove opponent or position confounding.',
                          'Safe means avoids immediate king loss; no claim of eventual winning value.',
                          'Diagnostic sample is not guaranteed unseen by earlier fitted models.']}
    a.out_dir.mkdir(parents=True,exist_ok=True)
    (a.out_dir/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    (a.out_dir/'sample-manifest.json').write_text(json.dumps(records,indent=2)+'\n')
    (a.out_dir/'teacher-readiness-panel.json').write_text(json.dumps(make_panel(all_rows,games,a.seed),indent=2)+'\n')
    with gzip.open(a.out_dir/'events.jsonl.gz','wt') as f:
        for row in all_rows:f.write(json.dumps(row,separators=(',',':'))+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
