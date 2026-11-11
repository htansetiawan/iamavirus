"""Fixed functional/memory screen for the existing offline actor retriever."""
import argparse
import ast
import gc
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sqlite3
import struct
import subprocess
import sys
import time
import tracemalloc

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "astra-submissions/analysis/experience-query-stream-20261111"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    spec = importlib.util.spec_from_file_location("query_variant", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def logical(answer):
    return {key: value for key, value in answer.items() if key != "elapsed_ms"}


def measure(module_path, database, view):
    module = load(module_path)
    gc.collect()
    tracemalloc.start()
    started = time.monotonic()
    result = module.query(Path(database), view, 0, top=10, budget=100000)
    elapsed = time.monotonic() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(json.dumps({"Python_peak_bytes": peak, "elapsed_seconds": elapsed,
                      "logical_result": logical(result)}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--new-source", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    from learning import _native, dataset
    plan = json.loads((OUT / "plan.json").read_text())
    private = Path(plan["private_output"])
    baseline_path = private / "baseline.py"
    assert sha(baseline_path) == plan["baseline_source_sha256"]
    original, changed = load(baseline_path), load(args.new_source)
    outside_query = lambda path: [ast.dump(node, include_attributes=False)
        for node in ast.parse(Path(path).read_text()).body
        if not isinstance(node, ast.FunctionDef) or node.name != "query"]
    assert outside_query(baseline_path) == outside_query(args.new_source)
    native = ROOT / "astra-submissions/experiments/last-only-pilot-20261110/build/native-validator.so"
    assert sha(native) == "ae7a39913fe9d058b4b5392849ffc6a9260d2123a891d12454b016b4843665e3"
    assert _native._library is None
    _native.ensure_built = lambda verbose=True: native
    ingest_result = json.loads((ROOT / "astra-submissions/analysis/checkpoint-ingest-20261111T1745Z/result.json").read_text())
    source_plan = json.loads((ROOT / plan["real_data"]["game_ids_from"]).read_text())
    raw = private / "real/raw"
    raw.mkdir(parents=True, exist_ok=False)
    start, end = (ingest_result[key]["bytes"] for key in ("journal_before", "journal_after"))
    with (ROOT / "data/raw/accepted.jsonl").open("rb") as stream:
        stream.seek(start)
        tail = stream.read(end - start)
    rows = [json.loads(line) for line in tail.splitlines()]
    assert {row["id"] for row in rows} == set(source_plan["completed_game_ids"]) and len(rows) == 68
    (raw / "accepted.jsonl").write_bytes(tail)
    for row in rows:
        folder = raw / "games" / row["id"]
        folder.mkdir(parents=True)
        source = ROOT / "data/raw/games" / row["id"] / "replay.json"
        metadata = json.loads(source.with_name("fetch_metadata.json").read_text())
        assert sha(source) == metadata["replay"]["sha256"]
        shutil.copyfile(source, folder / "replay.json")
    manifest_path = private / "real/episodes.json"
    manifest = dataset.build_dataset(raw, manifest_path, "review", split_policy="trajectory-hash-v1")
    assert not manifest["candidate_mismatches"]
    changed.build(manifest_path, raw / "accepted.jsonl", private / "real/index")
    database = private / "real/index/actors.sqlite"
    database_sha = sha(database)
    wanted = {(item["game"], item["ply"]) for item in plan["real_data"]["queries"]}
    episodes = {}
    for path in manifest["shards"].values():
        for episode in dataset.load_episodes(Path(path)):
            episodes[(episode.metadata.game_id, episode.actor.side)] = episode
    real_results = []
    for game, ply in sorted(wanted):
        episode = episodes[(game, ply % 2)]
        record = episode.to_dict()["actor"]
        view = record["observations"][record["plies"].index(ply)]
        before = original.query(database, view, ply % 2, top=10, budget=2048, exclude_game=game)
        after = changed.query(database, view, ply % 2, top=10, budget=2048, exclude_game=game)
        assert logical(before) == logical(after)
        real_results.append({"game": game, "ply": ply, "result": logical(after)})
    assert sha(database) == database_sha
    print("Five fixed real-query comparisons pass", flush=True)
    synthetic = private / "synthetic.sqlite"
    db = sqlite3.connect(synthetic)
    db.executescript(original.DDL)
    db.execute("INSERT INTO episodes VALUES(NULL,?,?,?,?,?,?,?,?,?)",
               ("synthetic", 0, "train", "fixture", "fixture", "null", "null", "synthetic", "synthetic"))
    view = list("?" * 64)
    view[4], view[15], view[23], view[31] = "K", "P", "-", "-"
    query_view = "".join(view)
    def synthetic_rows():
        for i in range(100000):
            candidate = list(query_view)
            if i < 99000:
                candidate[40 + i % 8] = "r"
            packed = original.pack_view("".join(candidate))
            yield (1, "train", 0, i, 2 * i, 0 if i == 0 else 2,
                   struct.pack("<I", i).ljust(32, b"\0"), packed, packed,
                   bytes(64), bytes(8), -1, original.pack_move("e1d1"), 4, 2)
    db.executemany("INSERT INTO decisions VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", synthetic_rows())
    db.execute("ANALYZE")
    db.commit()
    db.close()
    arms = {}
    for name, module_path in (("baseline", baseline_path), ("stream", args.new_source)):
        completed = subprocess.run([sys.executable, str(Path(__file__).resolve()), "measure",
                                    str(module_path), str(synthetic), query_view],
                                   text=True, capture_output=True, check=True, timeout=150)
        arms[name] = json.loads(completed.stdout)
    assert arms["baseline"]["logical_result"] == arms["stream"]["logical_result"]
    assert [row["decision_id"] for row in arms["stream"]["logical_result"]["matches"]] == list(range(99001, 99011))
    ratio = arms["stream"]["Python_peak_bytes"] / arms["baseline"]["Python_peak_bytes"]
    artifact_bytes = sum(path.stat().st_size for path in private.rglob("*") if path.is_file())
    assert artifact_bytes <= plan["maximum_private_bytes"]
    result = {"baseline_sha256": sha(baseline_path), "stream_sha256": sha(args.new_source),
              "AST_unchanged_outside_query": True, "real_games": 68,
              "real_candidate_mismatches": 0, "real_query_parity": real_results,
              "real_actor_database_sha256": database_sha,
              "real_actor_database_unchanged_by_queries": True,
              "real_index_manifest": json.loads((private / "real/index/manifest.json").read_text()),
              "synthetic_is_not_a_chess_corpus": True, "synthetic_rows": 100000,
              "memory_arms": arms, "stream_to_baseline_Python_peak_ratio": ratio,
              "fixed_memory_gate_passed": ratio <= .1, "private_artifact_bytes": artifact_bytes,
              "limits": ["Python traced allocations only; not RSS or SQLite internal memory.",
                         "One fixed memory screen, no latency or playing-strength conclusion.",
                         "Historical actor retrieval is not a learned strategy or a globally nearest-neighbor guarantee.",
                         "No oracle label bridge, model, GPU, arena version or website deployment."]}
    with (OUT / "result.json").open("x") as stream:
        json.dump(result, stream, indent=1, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"Python_peak_ratio": ratio, "gate_passed": ratio <= .1,
                      "real_queries": len(real_results), "private_bytes": artifact_bytes}), flush=True)
    return 0 if ratio <= .1 else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "measure":
        measure(*sys.argv[2:])
    else:
        raise SystemExit(main())
