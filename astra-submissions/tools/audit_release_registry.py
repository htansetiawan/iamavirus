"""Read-only v38 package/registry audit using cached public API responses."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import urllib.parse
import zipfile
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[2]
TEAM="a2c35173659545c99752376a70418438"


def read(path):return json.loads(Path(path).read_text())
def sha(path):
    with Path(path).open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()
def member_sha(archive,name):
    with archive.open(name) as f:return hashlib.file_digest(f,"sha256").hexdigest()
def prefix(archive,expected):
    anchors=[n for n in archive.namelist() if (n=="run.sh" or n.endswith("/run.sh")) and member_sha(archive,n)==expected]
    assert len(anchors)==1,anchors
    return anchors[0][:-len("run.sh")]
def git(*args):return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()
def save(path,value):
    with Path(path).open("x") as f:json.dump(value,f,indent=1,sort_keys=True,allow_nan=False);f.write("\n")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot",type=Path,required=True)
    parser.add_argument("--published-commit",required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();assert re.fullmatch("[0-9a-f]{40}",args.published_commit)
    args.output.mkdir(exist_ok=False)
    manifest_path=ROOT/"astra-submissions/v38-manifest.json";manifest=read(manifest_path)
    archive_path=ROOT/"astra-submissions"/manifest["archive"];parent_path=ROOT/manifest["parent_archive"]
    assert sha(archive_path)==manifest["archive_sha256"] and archive_path.stat().st_size==manifest["archive_bytes"]
    assert sha(parent_path)==manifest["parent_sha256"]
    with zipfile.ZipFile(archive_path) as current,zipfile.ZipFile(parent_path) as parent:
        stem=prefix(current,manifest["source_sha256"]["run.sh"])
        native=set()
        for name,expected in manifest["source_sha256"].items():
            assert current.namelist().count(stem+name)==1 and member_sha(current,stem+name)==expected,name
            if name.startswith("src/") and name.endswith((".c",".h")):native.add(name)
        parent_launchers=[n for n in parent.namelist() if n=="run.sh" or n.endswith("/run.sh")]
        assert len(parent_launchers)==1;parent_stem=parent_launchers[0][:-len("run.sh")]
        now={n[len(stem):] for n in current.namelist() if n.startswith(stem) and not n.endswith("/")}
        before={n[len(parent_stem):] for n in parent.namelist() if n.startswith(parent_stem) and not n.endswith("/")}
        changed=sorted(n for n in now&before if member_sha(current,stem+n)!=member_sha(parent,parent_stem+n))
        assert changed==["bin/stockfish","run.sh"]
        assert len(native)==19 and all(member_sha(current,stem+n)==member_sha(parent,parent_stem+n) for n in native)
        source_commit=subprocess.check_output(["git","-C",str(ROOT.parent/"fowsearch-c"),"rev-parse",manifest["parent_source_commit"]+"^{commit}"],text=True).strip()
        for name in native:
            original=subprocess.check_output(["git","-C",str(ROOT.parent/"fowsearch-c"),"show",source_commit+":"+name])
            assert hashlib.sha256(original).hexdigest()==manifest["source_sha256"][name],name
        history=current.getinfo(stem+"data/history.bin")
        assert history.file_size==16+16*359889
        alias=ROOT/manifest["staged_archive"]
        assert alias.exists() and sha(alias)==manifest["archive_sha256"]
        embedded=json.loads(current.read(stem+"astra-release.json"))
        assert len(now-set(manifest["source_sha256"]))==1 and now-set(manifest["source_sha256"])=={"astra-release.json"}
    code=ROOT/"astra-submissions/tools/package_release.py"
    spec=importlib.util.spec_from_file_location("existing_numbering_guard",code);packager=importlib.util.module_from_spec(spec);spec.loader.exec_module(packager)
    required=packager.next_version();refusal=None
    try:packager.require_unused_version(required)
    except FileExistsError as error:refusal=str(error)
    assert required==38 and refusal
    rows={}
    for relative in ["fable-submissions/README.md","MUTATIONS.md"]:
        text=(ROOT/relative).read_text();matches=re.findall(r"^\| \*\*38\*\* \|.*$",text,re.M)
        assert len(matches)==1 and manifest["archive"] in matches[0] and manifest["archive_sha256"][:12] in matches[0]
        rows[relative]=dict(row=matches[0],sha256=sha(ROOT/relative))
    public_objects={}
    for path in [archive_path,manifest_path]:
        relative=str(path.relative_to(ROOT));tree_line=git("ls-tree",args.published_commit,"--",relative)
        assert tree_line;blob=tree_line.split()[2];assert git("hash-object","--no-filters",str(path))==blob
        public_objects[relative]=blob
    source_records=read(args.snapshot/"receipts.json")
    assert len(source_records)==2
    for name,record in zip(["leaderboard","versions"],source_records):
        assert record["status"]==200 and sha(args.snapshot/(name+".json"))==record["sha256"]
    leaderboard=read(args.snapshot/"leaderboard.json");versions=read(args.snapshot/"versions.json")
    player=next(p for p in leaderboard["players"] if p["id"]==TEAM)
    version=next(v for v in versions["versions"] if v["version"]==38)
    assert player["activeVersion"]==38 and version["active"]
    assert [version[k] for k in ["games","wins","draws","losses"]]==[player["activeRecord"][k] for k in ["games","wins","draws","losses"]]
    listing=read(args.snapshot/"version-games/result.json")
    games=[];next_cursor=None
    for number,record in enumerate(listing["receipts"]):
        path=args.snapshot/f"version-games/page-{number:03d}.json"
        assert sha(path)==record["sha256"] and record["status"]==200
        query=dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(record["url"]).query))
        expected={key:str(value) for key,value in listing["params"].items()}
        if next_cursor:expected["cursor"]=next_cursor
        assert query==expected
        page=read(path);assert page["sort"]=="played" and page["order"]=="desc"
        assert (page["summary"]["total"]==listing["total"]) if number==0 else page["summary"] is None
        games+=page["games"];next_cursor=page["nextCursor"]
    assert len(games)==listing["total"]==len(set(g["id"] for g in games))
    assert next_cursor is None
    outcomes=Counter();reasons={key:Counter() for key in ["win","draw","loss"]}
    for game in games:
        seats=[side for side,key in enumerate(["white","black"]) if game.get(key+"PlayerId")==TEAM and game.get(key+"Version")==38]
        assert len(seats)==1
        result=game["result"];assert result in ["1-0","0-1","1/2-1/2"]
        outcome="draw" if result=="1/2-1/2" else "win" if (result=="1-0")== (seats[0]==0) else "loss"
        outcomes[outcome]+=1;reasons[outcome][game["reason"]]+=1
    assert dict(outcomes)==listing["counts"] and {key:dict(value) for key,value in reasons.items()}==listing["reasons"]
    rated=sorted([p for p in leaderboard["players"] if p.get("rating") is not None],key=lambda p:p["rating"],reverse=True)
    rank=next(i+1 for i,p in enumerate(rated) if p["id"]==TEAM)
    at=datetime.fromisoformat(source_records[0]["fetched_at"].replace("Z","+00:00"))
    snapshot=dict(kind="Reduced projection; not the original API payload",fetched_at=source_records[0]["fetched_at"],
        boston_time=at.astimezone(ZoneInfo("America/New_York")).isoformat(),active_version=38,elo=player["rating"],
        visible_rated_rank=rank,active_record=player["activeRecord"],version=version,
        score=(version["wins"]+.5*version["draws"])/version["games"],
        sources=source_records,top_rated=[{k:p[k] for k in ["id","name","rating","activeVersion","staff","external"]} for p in rated[:12]],
        later_completed_game_snapshot={k:listing[k] for k in ["first_page_at","total","counts","reasons","pages","HTTP_attempts"]},
        metadata_and_listing_are_separate_snapshots=True)
    save(args.output/"arena-summary.json",snapshot)
    report=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,version=38,archive_sha256=sha(archive_path),archive_bytes=archive_path.stat().st_size,
        manifest_sha256=sha(manifest_path),manifest_members_verified=len(manifest["source_sha256"]),native_source_members=19,
        parent_source_commit=source_commit,parent_archive_sha256=sha(parent_path),changed_common_members=changed,
        staged_alias_same_bytes=True,embedded_status=embedded.get("status"),public_commit_provided=args.published_commit,matching_git_objects=public_objects,
        fable_highest_physical_archive=required-1,required_astra_version=required,occupied_version_refused=refusal,
        shared_registry_rows=rows,source_sha256=sha(__file__),numbering_guard_sha256=sha(code),
        snapshot_directory=str(args.snapshot),raw_inputs_unchanged=True,
        game_page_coverage_and_reductions_verified=True,
        limits=["The provided published commit is checked by its local Git objects; its remote-main identity was independently read with git ls-remote this turn.","The arena API provides version metadata but no uploaded ZIP checksum. Bytes-to-version association remains the recorded human upload and Fable same-bytes decision.","No archive/manifest was rewritten, package built, arena upload/activation or new version reservation made.","Elo and WDL are dated observations; local speed and arena retention are not a causal strength estimate."])
    save(args.output/"audit.json",report)
    print(json.dumps(dict(passed=True,manifest_members=report["manifest_members_verified"],public_git_objects=len(public_objects),
        active_version=38,elo=player["rating"],metadata_games=version["games"],later_listing_games=listing["total"],required_version_occupied=True)))


if __name__=="__main__":main()
