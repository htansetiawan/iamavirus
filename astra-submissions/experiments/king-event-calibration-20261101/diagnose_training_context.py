#!/usr/bin/env python3
"""Training-only risk stratification; no fitting or test-set access."""
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'astra-submissions/analysis/king-event-calibration-20261101'
plan=json.loads((DATA/'plan.json').read_text())
fit=json.loads((DATA/'calibration.json').read_text())
alpha,beta=fit['model']['intercept'],fit['model']['slope']
groups=defaultdict(lambda:{'rows':0,'events':0,'weight':0.,'observed':0.,'raw':0.,'calibrated':0.,'raw_log_loss':0.,'calibrated_log_loss':0.,'games':set()})
read_games=[]
for game in plan['games']:
    if game['split']!='train':continue
    game_id=game['game'] if 'game' in game else game['id']
    path=DATA/'games'/f'{game_id}.jsonl'
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest==fit['data_sha256'][game_id]
    read_games.append(game_id)
    for line in path.read_text().splitlines():
        row=json.loads(line);assert row['split']=='train'
        p=max(1e-6,min(1-1e-6,row['sharp']))
        q=1/(1+math.exp(-(alpha+beta*(math.log(p)-math.log1p(-p)))))
        y=row['fatal'];king='king_move' if row['king_move'] else 'other_move'
        risk='raw_under_1pct' if row['sharp']<.01 else 'raw_1_to_3pct' if row['sharp']<.03 else 'raw_3_to_10pct' if row['sharp']<.1 else 'raw_over_10pct'
        size='worlds_le_32' if row['worlds']<=32 else 'worlds_gt_32'
        for seat in ('all_candidates','played') if row['played'] else ('all_candidates',):
            weight=1.0 if seat=='played' else row['decision_weight']
            for name in ('all',king,size,king+'/'+risk):
                g=groups[seat+'/'+name];g['rows']+=1;g['events']+=y;g['weight']+=weight;g['observed']+=weight*y
                g['raw']+=weight*row['sharp'];g['calibrated']+=weight*q;g['games'].add(game_id)
                for label,prob in (('raw_log_loss',p),('calibrated_log_loss',q)):
                    g[label]+=weight*(-math.log(prob) if y else -math.log1p(-prob))
assert len(read_games)==80
output={}
for name,g in sorted(groups.items()):
    weight=g['weight'];g['games']=len(g['games'])
    for field in ('observed','raw','calibrated','raw_log_loss','calibrated_log_loss'):g[field]/=weight
    output[name]=g
report={'scope':'Exploratory training-only stratification, no fitted change and no generalization claim. Decision weights are inherited; subgroup rows are correlated within games.','games_read':read_games,'test_games_read':0,'validation_games_read':0,'groups':output}
(DATA/'training-context-diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
for name in ('all_candidates/king_move','all_candidates/other_move','played/king_move','played/other_move'):
    print(name,json.dumps(output[name]))
