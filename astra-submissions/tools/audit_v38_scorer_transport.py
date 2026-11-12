#!/usr/bin/env python3
"""Read immutable sources and saved profiles; never run an engine or benchmark."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "astra-submissions/analysis/scorer-transport-audit-20261112"
PROFILE = ROOT / "astra-submissions/analysis/v38-search-cost-20261110"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit() -> dict:
    plan_path = OUT / "plan.json"
    plan = json.loads(plan_path.read_text())
    archive = ROOT / plan["archive"]
    assert sha(archive.read_bytes()) == plan["archive_sha256"]
    manifest_path = ROOT / "astra-submissions/v38-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    members = [
        "run.sh", "src/gtcfr.c", "src/sfeval.c",
        "third_party/stockfish19/src/search.cpp",
        "third_party/stockfish19/src/uci.cpp",
        "third_party/stockfish19/src/misc.h",
        "third_party/stockfish19/src/tt.cpp",
    ]
    pins = {str(p.relative_to(ROOT)): sha(p.read_bytes())
            for p in (plan_path, manifest_path, Path(__file__))}
    sources = {}
    with zipfile.ZipFile(archive) as z:
        for name in members:
            data = z.read(name)
            assert sha(data) == manifest["source_sha256"][name]
            sources[name] = data.decode()
    locations = []

    def at(name: str, needle: str, finding: str) -> None:
        source = sources[name]
        assert source.count(needle) == 1, (name, needle)
        start = source.index(needle)
        locations.append({"member": name, "member_sha256": sha(source.encode()),
                          "line": source[:start].count("\n") + 1,
                          "needle": needle, "finding": finding})

    launcher = sources["run.sh"]
    assert not re.search(r"^\s*(?:export\s+)?MIST_(ASYNC|ITERS)=", launcher, re.M)
    at("run.sh", "export ASTRA_SF_ALLCHILDREN=1", "Only the scorer mode is explicitly enabled here.")
    at("src/sfeval.c", 'int want = getenv("MIST_SF_WORKERS") ? atoi(getenv("MIST_SF_WORKERS")) : 2;', "Two workers by default.")
    at("src/gtcfr.c", 'const int async = W > 0 && getenv("MIST_ASYNC") && atoi(getenv("MIST_ASYNC")) != 0;', "Continuous pipeline is opt-in; no launcher override.")
    at("src/gtcfr.c", 'const double iters_per = getenv("MIST_ITERS") ? atof(getenv("MIST_ITERS")) : 0.3;', "MIST_ITERS is read inside the optional asynchronous branch.")
    at("src/gtcfr.c", "for (int i = 0; i < n; i += W)", "Default expansion submits a wave then collects its replies.")
    at("src/gtcfr.c", "while (!async && seconds_since(&t0) < params->seconds * 0.85)", "Default rounds run solver work before batched expansion.")
    g = sources["src/gtcfr.c"]
    batch = g[g.index("static int expand_batch("):g.index("static void ensure_visits(")]
    assert batch.index("sf_submit(") < batch.index("sf_collect(")
    assert g.count('getenv("MIST_ITERS")') == 2  # condition and value, one declaration
    at("src/sfeval.c", 'sscanf(pv + 4, "%7s", move);', "Parser reads the PV's first move.")
    at("src/sfeval.c", "if (strcmp(uci[i], move) == 0)", "Linear move matching for each accepted score line.")
    at("src/sfeval.c", 'if (strstr(line, "lowerbound") || strstr(line, "upperbound")) continue;', "Bound-only score lines are discarded.")
    s = "third_party/stockfish19/src/search.cpp"
    at(s, "for (pvIdx = 0; pvIdx < multiPV; ++pvIdx)", "Ordinary MultiPV runs repeated root searches.")
    at(s, "if ((!PvNode || moveCount > 1) && !(rootNode && astraAllChildren))", "All-child mode bypasses the ordinary non-PV root pass.")
    at(s, "if (PvNode && (moveCount == 1 || value > alpha || (rootNode && astraAllChildren)))", "Each all-child root move receives a PV search.")
    at(s, "if (rootNode && !std::count(rootMoves.begin() + pvIdx, rootMoves.begin() + pvLast, move))", "Root membership still scans a move range; whole scorer is not linear.")
    at(s, "RootMove& rm = *std::find(rootMoves.begin(), rootMoves.end(), move);", "Root score record lookup is still linear.")
    at(s, "info.hashfull  = tt.hashfull();", "Output construction recomputes table occupancy for each emitted PV.")
    at("third_party/stockfish19/src/uci.cpp", "void UCIEngine::on_update_full(const Engine::InfoFull& info, bool showWDL)", "Every full-info callback formats a line and requests a flush.")
    uci = sources["third_party/stockfish19/src/uci.cpp"]
    full_output = uci[uci.index("void UCIEngine::on_update_full("):uci.index("void UCIEngine::on_iter(")]
    assert "sync_cout << ss.str() << sync_endl;" in full_output
    at("third_party/stockfish19/src/misc.h", "#define sync_endl std::endl << IO_UNLOCK", "The output macro flushes the stream; source alone does not count syscalls.")
    at("third_party/stockfish19/src/tt.cpp", "static constexpr int ClusterSize = 3;", "Three entries per hash cluster.")
    at("third_party/stockfish19/src/tt.cpp", "for (int i = 0; i < 1000; ++i)", "Each hashfull call visits 1000 clusters, hence 3000 entries.")

    rows = []
    for p in sorted(PROFILE.glob("*-profile.json")):
        pins[str(p.relative_to(ROOT))] = sha(p.read_bytes())
        record = json.loads(p.read_text())
        assert record["exit_code"] == 0 and record["error"] is None
        logs = record["stderr"].splitlines()
        costs = [json.loads(l.removeprefix("astra-search-cost "))
                 for l in logs if l.startswith("astra-search-cost ")]
        turns = [float(l.removeprefix("astra-turn-wall "))
                 for l in logs if l.startswith("astra-turn-wall ")]
        assert len(costs) == len(turns) == 1
        c = costs[0]
        assert c["async"] == 0
        assert abs(sum(b["wall"] for b in c["buckets"].values()) - c["wall"]) < 1e-6
        assert 0 < c["buckets"]["stockfish"]["cpu"] <= c["buckets"]["stockfish"]["wall"]
        rows.append({"case": p.stem, "async": c["async"], "turn_wall": turns[0],
                     "search_wall": c["wall"], "buckets": c["buckets"]})
    assert len(rows) == 8
    search = sum(r["search_wall"] for r in rows)
    turn = sum(r["turn_wall"] for r in rows)
    sf_wall = sum(r["buckets"]["stockfish"]["wall"] for r in rows)
    sf_cpu = sum(r["buckets"]["stockfish"]["cpu"] for r in rows)
    solver = sum(r["buckets"][k]["wall"] for r in rows for k in ("solver", "strategy"))
    arithmetic_path = PROFILE / "independent-arithmetic.json"
    pins[str(arithmetic_path.relative_to(ROOT))] = sha(arithmetic_path.read_bytes())
    earlier = json.loads(arithmetic_path.read_text())
    assert earlier["passed"]
    assert abs(search - earlier["search_wall"]) < 1e-9
    assert abs(turn - earlier["target_turn_wall"]) < 1e-9
    assert abs(sf_wall / turn - earlier["stockfish_share_target_turn"]) < 1e-12
    assert abs(solver / turn - earlier["cfr_share_target_turn"]) < 1e-12
    return {
        "kind": "source-and-saved-profile-review", "passed": True,
        "archive_sha256": plan["archive_sha256"], "input_sha256": pins,
        "source_members_checked": len(members), "source_locations": locations,
        "default_mode": {"workers": 2, "continuous_async": False,
                         "external_environment_caveat": "The launcher inherits its environment. No claim about an unrecorded arena-side override.",
                         "saved_profiles_async": [r["async"] for r in rows]},
        "saved_costs": {"search_wall": search, "turn_wall": turn,
                        "scorer_wrapper_wall": sf_wall, "scorer_wrapper_caller_cpu": sf_cpu,
                        "solver_plus_strategy_wall": solver,
                        "scorer_wrapper_share_turn": sf_wall / turn,
                        "wrapper_caller_cpu_share_turn": sf_cpu / turn,
                        "serial_fixed_work_illustrations": {
                            "halve_all_scorer_wrapper_wall": turn / (turn - sf_wall / 2),
                            "remove_all_scorer_wrapper_wall": turn / (turn - sf_wall),
                            "remove_all_wrapper_caller_cpu": turn / (turn - sf_cpu)}},
        "illustration_not_native_counts": {
            "M": 35, "all_remaining_actions_once_per_ordinary_pass": sum(range(1, 36)),
            "all_child_root_actions_once": 35,
            "parser_unique_complete_lines_string_comparisons": sum(range(1, 36)),
            "full_root_membership_entry_comparisons": 35 * 35,
            "hashfull_entry_visits_for_35_callbacks": 35 * 1000 * 3,
            "caveat": "No timings. Full sweeps, one complete unique score per action, no bounds/retries, full legal-root coverage. Aspiration, cutoffs, deep work, diagnostics and actual move counts alter work."},
        "decision": "Stop before transport implementation. Worker formatting, metrics, flushes and pipe-only cost are not separately measured. This source review corrects the default-mode documentation and supplies a profiling question, not a new candidate.",
        "scope": "No native/model execution, timing, syscalls, fit, GPU, policy/backend change, match, release or deployment. Serial illustrations are not measured speedups, parallel critical-path bounds, node gains or Elo.",
    }


if __name__ == "__main__":
    result = audit()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("passed", "source_members_checked", "default_mode", "saved_costs", "decision")}, indent=2))
