"""Independent course-rule and arithmetic review of the preserved two calls."""
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "astra-submissions/analysis/safe-recapture-20261111"
PRIVATE = ROOT / "data/astra-spool/safe-recapture-20261111"


def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def main():
    previous = load(ROOT / "astra-submissions/experiments/farsight-root-20261110/audit.py", "existing_observer_review")
    oracle = load(ROOT / "astra-submissions/experiments/promotion-ledger-20261110/check.py", "existing_exchange_oracle")
    ref = oracle.ref
    plan = read(OUT / "plan.json")
    for path, expected in plan["source_pins"].items(): assert sha(path) == expected, path
    for path, expected in read(OUT / "replay-preflight.json")["source_pins"].items(): assert sha(path) == expected, path
    results = []
    for role in ("loss", "control"):
        case = plan["selected_pair"][role]
        folder = PRIVATE / role
        receipt = read(OUT / f"{role}-replay.json")
        for path, expected in receipt["files"].items(): assert sha(PRIVATE / path) == expected, path
        assert receipt["terminal"]["exit_code"] == 0 and not receipt["terminal"]["live_owned_members"]
        replay = read(ROOT / f"data/astra-spool/experience-catalogue-20261111/raw/games/{case['game']}/replay.json")
        truth = ref.FowBoard(); feed = ["fow", "w 180 2"]; forced = []; clocks = []
        for ply, frame in enumerate(replay["frames"][:case["root_ply"]+1]):
            if ply:
                move = ref.chess.Move.from_uci(frame["move"]); assert move in ref.fow_moves(truth); truth.push(move)
            assert oracle.board_string(truth) == frame["board"]
            assert ref.observation(truth,True) == frame["white"] and ref.observation(truth,False) == frame["black"]
            feed.append(frame["white"])
            if ply % 2 == 0:
                feed.append(str(frame["clocks"][0]))
                if ply < case["root_ply"]:
                    forced.append(replay["frames"][ply+1]["move"]); clocks.append(replay["frames"][ply+1]["clocks"][0])
        assert (folder / "input.txt").read_text().splitlines() == feed
        settings = read(folder / "settings.json")
        assert settings["MIST_FORCE_MOVES"] == ",".join(forced)
        assert settings["ASTRA_POST_CLOCKS"] == ",".join(map(str,clocks))
        assert settings["FOW_SEED"] == "4171111" and "MIST_TRUTH_SEQ" not in settings
        assert [float(v) for v in re.findall(r"astra-prefix: clock=([\d.]+)",(folder/"stderr.txt").read_text())] == clocks
        pop = read(folder / "population.json"); report = read(OUT / f"{role}-fixed-population.json")
        target = json.loads((folder / "targets.jsonl").read_text())
        assert [(s["index"],s["weight"]) for s in pop["samples"]] == [(s["belief_index"],s["weight"]) for s in target["samples"]]
        assert abs(math.fsum(s["weight"] for s in pop["samples"])-1) < 1e-12
        assert abs(math.fsum(a["probability"] for a in target["actions"])-1) < 1e-12
        assert len(pop["worlds"]) == pop["count"] == target["belief_count"]
        actions = [r["move"] for r in report["rows"]]
        with gzip.open(folder / "strided-flags.jsonl.gz","rt") as f: flags = [json.loads(line) for line in f]
        assert [r["index"] for r in flags] == list(range(0,pop["count"],report["stride"]))
        assert all(len(r["flags"]) == len(actions) and all(0 <= v < 8 for v in r["flags"]) for r in flags)
        weights = [[math.exp(w["logw"]/pop["temperature"]),math.exp(w["logw"])] for w in pop["worlds"]]
        for a,row in enumerate(report["rows"]):
            for bit,key in enumerate(["original_queen","amended_queen","king"]):
                for k in range(2):
                    numerator = math.fsum(weights[r["index"]][k] for r in flags if r["flags"][a] & (1 << bit))
                    denominator = math.fsum(weights[r["index"]][k] for r in flags)
                    assert abs(numerator/denominator-row[key][k]) < 1e-12
        for variant, key in [("original","original_queen"),("amended","amended_queen")]:
            risks = [[row["king"][k]+.9*row[key][k] for row in report["rows"]] for k in range(2)]
            minima = [min(r) for r in risks]
            excluded = {actions[i] for i in range(len(actions)) if any(risks[k][i] > minima[k]+.02 for k in range(2))}
            if len(excluded) == len(actions): excluded = {actions[i] for i in range(len(actions)) if risks[1][i] > minima[1]+.02}
            assert excluded == set(report[f"{variant}_mask"]["excluded"])
        with gzip.open(folder / "recorded-capture-support.json.gz","rt") as f: saved_support = json.load(f)
        capture_support = []; rule_matches = []; reply_count = 0; q = {a["uci"]:0. for a in target["actions"]}
        true_reply = []; recorded_index = actions.index(case["recorded_move"])
        flags_by_index = {r["index"]:r["flags"] for r in flags}
        for i,world in enumerate(pop["worlds"]):
            assert world["index"] == i
            board = previous.world_board(world)
            assert ref.observation(board,True) == replay["frames"][case["root_ply"]]["white"]
            if oracle.board_string(board) == oracle.board_string(truth) and board.turn == truth.turn and board.castling_rights == truth.castling_rights and board.ep_square == truth.ep_square and board.halfmove_clock == truth.halfmove_clock: rule_matches.append(i)
            root = ref.chess.Move.from_uci(case["recorded_move"]); assert root in ref.fow_moves(board)
            expected = oracle.reference(board,root.uci())
            if i in flags_by_index: assert bool(flags_by_index[i][recorded_index] & 2) == bool(expected["risk"])
            child = board.copy(); child.push(root); reply = ref.chess.Move.from_uci(report["recorded_reply"])
            if not oracle.lost(child) and reply in ref.fow_moves(child):
                child.push(reply)
                if not oracle.lost(child): capture_support.append(i)
        assert capture_support == saved_support["indices"]
        for k in range(2):
            mass = math.fsum(weights[i][k] for i in capture_support)/math.fsum(w[k] for w in weights)
            assert abs(mass-report["recorded_capture_mass_fitted_sharp"][k]) < 1e-12
        for sample in pop["samples"]:
            board = previous.world_board(pop["worlds"][sample["index"]])
            assert [a["move"] for a in sample["actions"]] == list(q)
            assert oracle.board_string(board) == next(s["hypothesis_board"] for s in target["samples"] if s["belief_index"] == sample["index"])
            for action in sample["actions"]:
                move = ref.chess.Move.from_uci(action["move"]); assert move in ref.fow_moves(board)
                q[action["move"]] += sample["weight"]*action["value"]
                if action["replies"]:
                    child = board.copy();child.push(move)
                    assert {m.uci() for m in ref.fow_moves(child)} == {r["move"] for r in action["replies"]}
                    assert abs(math.fsum(r["probability"] for r in action["replies"])-1) < 1e-12
                    assert abs(math.fsum(r["probability"]*r["value"] for r in action["replies"])-action["value"]) < 1e-9
                    reply_count += len(action["replies"])
                    if sample["index"] in rule_matches and action["move"] == case["recorded_move"]:
                        true_reply += [dict(index=sample["index"],**r) for r in action["replies"] if r["move"] == report["recorded_reply"]]
        for action in target["actions"]: assert abs(q[action["uci"]]-action["q"]) < 1e-9
        root_value = math.fsum(a["probability"]*q[a["uci"]] for a in target["actions"])
        assert abs(root_value-target["root_value"]) < 1e-9 and abs(root_value-pop["root_value"]) < 1e-9
        assert set(q) == set(actions)-set(report["original_mask"]["excluded"])-set(report["repeat_excluded"])
        assert target["solver_move"] == receipt["chosen"]
        alternatives = [a for a in target["actions"] if a["uci"] != case["recorded_move"] and a["uci"] not in report["amended_mask"]["excluded"]]
        results.append(dict(role=role,course_prefix_frames=case["root_ply"]+1,population_observations_checked=len(pop["worlds"]),
            all_worlds_checked=True,recorded_action_course_reference_checks=len(pop["worlds"]),true_rule_state_indices=rule_matches,
            capture_support_independently_reproduced=True,all_exported_reply_moves_checked=reply_count,root_values_reproduced=True,
            original_and_amended_masks_independently_reproduced=True,true_state_recorded_replies=true_reply,
            root_value=root_value,belief_overflowed=target["belief_overflowed"],
            best_remaining_original_tree_action=max(alternatives,key=lambda a:a["q"]) if alternatives else None))
    result = dict(at=datetime.now(timezone.utc).isoformat(),passed=True,cases=results,auditor_sha256=sha(__file__),
        scope="Same saved actor calls only; no engine invocation, patched policy, timing rerun, fitted model or strength estimate.")
    with (OUT / "pair-review.json").open("x") as f: json.dump(result,f,indent=1,sort_keys=True,allow_nan=False);f.write("\n")
    print(json.dumps(result))


if __name__ == "__main__": main()
