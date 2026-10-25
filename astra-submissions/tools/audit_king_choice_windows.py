#!/usr/bin/env python3
"""Audit v35 king-move choices against exact one-move referee danger labels.

This is an offline descriptive diagnostic. Finding a safe alternative under
true-board immediate-loss labels does not prove it was safe under the actor's
belief or strategically good long-term.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from learning import histories, ingest, rules

TARGETS = {"duck", "Decent Chess Bot", "Strongly Invisible", "Instructors"}


def read_index(path: Path, since: str, targets: set[str], version: int | None):
    rows = []
    digest = hashlib.sha256()
    with path.open() as f:
        for line in f:
            digest.update(line.encode())
            if not line.strip():
                continue
            row = json.loads(line)
            white, black = row.get("white"), row.get("black")
            if "IAmAVirus" not in (white, black):
                continue
            opponent = black if white == "IAmAVirus" else white
            if opponent not in targets or (row.get("createdAt") or "") < since:
                continue
            side = rules.WHITE if white == "IAmAVirus" else rules.BLACK
            own_version = row.get("whiteVersion" if side == rules.WHITE else "blackVersion")
            if version is not None and own_version != version:
                continue
            rows.append((row, side, opponent))
    return rows, digest.hexdigest()


def aggregate(rows: list[dict[str, Any]]):
    st = collections.defaultdict(collections.Counter)
    details = []
    fatal_details = []
    for game in rows:
        group = game["outcome"]
        opp = game["opponent"]
        for decision in game["decisions"]:
            s = st[("all", "all")]
            so = st[("opponent", opp)]
            sg = st[("outcome", group)]
            board = decision["board"]
            side_piece = "K" if decision["side"] == rules.WHITE else "k"
            move = decision["move"]
            is_king = board[(int(move[1]) - 1) * 8 + ord(move[0]) - 97] == side_piece
            danger = decision["danger"]
            legal = decision["legal"]
            actual_i = legal.index(move)
            chosen_fatal = bool(danger[actual_i])
            nonking_safe = [m for m, bad in zip(legal, danger)
                            if not bad and board[(int(m[1]) - 1) * 8 + ord(m[0]) - 97] != side_piece]
            safe_count = sum(not x for x in danger)
            fatal_has_safe_alternative = chosen_fatal and safe_count > 0
            for acc in (s, so, sg):
                acc["decisions"] += 1
                acc["king_moves"] += int(is_king)
                acc["chosen_fatal"] += int(chosen_fatal)
                acc["fatal_with_safe_alternative"] += int(fatal_has_safe_alternative)
                acc["fatal_all"] += int(any(danger))
                acc["safe_nonking_available"] += int(bool(nonking_safe))
                acc["king_move_with_safe_nonking"] += int(is_king and bool(nonking_safe))
                acc["king_move_fatal"] += int(is_king and chosen_fatal)
                acc["king_move_avoidable_by_immediate_label"] += int(is_king and not chosen_fatal and bool(nonking_safe))
                acc["safe_actions"] += safe_count
                acc["candidate_actions"] += len(legal)
            if is_king and nonking_safe:
                details.append({"game": game["id"], "opponent": opp, "outcome": group,
                                "ply": decision["ply"], "move": move, "fatal": chosen_fatal,
                                "safe_nonking_count": len(nonking_safe), "safe_count": safe_count,
                                "legal_count": len(legal), "board": board,
                                "observation": decision["observation"],
                                "example_safe_nonking": nonking_safe[:5]})
            safe_actions = [m for m, bad in zip(legal, danger) if not bad]
            if chosen_fatal and safe_actions:
                fatal_details.append({"game": game["id"], "opponent": opp, "outcome": group,
                                      "ply": decision["ply"], "move": move,
                                      "king_move": is_king, "safe_count": len(safe_actions),
                                      "legal_count": len(legal), "safe_alternatives": safe_actions[:8],
                                      "board": board, "observation": decision["observation"]})
    return st, details, fatal_details


def ratios(counter: collections.Counter):
    d = counter["decisions"]
    k = counter["king_moves"]
    return {
        "decisions": d,
        "king_moves": k,
        "king_moves_per_100_decisions": 100 * k / d if d else None,
        "chosen_immediate_fatal_per_100_decisions": 100 * counter["chosen_fatal"] / d if d else None,
        "king_move_immediate_fatal_rate": counter["king_move_fatal"] / k if k else None,
        "king_moves_with_safe_nonking_alternative": counter["king_move_with_safe_nonking"],
        "avoidable_king_moves_among_king_moves": counter["king_move_avoidable_by_immediate_label"] / k if k else None,
        "positions_with_any_immediate_fatal_action": counter["fatal_all"],
        "fatal_choices_with_safe_alternative": counter["fatal_with_safe_alternative"],
        "safe_alternative_rate_among_fatal_choices": (
            counter["fatal_with_safe_alternative"] / counter["chosen_fatal"]
            if counter["chosen_fatal"] else None
        ),
        "safe_action_fraction": counter["safe_actions"] / counter["candidate_actions"] if counter["candidate_actions"] else None,
    }


def game_counts(game: dict[str, Any]) -> dict[str, int]:
    counts = collections.Counter()
    for decision in game["decisions"]:
        board, move = decision["board"], decision["move"]
        piece = "K" if decision["side"] == rules.WHITE else "k"
        is_king = board[(int(move[1]) - 1) * 8 + ord(move[0]) - 97] == piece
        actual_i = decision["legal"].index(move)
        fatal = bool(decision["danger"][actual_i])
        safe_count = sum(not x for x in decision["danger"])
        nonking_safe = any(
            not bad and board[(int(action[1]) - 1) * 8 + ord(action[0]) - 97] != piece
            for action, bad in zip(decision["legal"], decision["danger"])
        )
        counts["decisions"] += 1
        counts["king_moves"] += int(is_king)
        counts["chosen_fatal"] += int(fatal)
        counts["fatal_with_safe_alternative"] += int(fatal and safe_count > 0)
        counts["fatal_king"] += int(is_king and fatal)
        counts["king_with_safe_nonking"] += int(is_king and nonking_safe)
        counts["avoidable_king"] += int(is_king and not fatal and nonking_safe)
    return dict(counts)


def bootstrap_contrasts(games: list[dict[str, Any]], samples: int = 5000):
    by_outcome = {
        outcome: [game_counts(g) for g in games if g["outcome"] == outcome]
        for outcome in ("loss", "win")
    }
    rng = random.Random(20261024)
    metric_defs = {
        "king_moves_per_100_decisions": ("king_moves", "decisions", 100.0),
        "chosen_immediate_fatal_per_100_decisions": ("chosen_fatal", "decisions", 100.0),
        "fatal_with_safe_alternative_per_100_decisions": (
            "fatal_with_safe_alternative", "decisions", 100.0
        ),
        "fatal_rate_among_king_moves": ("fatal_king", "king_moves", 1.0),
        "king_moves_with_safe_nonking_rate": ("king_with_safe_nonking", "king_moves", 1.0),
    }
    result = {"resampling_unit": "whole game, stratified by outcome", "seed": 20261024,
              "bootstrap_samples": samples, "outcomes": {}, "loss_minus_win": {}}
    distributions = {outcome: {name: [] for name in metric_defs} for outcome in by_outcome}
    for outcome, rows in by_outcome.items():
        for _ in range(samples):
            picked = [rows[rng.randrange(len(rows))] for _ in rows]
            totals = collections.Counter()
            for row in picked:
                totals.update(row)
            for name, (numerator, denominator, scale) in metric_defs.items():
                distributions[outcome][name].append(
                    scale * totals[numerator] / totals[denominator] if totals[denominator] else 0.0
                )
    for outcome, rows in by_outcome.items():
        result["outcomes"][outcome] = {"games": len(rows)}
    for name in metric_defs:
        diff = sorted(a - b for a, b in zip(distributions["loss"][name], distributions["win"][name]))
        result["loss_minus_win"][name] = {
            "estimate": round(sum(distributions["loss"][name]) / samples -
                               sum(distributions["win"][name]) / samples, 5),
            "game_bootstrap_95pct": [round(diff[int(0.025 * samples)], 5),
                                     round(diff[min(samples - 1, int(0.975 * samples))], 5)],
        }
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw", type=Path, default=Path("data/raw"))
    p.add_argument("--accepted", type=Path)
    p.add_argument("--since", default="2026-10-17")
    p.add_argument("--version", type=int, default=35)
    p.add_argument("--targets", nargs="*", default=sorted(TARGETS))
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--limit-games", type=int, default=0)
    args = p.parse_args()
    accepted = args.accepted or args.raw / "accepted.jsonl"
    selected, index_hash = read_index(accepted, args.since, set(args.targets), args.version)
    selected.sort(key=lambda x: ((x[0].get("createdAt") or ""), x[0]["id"]))
    if args.limit_games:
        selected = selected[:args.limit_games]
    games, problems, skipped = [], [], 0
    for row, side, opponent in selected:
        path = args.raw / "games" / row["id"] / "replay.json"
        try:
            replay = json.loads(path.read_text())
            states, validation = ingest.validate_replay(replay)
            if validation:
                problems.append({"game": row["id"], "problems": validation[:2]})
                continue
            episode = histories.build_episode(replay, states, side, ingest.RULES_FINGERPRINT)
            if episode.metadata.candidate_mismatches:
                problems.append({"game": row["id"], "candidate_mismatches": len(episode.metadata.candidate_mismatches)})
            if replay["result"] == "1/2-1/2":
                outcome = "draw"
            else:
                won = ((replay["result"] == "1-0") and side == rules.WHITE) or (
                    (replay["result"] == "0-1") and side == rules.BLACK)
                outcome = "win" if won else "loss"
            decisions = []
            for i, move in enumerate(episode.actor.own_actions):
                event = episode.actor.decision_event_indices[i]
                board = episode.targets.boards[i]
                decisions.append({"ply": event, "side": side, "move": move,
                                  "board": board,
                                  "observation": episode.actor.observations[event],
                                  "legal": episode.actor.legal_actions[i],
                                  "danger": episode.targets.king_loss_by_action[i]})
            games.append({"id": row["id"], "opponent": opponent, "outcome": outcome,
                          "decisions": decisions})
        except (OSError, KeyError, ValueError, IndexError) as exc:
            skipped += 1
            problems.append({"game": row["id"], "error": str(exc)[:160]})
    stats, examples, fatal_examples = aggregate(games)
    output = {
        "classification": "exact-referee immediate-danger audit; not a strength estimate",
        "scope": {"since": args.since, "own_version": args.version, "opponents": args.targets,
                  "selected_games": len(selected), "valid_games": len(games), "skipped_games": skipped,
                  "validation_or_candidate_problems": problems,
                  "accepted_index_sha256": index_hash,
                  "games": [{"id": g["id"], "opponent": g["opponent"], "outcome": g["outcome"],
                             "decisions": len(g["decisions"])} for g in games]},
        "aggregate": {"all": ratios(stats[("all", "all")]),
                      "outcomes": {k: ratios(v) for (kind, k), v in stats.items() if kind == "outcome"},
                      "opponents": {k: ratios(v) for (kind, k), v in stats.items() if kind == "opponent"}},
        "loss_win_game_bootstrap": bootstrap_contrasts(games),
        "king_moves_with_safe_nonking_examples": examples[:100],
        "fatal_choices_with_safe_alternatives_examples": fatal_examples,
        "limits": [
            "The actor-legal set is exact for the saved observation/history, but immediate danger labels use the true board.",
            "A safe non-king move under the actual board may still be risky in the actor's belief and may be strategically inferior.",
            "Labels cover one own move only; they do not score opponent replies, long-term attack value, or game strength.",
            "Only selected v35 games against four high-drain opponents since the supplied date are included.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"selected": len(selected), "valid": len(games), "skipped": skipped,
                      "outcomes": output["aggregate"]["outcomes"],
                      "overall": output["aggregate"]["all"],
                      "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
