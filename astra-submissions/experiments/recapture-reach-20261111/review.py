"""Review saved census coverage/labels; do not invoke a native helper or policy."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/"astra-submissions/analysis/recapture-reach-20261111"
PRIVATE=ROOT/"data/astra-spool/recapture-reach-20261111"


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    plan=read(OUT/"plan.json");result=read(OUT/"result.json");selection=read(OUT/"selected-games.json")
    for path,expected in plan["source_pins"].items():assert sha(path)==expected,path
    for path,expected in result["private_hashes"].items():assert sha(path)==expected,path
    oracle=load(ROOT/"astra-submissions/experiments/promotion-ledger-20261110/check.py","independent_course_labels");ref=oracle.ref
    with gzip.open(PRIVATE/"decisions.jsonl.gz","rt") as f:rows=[json.loads(line) for line in f]
    with gzip.open(PRIVATE/"changed-actions.jsonl.gz","rt") as f:changes=[json.loads(line) for line in f]
    index={(r["game"],r["side"],r["ply"]):r for r in rows};assert len(index)==len(rows)==3798
    changed_index={(r["game"],r["side"],r["ply"],r["action"]):r for r in changes};assert len(changed_index)==len(changes)
    groups=defaultdict(Counter);count=Counter();expected_keys=set();ep_exclusions=[];played_differences=[];other_mismatches=[]
    for item in selection:
        path=ROOT/f"data/astra-spool/experience-catalogue-20261111/raw/games/{item['game']}/replay.json"
        assert sha(path)==item["source_sha256"];replay=read(path);board=ref.FowBoard();side=item["side"]
        group=groups[item["cohort"]];group["games"]+=1
        outcome="draw" if item["result"]=="1/2-1/2" else "win" if (item["result"]=="1-0")== (side==0) else "loss"
        group[outcome+"_games"]+=1;count["games"]+=1
        for ply,frame in enumerate(replay["frames"]):
            if ply:
                move=ref.chess.Move.from_uci(frame["move"]);assert move in ref.fow_moves(board);board.push(move)
            assert oracle.board_string(board)==frame["board"]
            assert ref.observation(board,True)==frame["white"] and ref.observation(board,False)==frame["black"]
            count["course_frames"]+=1;group["course_frames"]+=1
            if ply%2!=side or ply==len(replay["frames"])-1:continue
            identity=(item["game"],side,ply);expected_keys.add(identity);row=index[identity]
            assert row["source_sha256"]==item["source_sha256"] and row["cohort"]==item["cohort"] and row["outcome"]==outcome
            recorded=replay["frames"][ply+1]["move"];assert row["recorded"]==recorded
            legal={m.uci() for m in ref.fow_moves(board)};assert row["true_legal_choices"]==len(legal)
            view_actions=row["actions"][:row["view_choices"]];assert set(view_actions)<=legal
            for text in legal-set(view_actions):
                assert board.is_en_passant(ref.chess.Move.from_uci(text))
                ep_exclusions.append(dict(game=item["game"],side=side,ply=ply,move=text,played=text==recorded))
            assert row["actions"]==view_actions+([recorded] if recorded not in view_actions else [])
            assert len(row["flags"])==len(row["actions"]) and len(set(row["actions"]))==len(row["actions"])
            assert all(0<=flag<8 and (not flag&1 or flag&2) for flag in row["flags"])
            count["decisions"]+=1;group["decisions"]+=1
            for key,value in [("view_choices",len(view_actions)),("true_legal_choices",len(legal)),("native_king_checks",len(row["actions"]))]:count[key]+=value;group[key]+=value
            flag=row["flags"][row["actions"].index(recorded)];trial=board.copy();trial.push_uci(recorded)
            king=bool(oracle.lost(trial));assert king==bool(flag&4);group["played_king_losses"]+=king
            if king:assert row["actual_reference"] is None
            else:
                expected=oracle.reference(board,recorded);assert expected==row["actual_reference"]
                for label,pred in [("original",bool(flag&1)),("amended",bool(flag&2))]:
                    group[f"played_{label}_{int(pred)}_reference_{expected['risk']}"]+=1
                if bool(flag&1)!=bool(expected["risk"]):
                    record=dict(game=item["game"],side=side,ply=ply,action=recorded,flags=flag,course_reference=expected)
                    (played_differences if bool(flag&1)!=bool(flag&2) else other_mismatches).append(record)
            changed_at_root=[]
            for text,flag in zip(row["actions"],row["flags"]):
                changed=bool(flag&1)!=bool(flag&2);key=(*identity,text)
                assert changed==(key in changed_index)
                if not changed:continue
                candidate=changed_index[key];expected=oracle.reference(board,text)
                assert candidate["reference"]==expected and candidate["board"]==frame["board"] and candidate["view"]==frame[("white","black")[side]]
                assert candidate["played"]==(text==recorded) and candidate["original"]==bool(flag&1) and candidate["amended"]==bool(flag&2)
                assert candidate["source_sha256"]==item["source_sha256"] and candidate["outcome"]==outcome
                changed_at_root.append(text);group["changed_choices"]+=1;group["changed_choices_reference_"+str(expected["risk"])]+=1
                group["changed_choices_enemy_terminal"]+=candidate["enemy_terminal_approximation"]
                group["changed_choices_promotion"]+=candidate["promotion_approximation"]
                if text==recorded:group["changed_played_decisions"]+=1
            if changed_at_root:group["changed_decisions"]+=1
    assert expected_keys==set(index)
    for cohort,group in groups.items():
        chosen=[r for r in changes if r["cohort"]==cohort]
        group["changed_games"]=len({r["game"] for r in chosen})
        group["changed_played_games"]=len({r["game"] for r in chosen if r["played"]})
        assert dict(group)==result["cohorts"][cohort],cohort
    assert dict(count)==result["counts"]
    assert len(ep_exclusions)==7 and sum(r["played"] for r in ep_exclusions)==3
    receipt=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,counts=dict(count),cohort_aggregates_reproduced=True,
        changed_actions=len(changes),all_changed_course_references_checked=True,played_reference_differences=played_differences,
        unchanged_other_reference_mismatches=other_mismatches,conservative_view_ep_exclusions=ep_exclusions,
        no_native_reinvocation=True,source_sha256=sha(__file__),
        scope="Independent saved-record coverage/aggregate audit and course recheck of all actual moves and all changed actions. Original native king checks on every alternative were not repeated. No runtime posterior, policy or strength claim.")
    with (OUT/"record-review.json").open("x") as f:json.dump(receipt,f,indent=1,sort_keys=True,allow_nan=False);f.write("\n")
    print(json.dumps(dict(passed=True,decisions=count["decisions"],changed_actions=len(changes),en_passant_exclusions=len(ep_exclusions))))


if __name__=="__main__":main()
