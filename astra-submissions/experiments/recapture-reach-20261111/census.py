"""True-history reach audit; no deciding engine, new model or policy trial."""
from collections import Counter, defaultdict
import ctypes as C
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "astra-submissions/analysis/recapture-reach-20261111"
PRIVATE = ROOT / "data/astra-spool/recapture-reach-20261111"


def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    with Path(path).open("x") as f: json.dump(value,f,indent=1,sort_keys=True,allow_nan=False);f.write("\n")
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def details(board, text, oracle):
    """Expose the other known helper approximations without changing them."""
    ref=oracle.ref; us=board.turn; root=ref.chess.Move.from_uci(text)
    after=board.copy();after.push(root)
    events=[]
    for reply in ref.fow_moves(after):
        if after.piece_at(reply.to_square)!=ref.chess.Piece(ref.chess.QUEEN,us):continue
        child=after.copy();child.push(reply)
        nominal=sorted(ref.chess.square_name(s) for s in child.attackers(us,reply.to_square))
        safe=[]
        for recapture in ref.fow_moves(child):
            if recapture.to_square!=reply.to_square:continue
            trial=child.copy();trial.push(recapture)
            if not oracle.lost(trial):safe.append(recapture.uci())
        events.append(dict(reply=reply.uci(),capturer=after.piece_at(reply.from_square).symbol(),
            capturer_hidden_before=ref.observation(board,us)[reply.from_square]=="?",
            enemy_capture_loses_king=bool(oracle.lost(child)),capture_promotes=reply.promotion is not None,
            nominal_recapturers=nominal,safe_recaptures=sorted(safe),
            nominal_but_no_safe_recapture=bool(nominal) and not safe))
    return dict(root_promotes=root.promotion is not None,events=events,
        enemy_terminal_approximation=any(e["enemy_capture_loses_king"] for e in events),
        promotion_approximation=root.promotion is not None or any(e["capture_promotes"] for e in events))


def run():
    plan=read(OUT/"plan.json")
    for path,expected in plan["source_pins"].items():assert sha(path)==expected,path
    selection=read(OUT/"selected-games.json")
    leases=read(ROOT/"chatroom/cores.json")["allocation"]
    assert any(x.get("lease")=="418-recapture-reach" and x["cores"]==plan["cores"] for x in leases)
    assert not any(set(x.get("cores",[]))&set(plan["cores"]) for x in leases if x.get("lease")!="418-recapture-reach")
    os.sched_setaffinity(0,set(plan["cores"]))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError("600-second offline audit cap")))
    signal.alarm(plan["wall_seconds"])
    PRIVATE.mkdir(exist_ok=False)
    save(OUT/"started.json",dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),plan_sha256=sha(OUT/"plan.json")))
    prepare=load(ROOT/"astra-submissions/experiments/safe-recapture-20261111/prepare.py","recapture_probe")
    pair=load(ROOT/"astra-submissions/experiments/safe-recapture-20261111/pair.py","recapture_encodings")
    oracle=load(ROOT/"astra-submissions/experiments/promotion-ledger-20261110/check.py","course_exchange_oracle")
    ref=oracle.ref;lib=prepare.library()
    lib.view_moves.argtypes=[C.c_char_p,C.c_int,C.c_uint64,C.POINTER(pair.Moves)];lib.view_moves.restype=C.c_int
    counts=Counter();groups=defaultdict(Counter);changed=[];diagnostics=[];start=time.monotonic()
    paths=[PRIVATE/"decisions.jsonl.gz",PRIVATE/"changed-actions.jsonl.gz"]
    with paths[0].open("xb") as raw,gzip.GzipFile(filename="",fileobj=raw,mode="wb",mtime=0) as packed:
        for number,item in enumerate(selection):
            path=ROOT/f"data/astra-spool/experience-catalogue-20261111/raw/games/{item['game']}/replay.json"
            assert sha(path)==item["source_sha256"]
            replay=read(path);board=ref.FowBoard();side=item["side"];key=("white","black")[side]
            assert replay[key+"PlayerId"]==plan["team_id"] and replay[key+"Version"]==38
            group=groups[item["cohort"]];counts["games"]+=1;group["games"]+=1
            won=(replay["result"]=="1-0")==(side==0) if replay["result"]!="1/2-1/2" else None
            outcome="draw" if won is None else "win" if won else "loss"
            group[outcome+"_games"]+=1
            for ply,frame in enumerate(replay["frames"]):
                if ply:
                    move=ref.chess.Move.from_uci(frame["move"]);assert move in ref.fow_moves(board);board.push(move)
                assert oracle.board_string(board)==frame["board"]
                assert ref.observation(board,True)==frame["white"] and ref.observation(board,False)==frame["black"]
                counts["course_frames"]+=1;group["course_frames"]+=1
                if ply%2!=side or ply==len(replay["frames"])-1:continue
                counts["decisions"]+=1;group["decisions"]+=1
                current_view=frame[key];legal={m.uci() for m in ref.fow_moves(board)}
                moves=pair.Moves();lib.view_moves(current_view.encode(),side,int(board.castling_rights),C.byref(moves))
                actions=[pair.decoded(moves.moves[i]) for i in range(moves.count)]
                assert len(actions)==len(set(actions)) and set(actions)<=legal
                recorded=replay["frames"][ply+1]["move"];assert recorded in legal
                absent=recorded not in actions
                if absent:diagnostics.append(dict(game=item["game"],side=side,ply=ply,recorded=recorded,kind="recorded_move_outside_view_generator"))
                full_actions=actions+([recorded] if absent else [])
                counts["view_choices"]+=len(actions);group["view_choices"]+=len(actions)
                counts["true_legal_choices"]+=len(legal);group["true_legal_choices"]+=len(legal)
                flags=[];actual_reference=None;root_changes=[]
                for text in full_actions:
                    flag=lib.astra_flags(frame["board"].encode(),side,int(board.castling_rights),board.ep_square if board.ep_square is not None else -1,board.halfmove_clock,text.encode(),4)
                    assert 0<=flag<8
                    original,amended,king=(bool(flag&(1<<bit)) for bit in range(3))
                    assert not original or amended
                    trial=board.copy();trial.push_uci(text);assert king==bool(oracle.lost(trial))
                    counts["native_king_checks"]+=1;group["native_king_checks"]+=1
                    flags.append(flag);is_changed=original!=amended
                    if text==recorded:
                        group["played_king_losses"]+=king
                        if not king:
                            actual_reference=oracle.reference(board,text)
                            for label,prediction in [("original",original),("amended",amended)]:
                                group[f"played_{label}_{int(prediction)}_reference_{actual_reference['risk']}"]+=1
                    if is_changed:
                        assert not king
                        expected=actual_reference if text==recorded and actual_reference is not None else oracle.reference(board,text)
                        extra=details(board,text,oracle)
                        next_reply=replay["frames"][ply+2]["move"] if ply+2<len(replay["frames"]) else None
                        row=dict(game=item["game"],source_sha256=item["source_sha256"],cohort=item["cohort"],side=side,ply=ply,
                            outcome=outcome,opponent_id=item["opponent_id"],opponent_version=item["opponent_version"],
                            board=frame["board"],view=current_view,castle=f"{int(board.castling_rights):016x}",ep=board.ep_square,
                            halfmove=board.halfmove_clock,action=text,played=text==recorded,in_view_choices=text in actions,
                            original=original,amended=amended,reference=expected,**extra,
                            actual_next_reply=next_reply if text==recorded else None)
                        changed.append(row);root_changes.append(text)
                        group["changed_choices"]+=1;group["changed_choices_reference_"+str(expected["risk"])]+=1
                        group["changed_choices_enemy_terminal"]+=extra["enemy_terminal_approximation"]
                        group["changed_choices_promotion"]+=extra["promotion_approximation"]
                        if text==recorded:group["changed_played_decisions"]+=1
                if root_changes:group["changed_decisions"]+=1
                record=dict(game=item["game"],source_sha256=item["source_sha256"],cohort=item["cohort"],side=side,ply=ply,
                    outcome=outcome,recorded=recorded,actions=full_actions,view_choices=len(actions),true_legal_choices=len(legal),flags=flags,
                    actual_reference=actual_reference)
                packed.write((json.dumps(record,separators=(",",":"))+"\n").encode())
            if number%10==9:print(json.dumps(dict(games=number+1,decisions=counts["decisions"],changed_actions=len(changed))),flush=True)
    with paths[1].open("xb") as raw,gzip.GzipFile(filename="",fileobj=raw,mode="wb",mtime=0) as packed:
        for row in changed:packed.write((json.dumps(row,separators=(",",":"))+"\n").encode())
    for cohort,group in groups.items():
        selected=[r for r in changed if r["cohort"]==cohort]
        group["changed_games"]=len({r["game"] for r in selected})
        group["changed_played_games"]=len({r["game"] for r in selected if r["played"]})
    assert counts["games"]==plan["games"] and counts["decisions"]==plan["decisions"]
    assert sum(p.stat().st_size for p in PRIVATE.iterdir())<=plan["maximum_private_bytes"]
    result=dict(at=datetime.now(timezone.utc).isoformat(),seconds=time.monotonic()-start,counts=dict(counts),
        cohorts={k:dict(v) for k,v in groups.items()},changed_actions=len(changed),view_generator_diagnostics=diagnostics,
        changed_played_examples=[{k:r[k] for k in ["game","cohort","side","ply","action","outcome","original","amended","actual_next_reply"]}|dict(reference_risk=r["reference"]["risk"],enemy_terminal_approximation=r["enemy_terminal_approximation"],promotion_approximation=r["promotion_approximation"]) for r in changed if r["played"]],
        private_hashes={str(p):sha(p) for p in paths},private_bytes=sum(p.stat().st_size for p in PRIVATE.iterdir()),
        limits=plan["limits"])
    save(OUT/"result.json",result)
    print(json.dumps({k:v for k,v in result.items() if k not in ["changed_played_examples","private_hashes","limits"]}),flush=True)
    signal.alarm(0)


if __name__=="__main__":
    try:run()
    except BaseException as error:
        if not (OUT/"failure.json").exists():save(OUT/"failure.json",dict(at=datetime.now(timezone.utc).isoformat(),error=repr(error)))
        raise
