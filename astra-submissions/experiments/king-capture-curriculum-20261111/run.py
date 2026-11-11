"""Build and audit a focused view of already existing counterfactual targets."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import fcntl
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import sqlite3
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "astra-submissions/analysis/king-capture-curriculum-20261111"
sys.path[:0] = [str(ROOT), str(ROOT / "astra-submissions/tools")]
import king_capture_curriculum as curriculum


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=1, sort_keys=True, allow_nan=False)
        stream.write("\n")


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
                purpose="415 all-king-capture curriculum/legacy-offer audit; no fit/search/GPU/API"))
        state["updated"] = now()
        temporary = path.with_name(".cores-" + ident)
        temporary.write_text(json.dumps(state, indent=2) + "\n")
        os.replace(temporary, path)


def main():
    plan = json.loads((OUT / "plan.json").read_text())
    for rel, expected in {**plan["source_pins"], **plan["implementation_pins"]}.items():
        assert sha(ROOT / rel) == expected, rel
    assert not (OUT / "started.json").exists()
    private = Path(plan["execution"]["private_output"])
    private.mkdir(exist_ok=False)
    ident = uuid.uuid4().hex
    lease(ident)
    started = time.monotonic()
    state = dict(status="running", started_at=now(), pid=os.getpid(), lease=ident)
    save(OUT / "started.json", state)
    os.sched_setaffinity(0, {4, 5})
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("fixed curation bound")))
    signal.alarm(plan["execution"]["maximum_seconds"])
    try:
        spec = importlib.util.spec_from_file_location("capture_referee", ROOT.parent / "fow-starter/referee.py")
        ref = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ref)
        import chess
        manifest_path = ROOT / plan["episodes"]
        manifest = json.loads(manifest_path.read_text())
        sources = json.loads((ROOT / "data/astra-spool/experience-catalogue-20261111/source-replays.json").read_text())
        source_by_id = {s["game"]: s for s in sources}
        old_rows = json.loads((ROOT / plan["old_rows"]).read_text())
        legacy = {(r["id"], 0 if r["side"] == "white" else 1, e["ply"] - 1, e["move"]): e
                  for r in old_rows for e in r["offers"]}
        assert len(legacy) == sum(len(r["offers"]) for r in old_rows) == 550
        actor_path = ROOT / "data/astra-spool/experience-catalogue-20261111/actors/actors.sqlite"
        result414 = json.loads((ROOT / "astra-submissions/analysis/experience-catalogue-20261111/result.json").read_text())
        actor_sha = sha(actor_path)
        assert actor_sha == result414["actor_index"]["database_sha256"]
        db = sqlite3.connect(actor_path.resolve().as_uri() + "?mode=ro", uri=True)
        db.row_factory = sqlite3.Row
        try:
            bindings = {(r["game"], r["side"], r["ply"]): dict(r) for r in db.execute(
                "SELECT e.game,e.source_sha256,d.* FROM decisions d JOIN episodes e ON e.id=d.episode")}
        finally:
            db.close()
        cases = defaultdict(lambda: defaultdict(list))
        ids, episodes_seen, folds = set(), set(), {}
        records = []
        input_hash = hashlib.sha256()
        shard_pins = {}
        for split, name in sorted(manifest["shards"].items()):
            path = Path(name)
            assert sha(path) == manifest["shard_sha256"][split]
            shard_pins[str(path)] = sha(path)
            with gzip.open(path, "rt") as stream:
                for line in stream:
                    episode = json.loads(line)
                    meta, actor = episode["metadata"], episode["actor"]
                    game = meta["game_id"]
                    assert meta["split"] == split
                    assert (game, actor["side"]) not in episodes_seen
                    episodes_seen.add((game, actor["side"]))
                    assert folds.setdefault(game, split) == split
                    assert meta["source_hash"] == source_by_id[game]["sha256"]
                    for row in curriculum.records(episode):
                        m, inputs = row["metadata"], row["inputs"]
                        key = (game, m["side"], m["ply"])
                        binding = bindings[key]
                        assert binding["source_sha256"] == m["source_sha256"]
                        for emitted, stored in (("observation", "observation"), ("last_seen", "memory"),
                                                ("ages", "ages"), ("rights", "rights"), ("legal", "legal")):
                            assert inputs[emitted] == binding[stored].hex()
                        assert inputs["en_passant"] == binding["ep"]
                        assert m["prefix_fingerprint"] == binding["history"].hex()
                        assert row["sample_id"] not in ids
                        ids.add(row["sample_id"])
                        input_hash.update(json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode() + b"\n")
                        cases[game][m["ply"]].append(row)
                        records.append(row)
        assert len(episodes_seen) == 736 and len(folds) == 368
        observed_legacy, frames, exact_capture_checks, complete_safe_sets = set(), 0, 0, 0
        contexts = Counter()
        per_cohort = defaultdict(Counter)
        for game in sorted(source_by_id):
            src = source_by_id[game]
            raw_path = ROOT / plan["raw_games"] / game / "replay.json"
            assert sha(raw_path) == src["sha256"] == sha(src["source"])
            replay = json.loads(raw_path.read_text())
            board = ref.FowBoard()
            repetitions = Counter({ref.position_key(board): 1})
            for ply, frame in enumerate(replay["frames"]):
                full = "".join(board.piece_at(s).symbol() if board.piece_at(s) else "-" for s in range(64))
                assert (frame["ply"], frame["board"], frame["white"], frame["black"]) == (
                    ply, full, ref.observation(board, True), ref.observation(board, False))
                frames += 1
                selected = cases[game].get(ply, [])
                if selected:
                    legal = list(ref.fow_moves(board))
                    safe, outcomes = [], {}
                    loss = "0-1" if board.turn else "1-0"
                    for candidate in legal:
                        trial = board.copy(stack=False)
                        trial.push(candidate)
                        key = ref.position_key(trial)
                        outcome = ref.outcome(trial, Counter({key: repetitions.get(key, 0) + 1}))
                        losing = outcome is not None and outcome[0] == loss
                        outcomes[candidate.uci()] = losing
                        if not losing:
                            safe.append(candidate.uci())
                    safe.sort()
                    complete_safe_sets += 1
                    for row in selected:
                        m, inputs, target = row["metadata"], row["inputs"], row["targets"]
                        assert m["side"] == (0 if board.turn else 1)
                        assert inputs["candidate"] in outcomes
                        assert target["king_loss"] == outcomes[inputs["candidate"]]
                        assert target["safe_alternatives"] == safe
                        assert target["played"] == (inputs["candidate"] == replay["frames"][ply + 1]["move"])
                        exact_capture_checks += 1
                        role = "fatal_hidden" if target["all_cover_hidden"] else "fatal_visible_or_mixed" if target["king_loss"] else "safe"
                        contexts[role] += 1
                        per_cohort[src["cohort"]][role] += 1
                        per_cohort[src["cohort"]][role + "_played"] += int(target["played"])
                        if target["all_cover_hidden"]:
                            key = (game, m["side"], ply, inputs["candidate"])
                            if src["cohort"] == "old327":
                                old = legacy[key]
                                assert old["piece"] == inputs["victim"]
                                assert sorted(old["cover"]) == sorted(k["square"] for k in target["cover"])
                                assert old["taken"] == target["played"] and old["avoidable"] == target["avoidable"]
                                assert sorted(old["safe_moves"]) == safe
                                observed_legacy.add(key)
                if ply + 1 < len(replay["frames"]):
                    assert ref.outcome(board, repetitions) is None
                    move = board.parse_uci(replay["frames"][ply + 1]["move"])
                    assert move in ref.fow_moves(board)
                    board.push(move)
                    repetitions[ref.position_key(board)] += 1
        assert observed_legacy == set(legacy)
        output = private / "candidates.jsonl.gz"
        with output.open("xb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as packed:
            with io.TextIOWrapper(packed, encoding="utf-8") as stream:
                for row in records:
                    stream.write(json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
        assert sha(actor_path) == actor_sha
        for path, expected in shard_pins.items():
            assert sha(path) == expected
        for src in sources:
            assert sha(src["source"]) == src["sha256"]
        private_bytes = sum(p.stat().st_size for p in private.rglob("*") if p.is_file())
        assert private_bytes <= plan["execution"]["maximum_private_bytes"]
        result = dict(at=now(), schema=curriculum.SCHEMA, games=368, episodes=736,
            decisions_in_source=31318, selected_candidate_records=len(records),
            selected_decisions=complete_safe_sets, full_course_frames=frames,
            exact_capture_outcome_checks=exact_capture_checks, complete_true_safe_sets=complete_safe_sets,
            old_hidden_offer_records_matched=len(observed_legacy), all550legacy_offers_reproduced=True,
            contexts=dict(contexts), contexts_by_cohort={k: dict(v) for k, v in per_cohort.items()},
            folds={k: sum(1 for row in records if row["metadata"]["split"] == k) for k in manifest["shards"]},
            chosen_capture_records=sum(r["targets"]["played"] for r in records),
            chosen_fatal_capture_records=sum(r["targets"]["played"] and r["targets"]["king_loss"] for r in records),
            optional_hidden_offers=sum(r["targets"]["all_cover_hidden"] and r["targets"]["avoidable"] for r in records),
            optional_hidden_offers_taken=sum(r["targets"]["all_cover_hidden"] and r["targets"]["avoidable"] and r["targets"]["played"] for r in records),
            invalid_imitation_records=sum(not r["targets"]["choice_valid"] for r in records),
            features_logical_sha256=input_hash.hexdigest(), output=str(output), output_sha256=sha(output),
            output_bytes=output.stat().st_size, private_artifact_bytes=private_bytes,
            all_actor_prefix_bindings_match=True, all_source_replays_shards_and_actor_index_unchanged=True,
            source_shards=shard_pins, seconds=time.monotonic() - started, limits=plan["limits"])
        assert result["chosen_fatal_capture_records"] == 66
        save(OUT / "result.json", result)
        state.update(status="complete")
        print(json.dumps({k: result[k] for k in ("selected_candidate_records", "selected_decisions", "contexts",
            "old_hidden_offer_records_matched", "chosen_capture_records", "chosen_fatal_capture_records", "output_bytes")}), flush=True)
    except BaseException as exc:
        state.update(status="failed", error=repr(exc))
        raise
    finally:
        lease(ident, remove=True)
        state.update(ended_at=now(), seconds=time.monotonic() - started, own_lease_released=True)
        save(OUT / "execution.json", state)


if __name__ == "__main__":
    main()
