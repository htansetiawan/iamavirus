"""Public standings/listings only, usable while the raw drive is offline.

No replay downloads, RawStore, training input or arena mutation. One bounded
snapshot; this does not start a replacement persistent replay watcher.
"""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from learning.api_client import ApiClient

OWN='a2c35173659545c99752376a70418438'
NORMAL={'King capturable','Threefold repetition','Fifty-move rule','50-move rule',
        'Move limit reached','No legal moves','Stalemate','Insufficient material'}


def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    client=ApiClient(min_interval=1.2,timeout=30)
    def save(name,obj):
        raw=(json.dumps(obj,indent=2,allow_nan=False)+'\n').encode();(out/name).write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()
    board,fetch=client.leaderboard();save('leaderboard.json',dict(leaderboard=board,fetch=fetch.__dict__))
    params=dict(sort='played',order='desc',limit=100,colors='any',white='IAmAVirus v38')
    games=[];cursor=None;first=None
    for index in range(10):
        page,fetch=client.games_page(params,cursor)
        save(f'games-{index:03d}.json',dict(page=page,fetch=fetch.__dict__))
        assert page['sort']=='played' and page['order']=='desc'
        if first is None:first=page
        games.extend(page['games']);cursor=page['nextCursor']
        if cursor is None:break
    assert cursor is None,'bounded snapshot incomplete; do not report partial totals'
    assert len(games)==len({g['id'] for g in games})==first['summary']['total']
    wdl=[0,0,0];unusual=[]
    for g in games:
        assert re.fullmatch('[a-z0-9]{8}',g['id'])
        sides=[s for s in ('white','black') if g[s+'PlayerId']==OWN and g[s+'Version']==38]
        assert len(sides)==1,'ambiguous self-play or query mismatch'
        side=sides[0];draw=g['result']=='1/2-1/2';assert g['result'] in ('1-0','0-1','1/2-1/2')
        win=not draw and ((g['result']=='1-0')==(side=='white'));i=0 if win else 1 if draw else 2
        wdl[i]+=1
        if i==2 and g['reason'] not in NORMAL:unusual.append(dict(id=g['id'],reason=g['reason']))
    summary=first['summary']['team1'];assert summary['ambiguous']==0
    assert wdl==[summary[k] for k in ('wins','draws','losses')]
    players=sorted(board['players'],key=lambda p:-(p.get('rating') or 0))
    rank,ours=next((i+1,p) for i,p in enumerate(players) if p['id']==OWN)
    result=dict(at=datetime.now(timezone.utc).isoformat(),games=len(games),wdl=wdl,
        score=(wdl[0]+.5*wdl[1])/len(games),rating=ours['rating'],rank=rank,active_version=ours['activeVersion'],
        suspicious_nonboard_losses=unusual,requests=client.requests_made,
        scope='One complete public v38 listing snapshot plus leaderboard; no replay ingestion, raw-store write, model input or arena change.',
        limitation='Leaderboard and game-list snapshots are taken at different instants. This is monitoring metadata, not causal strength evidence.',
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    save('result.json',result);print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
