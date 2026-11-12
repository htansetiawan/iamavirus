"""Descriptive version-aware matchups from the already cached release listing."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
SNAPSHOT=ROOT/"data/astra-spool/release-registry-20261111T220142Z"
OUT=ROOT/"astra-submissions/analysis/release-registry-20261111"
TEAM="a2c35173659545c99752376a70418438"


def record(counter):
    games=sum(counter.values())
    return dict(wins=counter["win"],draws=counter["draw"],losses=counter["loss"],games=games,
                score=(counter["win"]+.5*counter["draw"])/games if games else None)


def main():
    listing=json.loads((SNAPSHOT/"version-games/result.json").read_text())
    leaderboard=json.loads((SNAPSHOT/"leaderboard.json").read_text())
    all_teams=defaultdict(Counter);versions=defaultdict(lambda:defaultdict(Counter));total=Counter();inputs={}
    for number,receipt in enumerate(listing["receipts"]):
        path=SNAPSHOT/f"version-games/page-{number:03d}.json"
        digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest==receipt["sha256"];inputs[str(path)]=digest
        for game in json.loads(path.read_text())["games"]:
            seats=[side for side,key in enumerate(["white","black"]) if game.get(key+"PlayerId")==TEAM and game.get(key+"Version")==38];assert len(seats)==1
            side=seats[0];enemy=["black","white"][side];opponent=game[enemy+"PlayerId"];version=game[enemy+"Version"]
            outcome="draw" if game["result"]=="1/2-1/2" else "win" if (game["result"]=="1-0")== (side==0) else "loss"
            total[outcome]+=1;all_teams[opponent][outcome]+=1;versions[opponent][version][outcome]+=1
    assert dict(total)==listing["counts"] and sum(total.values())==listing["total"]
    rated=sorted([p for p in leaderboard["players"] if p.get("rating") is not None],key=lambda p:p["rating"],reverse=True)
    us=next(i for i,p in enumerate(rated) if p["id"]==TEAM);rows=[]
    for rank,player in enumerate(rated,1):
        if player["id"]==TEAM:continue
        identity=player["id"];current=player["activeVersion"]
        played=versions.get(identity,{})
        rows.append(dict(team_id=identity,name=player["name"],rating=player["rating"],visible_rank=rank,
            active_version=current,all_played_versions=record(all_teams.get(identity,Counter())),current_opponent_version=record(played.get(current,Counter())),
            played_versions={str(v):record(c) for v,c in played.items()}))
    result=dict(at=datetime.now(timezone.utc).isoformat(),team_version=38,our_metadata_rank=us+1,
        metadata_at=json.loads((SNAPSHOT/"receipts.json").read_text())[0]["fetched_at"],listing_at=listing["first_page_at"],
        total=record(total),above_us=[r for r in rows if r["visible_rank"]<us+1],all_visible_rated_opponents=rows,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),input_sha256=inputs,
        scope="All completed v38 games in one cached snapshot; current opponent versions/ratings are from an earlier metadata read. Opponent names are reporting labels, not runtime strategy selectors. Historical mix and small cells prevent causal strength claims.")
    with (OUT/"matchups.json").open("x") as f:json.dump(result,f,indent=1,sort_keys=True);f.write("\n")
    print(json.dumps(dict(total=result["total"],above_us=result["above_us"])))


if __name__=="__main__":main()
