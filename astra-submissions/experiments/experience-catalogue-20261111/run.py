"""Materialize an analyst catalogue from inspected data; no model or bot search."""
from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "astra-submissions/analysis/experience-catalogue-20261111"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "astra-submissions/tools"))
import experience_catalogue as catalogue
from learning import dataset, ingest, _native


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=1, sort_keys=True, allow_nan=False)
        stream.write("\n")


def logical(answer):
    return {key: value for key, value in answer.items() if key != "elapsed_ms"}


def lease(ident, remove=False):
    path = ROOT / "chatroom/cores.json"
    with Path("/tmp/iamavirus-cores-json.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.loads(path.read_text())
        if remove:
            state["allocation"] = [r for r in state["allocation"] if r.get("lease") != ident]
        else:
            assert not any(set(r.get("cores", [])) & {4, 5} for r in state["allocation"])
            state["allocation"].append(dict(owner="astra", cores=[4, 5], lease=ident,
                purpose="414 analyst catalogue materialization; inspected300+68games, no model/bot/GPU/API"))
        state["updated"] = now()
        temp = path.with_name(".cores-" + ident)
        temp.write_text(json.dumps(state, indent=2) + "\n")
        os.replace(temp, path)


def main():
    plan = json.loads((OUT / "plan.json").read_text())
    for rel, expected in plan["source_pins"].items():
        assert sha(ROOT / rel) == expected, rel
    for rel, expected in plan["implementation_pins"].items():
        assert sha(ROOT / rel) == expected, rel
    assert not (OUT / "started.json").exists()
    private = Path(plan["execution"]["private_output"])
    private.mkdir(exist_ok=False)
    ident = uuid.uuid4().hex
    lease(ident)
    started = time.monotonic()
    state = dict(status="running", started_at=now(), pid=os.getpid(), lease=ident)
    save(OUT / "started.json", state)
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("fixed curation bound")))
    signal.alarm(plan["execution"]["maximum_seconds"])
    os.sched_setaffinity(0, {4, 5})
    try:
        source = ROOT / "astra-submissions/experiments/terminal-motifs-20261110/labels.py"
        spec = importlib.util.spec_from_file_location("existing_terminal_labels", source)
        labels = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(labels)
        ref, chess, native = labels.ref, labels.chess, labels.Native()
        old_plan = json.loads((ROOT / plan["cohorts"]["old_game_source"]).read_text())
        old_cohort = json.loads(Path(old_plan["cohort"]).read_text())["games"]
        rows = json.loads((ROOT / "data/astra-spool/terminal-motifs-20261110/rows.json").read_text())
        original_old_rows = json.dumps(rows, sort_keys=True)
        current = json.loads((ROOT / plan["cohorts"]["current_game_source"]).read_text())["completed_game_ids"]
        old_by_id = {g["game"]: g for g in old_cohort}
        old_ids = set(old_by_id)
        assert len(old_cohort) == len(old_ids) == 300 and len(rows) == 600
        assert len(current) == len(set(current)) == 68 and not old_ids & set(current)
        replays, sources, accepted = {}, [], []
        raw = private / "raw"
        for game in sorted(old_ids | set(current)):
            old = old_by_id.get(game)
            src = ((Path(old_plan["raw"]) / game / "replay.json") if old else
                   ROOT / "data/astra-spool/experience-query-stream-20261111/real/raw/games" / game / "replay.json")
            expected = old["replay_sha256"] if old else json.loads(
                (ROOT / "data/raw/games" / game / "fetch_metadata.json").read_text())["replay"]["sha256"]
            assert sha(src) == expected
            target = raw / "games" / game / "replay.json"
            target.parent.mkdir(parents=True)
            shutil.copyfile(src, target)
            replay = json.loads(target.read_bytes())
            replays[game] = replay
            sources.append(dict(game=game, source=str(src), sha256=expected,
                                cohort="old327" if old else "current68"))
            accepted.append(dict(id=game, moves_sha256=ingest.replay_hash(replay),
                **{key: replay.get(key) for key in ("createdAt", "white", "black", "whitePlayerId",
                                                  "blackPlayerId", "whiteVersion", "blackVersion")}))
        (raw / "accepted.jsonl").write_text("".join(json.dumps(r) + "\n" for r in accepted))
        fresh_frames = fresh_alternatives = fresh_terminals = 0
        for game in current:
            replay = replays[game]
            board = ref.FowBoard()
            repetitions = Counter({ref.position_key(board): 1})
            parent = parent_repetitions = None
            for ply, frame in enumerate(replay["frames"]):
                if ply:
                    assert ref.outcome(board, repetitions) is None
                    move = board.parse_uci(frame["move"])
                    assert move in ref.fow_moves(board)
                    parent = board.copy(stack=False)
                    if ply == len(replay["frames"]) - 1:
                        parent_repetitions = repetitions.copy()
                    board.push(move)
                    repetitions[ref.position_key(board)] += 1
                full = "".join(board.piece_at(s).symbol() if board.piece_at(s) else "-" for s in range(64))
                assert (frame["ply"], frame["board"], frame["white"], frame["black"]) == (
                    ply, full, ref.observation(board, True), ref.observation(board, False))
                fresh_frames += 1
            event = None
            n = len(replay["frames"]) - 1
            if replay["reason"] == "King capturable":
                event = labels.terminal(parent, chess.Move.from_uci(replay["frames"][-1]["move"]),
                                        native, parent_repetitions)
                fresh_alternatives += len(ref.fow_moves(parent))
                fresh_terminals += 1
                mover = "white" if n % 2 else "black"
                for killer in event["killers"]:
                    sq = chess.parse_square(killer["square"])
                    symbol = replay["frames"][-1]["board"][sq]
                    arrivals = [i for i in range(1, n) if replay["frames"][i]["board"][sq] == symbol
                                and replay["frames"][i - 1]["board"][sq] != symbol]
                    arrival = max(arrivals, default=0)
                    killer.update(last_arrival_ply=arrival, plies_since_arrival=n - arrival,
                        hidden_at_every_frame_since_arrival=all(
                            f[mover][sq] == "?" for f in replay["frames"][arrival:n]))
            for side in ("white", "black"):
                rows.append(dict(id=game, side=side, plies=n,
                    source_sha256=sha(raw / "games" / game / "replay.json"),
                    terminal_motif=event if event and (n - 1) % 2 == (0 if side == "white" else 1) else None))
        assert json.dumps(rows[:600], sort_keys=True) == original_old_rows
        save(private / "rows.json", rows)
        save(private / "source-replays.json", sources)
        cat_db = private / "catalogue.sqlite"
        cat_manifest = catalogue.build(private / "rows.json", raw / "games", cat_db)
        print(json.dumps({"catalogue": cat_manifest, "new_frames": fresh_frames}), flush=True)
        native_path = ROOT / "astra-submissions/experiments/last-only-pilot-20261110/build/native-validator.so"
        assert sha(native_path) == "ae7a39913fe9d058b4b5392849ffc6a9260d2123a891d12454b016b4843665e3"
        assert _native._library is None
        _native.ensure_built = lambda verbose=True: native_path
        episodes_path = private / "episodes.json"
        manifest = dataset.build_dataset(raw, episodes_path, "analyst-review", split_policy="trajectory-hash-v1")
        assert not manifest["candidate_mismatches"]
        catalogue.actors.build(episodes_path, raw / "accepted.jsonl", private / "actors")
        actor_db = private / "actors/actors.sqlite"
        frozen = {str(p): sha(p) for p in (actor_db, cat_db, private / "rows.json")}
        queries = []
        for item in plan["queries"]:
            game, ply = item["game"], item["ply"]
            view = replays[game]["frames"][ply]["white" if ply % 2 == 0 else "black"]
            before = catalogue.actors.query(actor_db, view, ply % 2, top=10, budget=2048, exclude_game=game)
            after = catalogue.query(actor_db, cat_db, view, ply % 2, top=10, budget=2048, exclude_game=game)
            assert logical(before) == logical(after["actor_result"])
            queries.append(dict(game=game, ply=ply, result=after))
        with catalogue.readonly(actor_db) as adb, catalogue.readonly(cat_db) as cdb:
            binding = None
            for m in cdb.execute("SELECT game,side,ply FROM motifs ORDER BY game,side,ply"):
                match = adb.execute("SELECT d.id,d.history,d.observation FROM decisions d JOIN episodes e ON "
                    "d.episode=e.id WHERE e.game=? AND d.side=? AND d.ply=? AND d.split='train'", tuple(m)).fetchone()
                if match:
                    binding = dict(game=m["game"], side=m["side"], ply=m["ply"], id=match["id"],
                                   history=match["history"], view=catalogue.actors.unpack_view(match["observation"]))
                    break
            assert binding is not None
        control = catalogue.query(actor_db, cat_db, binding["view"], binding["side"],
                                  top=10, budget=2048, history=binding["history"])
        assert control["oracle_annotations"][str(binding["id"])]["status"] == "labelled_terminal"
        browse = catalogue.browse(cat_db, kind="king_bait", attacker="R", all_hidden=True, forced=False, limit=10)
        assert browse["matches"]
        for example in browse["matches"]:
            label = example["oracle_label"]
            assert label["kind"] == "king_bait" and not label["forced_one_ply_loss"]
            assert label["all_killers_hidden"] and any(k["piece"] == "R" for k in label["killers"])
        for path, expected in frozen.items():
            assert sha(path) == expected
        for source in sources:
            assert sha(source["source"]) == source["sha256"]
        save(private / "queries.json", queries)
        save(private / "browse.json", browse)
        private_bytes = sum(p.stat().st_size for p in private.rglob("*") if p.is_file())
        assert private_bytes <= plan["execution"]["maximum_private_bytes"]
        result = dict(at=now(), games=368, old_seat_rows_unchanged=True,
            fresh_course_frames=fresh_frames, fresh_native_terminal_alternatives=fresh_alternatives,
            fresh_terminal_examples=fresh_terminals, catalogue=cat_manifest,
            actor_index=json.loads((private / "actors/manifest.json").read_text()),
            fixed_queries=[dict(game=q["game"], ply=q["ply"], candidates=q["result"]["actor_result"]["candidates_examined"],
                truncated=q["result"]["actor_result"]["truncated"],
                annotation_statuses=dict(Counter(a["status"] for a in q["result"]["oracle_annotations"].values())))
                for q in queries],
            all_seven_actor_result_fields_and_ranks_unchanged=True,
            self_reference_binding_control={k: binding[k] for k in ("game", "side", "ply", "id")},
            self_reference_control_is_not_quality_evidence=True,
            browse_example_count=len(browse["matches"]),
            read_databases_and_all_source_replays_unchanged=True,
            private_artifact_bytes=private_bytes,
            private_hashes={str(p): sha(p) for p in (private / "rows.json", private / "source-replays.json",
                private / "queries.json", private / "browse.json", actor_db, cat_db)},
            seconds=time.monotonic() - started, limits=plan["limits"])
        save(OUT / "result.json", result)
        state.update(status="complete")
        print(json.dumps({k: result[k] for k in ("games", "fresh_terminal_examples", "fixed_queries", "private_artifact_bytes")}), flush=True)
    except BaseException as exc:
        state.update(status="failed", error=repr(exc))
        raise
    finally:
        lease(ident, remove=True)
        state.update(ended_at=now(), seconds=time.monotonic() - started, own_lease_released=True)
        save(OUT / "execution.json", state)


if __name__ == "__main__":
    main()
