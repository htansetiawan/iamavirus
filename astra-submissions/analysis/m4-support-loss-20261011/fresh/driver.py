from pathlib import Path
import gzip,json,hashlib,shutil,importlib.util,sys
from collections import Counter

repo=Path('/home/henrytan/git/iamavirus')
src=Path('/media/henrytan/seagate/iamavirus/astra/arena-monitor')
out=Path('/media/henrytan/seagate/iamavirus/astra/m4-fresh-20261011-1712')
out.mkdir(exist_ok=False)
snapshot=json.loads((src/'latest.json').read_text())
assert snapshot['at']=='2026-10-11T17:12:20.918976+00:00'
shutil.copyfile(src/'latest.json',out/'snapshot.json')
shutil.copyfile(__file__,out/'driver.py')
shutil.copyfile(repo/'astra-submissions/tools/m4_match_audit.py',out/'audit.py')
shutil.copyfile('/media/henrytan/seagate/iamavirus/astra/m4-fresh-20261011-1544/referee.py',out/'referee.py')
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
auditor=module('auditor',out/'audit.py');referee=module('referee',out/'referee.py')
rows=[];inventory=[]
for event in snapshot['new_results']:
    path=src/'replays'/(event['game']+'.json.gz');raw=path.read_bytes();game=json.loads(gzip.decompress(raw))
    assert game['rulesVersion']=='fow-v1'
    (out/path.name).write_bytes(raw)
    record=auditor.audit(game,event['side'],referee);record.update(opponent=event['opponent'],arena_version=event['arena_version'],team_result=event['result'])
    rows.append(record);inventory.append({'game':game['id'],'replay_sha256':hashlib.sha256(raw).hexdigest()})
    print(json.dumps({'id':game['id'],'frames_validated':record['frames_validated']}),flush=True)
(out/'audit.json').write_text(json.dumps({'games':rows},indent=2)+'\n')
losses=[]
for row in rows:
    if row['team_result']!='L':continue
    d=row['decisions'][-1]
    losses.append({'game':row['id'],'opponent':row['opponent'],'ply':d['ply'],'material_cp':d['material_cp'],
                   'safe_actions':len(d['safe_moves']),'move':d['move'],'attackers_before':d['attackers_before'],
                   'terminal_attackers':row['terminal_attackers'],'observation_changed':d['opponent_move_changed_view']})
result={'games':len(rows),'frames':sum(r['frames_validated'] for r in rows),'record':dict(Counter(r['team_result'] for r in rows)),
        'losses':losses,'replays':inventory,'tool_sha256':hashlib.sha256((out/'audit.py').read_bytes()).hexdigest(),
        'referee_sha256':hashlib.sha256((out/'referee.py').read_bytes()).hexdigest()}
(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['replays','losses']}),flush=True)
