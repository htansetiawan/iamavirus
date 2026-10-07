"""Evaluation: tactical regressions, model metrics, matches, and runtime.

    python -m learning.evaluate --candidate <checkpoint> --suite tactical --raw data/raw
    python -m learning.evaluate --candidate <checkpoint> --suite model --manifest data/manifests/v1.json
    python -m learning.evaluate --candidate <checkpoint> --suite match --opponents capture-greedy cpp:20000 --pairs 20
    python -m learning.evaluate --candidate <release-dir> --baseline-mode cpp --suite arena --pairs 20

`match` runs colour-swapped seed pairs in the simulator (a pair is the
resampling unit) and reports a paired-bootstrap 95% interval on the score.
`arena` drives the real C++ bot through the course referee in two modes
(candidate release vs cpp baseline) under real 180+2 clocks.
`tactical` validates danger labels and history reconstruction on the six
regression games and reports the policy probability of each recorded losing
move; it demands no certainty threshold from a single hidden-state realisation.
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

from . import dataset as ds
from . import env, histories, ingest, labels, rollouts, rules
from .model import masked_log_softmax
from .pretrain import evaluate as model_metrics, load_config, load_model

REGRESSION_GAMES = {
    "cxgvxx6h": "before 7.Kxf2: hidden queen b6 protects f2 along b6-c5-d4-e3-f2",
    "rz89dmpy": "before 47...c5: hidden queen a8 attacks king a6; Kb5 is the only immediate survivor",
    "92of99z7": "hidden knight takes Qd5; later rook a5 threatens king a7",
    "ky4pm8o2": "hidden knight attacks Qd6; disappearance of own rook constrains capturer on g8",
    "gxmut7rr": "hidden protection of f7; final bishop e4 diagonal to h1",
    "zviidq21": "hidden recapture of Qa5; final queen b3 diagonal to g8",
}
TEAM_IDS = {"IAmAVirus", "a2c35173659545c99752376a70418438"}


# ---------------------------------------------------------------------------
# Tactical regression corpus
# ---------------------------------------------------------------------------

@torch.no_grad()
def policy_over_history(model, episode: histories.PlayerEpisode, device):
    """Policy probabilities and danger estimates at every decision of a history."""
    planes, scalars, decisions = ds.episode_tensors(episode)
    hidden = model.initial_hidden(1, device)
    by_event = {d["event"]: d for d in decisions}
    out = []
    for event in range(planes.shape[0]):
        hidden, spatial, _, value = model.observe(torch.from_numpy(planes[event:event + 1]).to(device),
                                                  torch.from_numpy(scalars[event:event + 1]).to(device), hidden)
        if event in by_event and by_event[event]["count"] > 0:
            d = by_event[event]
            logits, danger = model.score(hidden, spatial, torch.from_numpy(d["from"][None]).to(device),
                                         torch.from_numpy(d["to"][None]).to(device),
                                         torch.from_numpy(d["promo"][None]).to(device))
            probs = masked_log_softmax(logits, torch.ones_like(logits, dtype=torch.bool)).exp()[0].cpu().numpy()
            out.append({"event": event, "probs": probs, "danger": torch.sigmoid(danger)[0].cpu().numpy(),
                        "value": float(value[0, 0]), "danger_labels": d["danger"]})
    return out


def tactical_suite(model, raw: Path, device) -> dict:
    store = ingest.RawStore(raw)
    report = {}
    for game_id, focus in REGRESSION_GAMES.items():
        path = store.games / game_id / "replay.json"
        if not path.exists():
            report[game_id] = {"status": "missing from raw cache", "focus": focus}
            continue
        replay = json.loads(path.read_text())
        states, problems = ingest.validate_replay(replay)
        if problems:
            report[game_id] = {"status": "invalid", "problems": problems}
            continue
        # Our seat is the losing side in these games.
        result = replay["result"]
        side = rules.BLACK if result == "1-0" else rules.WHITE
        episode = histories.build_episode(replay, states, side, ingest.RULES_FINGERPRINT)
        if episode.num_decisions == 0:
            report[game_id] = {"status": "no decisions", "focus": focus}
            continue
        scored = policy_over_history(model, episode, device)
        last = scored[-1] if scored else None
        k = episode.num_decisions - 1
        legal = episode.actor.legal_actions[k]
        played = episode.actor.own_actions[k]
        idx = legal.index(played)
        lost_now = episode.targets.king_loss_by_action[k][idx] == 1
        survivors = [m for m, d in zip(legal, episode.targets.king_loss_by_action[k]) if d == 0]
        entry = {"status": "ok", "focus": focus, "decisions": episode.num_decisions,
                 "candidate_mismatches": len(episode.metadata.candidate_mismatches),
                 "final_move": played, "final_move_loses_king_on_true_board": lost_now,
                 "true_board_survivors": survivors[:12], "survivor_count": len(survivors)}
        if last is not None and last["event"] == episode.actor.decision_event_indices[k]:
            entry["policy_probability_of_losing_move"] = float(last["probs"][idx])
            entry["danger_estimate_of_losing_move"] = float(last["danger"][idx])
            entry["policy_mass_on_true_survivors"] = float(sum(last["probs"][legal.index(m)] for m in survivors))
            top = int(np.argmax(last["probs"]))
            entry["policy_top_move"] = legal[top]
            entry["policy_top_move_survives"] = episode.targets.king_loss_by_action[k][top] == 0
        report[game_id] = entry
    return report


# ---------------------------------------------------------------------------
# Matches in the simulator
# ---------------------------------------------------------------------------

def paired_bootstrap(pair_scores: list[float], samples: int = 2000, seed: int = 0) -> dict:
    arr = np.array(pair_scores, dtype=np.float64)
    if len(arr) == 0:
        return {"mean": 0.0, "ci95": [0.0, 0.0], "pairs": 0}
    rng = np.random.default_rng(seed)
    means = [arr[rng.integers(0, len(arr), len(arr))].mean() for _ in range(samples)]
    return {"mean": float(arr.mean()), "ci95": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))],
            "pairs": int(len(arr))}


def simulator_matches(model, opponents: list[str], pairs: int, device, seed: int = 0,
                      baseline_model=None, games_in_flight: int = 16) -> dict:
    """Candidate vs each opponent, colour-swapped seed pairs, paired bootstrap.

    When `baseline_model` is given the comparison is candidate-minus-baseline
    against the same opponents and seeds; otherwise the candidate's score
    against each opponent is reported with its own interval around 0.5.
    """
    results = {}
    for opponent in opponents:
        def play(actor, label):
            league = rollouts.League(recent=[], older=[], fixed=[opponent], recent_share=0, older_share=0, fixed_share=1)
            collector = rollouts.Collector(actor, {}, device, league, games_in_flight)
            scores = {}
            next_seed = seed * 100_000
            episodes_done = 0
            # Drive exactly 2 * pairs games: seeds s and s+1 swap colours.
            games = []
            records = []
            rng = random.Random(seed)
            while episodes_done < 2 * pairs:
                while len(games) < games_in_flight and next_seed < seed * 100_000 + 2 * pairs:
                    games.append(collector.new_game(next_seed, rng))
                    next_seed += 1
                if not games:
                    break
                neural = []
                for game in games:
                    if game.need_delivery:
                        game.deliver()
                        neural += [p for p in game.players if p.neural]
                if neural:
                    collector.run_observe(neural)
                to_score = [g.players[g.side_to_move] for g in games if g.players[g.side_to_move].neural]
                choices = collector.run_score(to_score, rng) if to_score else {}
                for game in games:
                    player = game.players[game.side_to_move]
                    uci = choices.get(id(player), (None,))[0] if player.neural else player.decide(game.rng)
                    if uci is None:
                        game.forfeit(game.side_to_move, "No legal moves")
                    else:
                        game.push(uci)
                still = []
                for game in games:
                    if game.done:
                        rec = game.record()
                        records.append(rec)
                        side = 0 if rec.white_kind == "learner" else 1
                        scores[rec.seed] = 0.5 + 0.5 * labels.terminal_return(rec.result, side)
                        episodes_done += 1
                    else:
                        still.append(game)
                games = still
            return scores, records
        cand_scores, cand_records = play(model, "candidate")
        pair_values = []
        base = seed * 100_000
        if baseline_model is not None:
            base_scores, _ = play(baseline_model, "baseline")
            for p in range(pairs):
                a = cand_scores.get(base + 2 * p, 0.5) + cand_scores.get(base + 2 * p + 1, 0.5)
                b = base_scores.get(base + 2 * p, 0.5) + base_scores.get(base + 2 * p + 1, 0.5)
                pair_values.append((a - b) / 2)
        else:
            for p in range(pairs):
                pair_values.append((cand_scores.get(base + 2 * p, 0.5) + cand_scores.get(base + 2 * p + 1, 0.5)) / 2)
        wins = sum(1 for v in cand_scores.values() if v == 1.0)
        draws = sum(1 for v in cand_scores.values() if v == 0.5)
        losses = sum(1 for v in cand_scores.values() if v == 0.0)
        results[opponent] = {"games": len(cand_scores), "wins": wins, "draws": draws, "losses": losses,
                             "score_rate": (wins + 0.5 * draws) / max(len(cand_scores), 1),
                             "paired": paired_bootstrap(pair_values),
                             "comparison": "candidate-minus-baseline" if baseline_model is not None else "candidate score",
                             "mean_plies": float(np.mean([r.plies for r in cand_records])) if cand_records else 0}
    return results


# ---------------------------------------------------------------------------
# Arena-like matches through the referee (real clocks)
# ---------------------------------------------------------------------------

def arena_matches(candidate_dir: Path, mode: str, baseline_mode: str, pairs: int, kit: Path, repo: Path,
                  opponent_cmd: str | None = None, seed: int = 0) -> dict:
    """Candidate (bot in `mode` with the release) vs opponent, and baseline (bot
    in `baseline_mode`) vs the same opponent, colour-swapped seeds, under
    real 180+2 clocks via referee.py. The opponent defaults to the cpp bot
    itself with a different seed (self-play baseline), or `opponent_cmd`."""
    python = kit / ".venv" / "bin" / "python"
    referee = kit / "referee.py"
    run = repo / "run.sh"
    results = {"candidate": [], "baseline": [], "pairs": pairs, "mode": mode, "baseline_mode": baseline_mode}
    out_dir = repo / "data" / "arena"
    out_dir.mkdir(parents=True, exist_ok=True)

    def one(label, bot_mode, colour, s):
        # referee.py splits the command with shlex and executes it without a
        # shell, so environment variables go through `env`.
        bot = f"env FOW_MODE={bot_mode} FOW_MODEL_DIR={candidate_dir} FOW_SEED={s} {run}"
        opp = opponent_cmd or f"env FOW_MODE=cpp FOW_SEED={s + 977} {run}"
        white, black = (bot, opp) if colour == 0 else (opp, bot)
        out = out_dir / f"{label}-{bot_mode}-{colour}-{s}.json"
        started = time.time()
        subprocess.run([str(python), str(referee), "--trusted-local", "--white", white, "--black", black,
                        "--white-name", "white", "--black-name", "black", "--base-time", "180",
                        "--increment", "2", "--max-plies", "1000", "--output", str(out)],
                       check=True, capture_output=True, text=True)
        replay = json.loads(out.read_text())
        score = 0.5 + 0.5 * labels.terminal_return(replay["result"], colour)
        return {"seed": s, "colour": colour, "result": replay["result"], "reason": replay["reason"],
                "plies": len(replay["frames"]) - 1, "score": score, "seconds": time.time() - started}

    pair_values = []
    for p in range(pairs):
        s = seed * 1000 + p
        cand = [one("candidate", mode, 0, s), one("candidate", mode, 1, s)]
        base = [one("baseline", baseline_mode, 0, s), one("baseline", baseline_mode, 1, s)]
        results["candidate"] += cand
        results["baseline"] += base
        pair_values.append((cand[0]["score"] + cand[1]["score"] - base[0]["score"] - base[1]["score"]) / 2)
        print(f"  pair {p}: candidate {[c['result'] for c in cand]} baseline {[b['result'] for b in base]}", file=sys.stderr)
    results["paired"] = paired_bootstrap(pair_values)
    results["candidate_score_rate"] = float(np.mean([c["score"] for c in results["candidate"]]))
    results["baseline_score_rate"] = float(np.mean([c["score"] for c in results["baseline"]]))
    return results


def runtime_suite(candidate_dir: Path, repo: Path, kit: Path, seed: int = 0) -> dict:
    """Init time, per-decision inference latency and peak memory for the bot in
    neural mode, measured through one real referee game against the baseline."""
    python = kit / ".venv" / "bin" / "python"
    out = repo / "data" / "arena" / f"runtime-{seed}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    bot = f"env FOW_MODE=neural FOW_MODEL_DIR={candidate_dir} FOW_SEED={seed} /usr/bin/time -v {repo / 'run.sh'}"
    subprocess.run([str(python), str(kit / "referee.py"), "--trusted-local", "--white", bot,
                    "--black", f"{python} -u {kit / 'baseline.py'} --seed 1", "--base-time", "180",
                    "--increment", "2", "--max-plies", "1000", "--output", str(out)], check=True,
                   capture_output=True, text=True)
    replay = json.loads(out.read_text())
    diag = replay.get("privateDiagnostics", {}).get("white", "")
    infer = []
    load = None
    peak_kb = None
    for line in diag.splitlines():
        if line.startswith("model loaded in"):
            load = float(line.split()[3].rstrip("s"))
        if " infer=" in line:
            infer.append(float(line.split(" infer=")[1].split()[0]))
        if "Maximum resident set size" in line:
            peak_kb = int(line.split(":")[1])
    if peak_kb is None:
        # The referee ends the bot before `time` can report, so peak memory is
        # measured on a scripted turn instead: initialise, one view, one clock.
        script = "fow\nw 180 2\n" + rules.START_BOARD.replace("p", "?").replace("r", "?").replace(
            "n", "?").replace("b", "?").replace("q", "?").replace("k", "?") + "\n180\n"
        probe = subprocess.run(["/usr/bin/time", "-v", str(repo / "bot")], input=script, capture_output=True,
                               text=True, env={**dict(__import__("os").environ), "FOW_MODE": "hybrid",
                                               "FOW_MODEL_DIR": str(candidate_dir), "FOW_SEED": str(seed)})
        for line in probe.stderr.splitlines():
            if "Maximum resident set size" in line:
                peak_kb = int(line.split(":")[1])
    return {"result": replay["result"], "plies": len(replay["frames"]) - 1, "model_load_seconds": load,
            "inference_p50": float(np.percentile(infer, 50)) if infer else None,
            "inference_p99": float(np.percentile(infer, 99)) if infer else None,
            "peak_rss_mib": peak_kb / 1024 if peak_kb else None, "decisions": len(infer)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--candidate", type=Path, required=True, help="checkpoint (.pt) or release directory")
    parser.add_argument("--suite", choices=["tactical", "model", "match", "arena", "runtime"], required=True)
    parser.add_argument("--baseline", type=Path, default=None, help="baseline checkpoint for match comparison")
    parser.add_argument("--baseline-mode", default="cpp")
    parser.add_argument("--mode", default="hybrid", help="bot mode for the arena suite")
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=Path("learning/configs/replay_ppo.yaml"))
    parser.add_argument("--opponents", nargs="*", default=["capture-greedy", "uniform-random"])
    parser.add_argument("--pairs", type=int, default=10)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--kit", type=Path, default=Path.home() / "git" / "fow-starter")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    repo = Path(__file__).resolve().parents[1]
    report: dict = {"suite": args.suite, "candidate": str(args.candidate), "seed": args.seed}
    if args.suite in ("tactical", "model", "match"):
        model, payload = load_model(args.candidate, device)
        model.eval()
        report["checkpoint_step"] = payload.get("step")
    if args.suite == "tactical":
        report["games"] = tactical_suite(model, args.raw, device)
    elif args.suite == "model":
        manifest = json.loads(args.manifest.read_text())
        cfg = load_config(args.config)["pretrain"]
        for split in ("validation", "test"):
            episodes = ds.load_episodes(Path(manifest["shards"][split]))
            report[split] = model_metrics(model, episodes, cfg, device, random.Random(0))
    elif args.suite == "match":
        baseline = load_model(args.baseline, device)[0].eval() if args.baseline else None
        report["matches"] = simulator_matches(model, args.opponents, args.pairs, device, args.seed, baseline)
    elif args.suite == "arena":
        report["arena"] = arena_matches(args.candidate, args.mode, args.baseline_mode, args.pairs, args.kit, repo, seed=args.seed)
    elif args.suite == "runtime":
        report["runtime"] = runtime_suite(args.candidate, repo, args.kit, args.seed)
    text = json.dumps(report, indent=1, default=float)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
        print(f"wrote {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
