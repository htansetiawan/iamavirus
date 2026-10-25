#!/usr/bin/env python3
"""Join exact-v35 guard traces back to referee immediate-fatal labels."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from learning import histories, ingest, rules


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw", type=Path, default=Path("data/raw"))
    p.add_argument("--arms", nargs=2, action="append", metavar=("NAME", "TRACE"), required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    outcomes = []
    seen = {}
    for name, trace_path in args.arms:
        report = json.loads(Path(trace_path).read_text())
        rows = []
        for item in report["traces"]:
            game = item["game"]
            replay = json.loads((args.raw / "games" / game / "replay.json").read_text())
            states, problems = ingest.validate_replay(replay)
            if problems:
                raise ValueError(f"{game}: invalid replay {problems[:2]}")
            side = rules.WHITE if replay["white"] == "IAmAVirus" else rules.BLACK
            episode = histories.build_episode(replay, states, side, ingest.RULES_FINGERPRINT)
            ply = item["ply"]
            i = episode.actor.decision_event_indices.index(ply)
            legal = episode.actor.legal_actions[i]
            chosen = item["v35_replayed_choice"]
            if chosen not in legal:
                raise ValueError(f"{game} ply {ply}: replayed choice {chosen} not actor-legal")
            truth = states[ply].board
            fatal = truth.move_loses_king(chosen)
            attackers = []
            if fatal:
                attackers = true_attackers_after(truth, chosen, side)
            last_move = replay["frames"][ply].get("move") if ply > 0 else None
            view_key = "white" if side == rules.WHITE else "black"
            before_view = replay["frames"][ply - 1][view_key] if ply > 0 else None
            after_view = replay["frames"][ply][view_key]
            visibility = []
            for attacker in attackers:
                src = (int(attacker["from"][1]) - 1) * 8 + ord(attacker["from"][0]) - 97
                dst = (int(last_move[3]) - 1) * 8 + ord(last_move[2]) - 97 if last_move else None
                last_from = (int(last_move[1]) - 1) * 8 + ord(last_move[0]) - 97 if last_move else None
                visibility.append({
                    "last_opponent_move": last_move,
                    "last_move_destination_is_attacker_square": dst == src if dst is not None else False,
                    "attacker_square_seen_before_last_move": before_view[src] != "?" if before_view else None,
                    "attacker_square_seen_after_last_move": after_view[src] != "?",
                    "last_move_origin_seen_before": before_view[last_from] != "?" if before_view and last_from is not None else None,
                    "last_move_destination_seen_after": after_view[dst] != "?" if dst is not None else None,
                })
            key = (game, ply)
            seen.setdefault(key, {})[name] = {"move": chosen, "immediate_fatal": fatal,
                                              "attackers": attackers,
                                              "attacker_visibility_context": visibility,
                                              "matches_recorded_fatal_move": chosen == item["actual_fatal_move"],
                                              "logged_risk": item["actual_move_risk"] if chosen == item["actual_fatal_move"] else item["safe_alternative_risks"].get(chosen),
                                              "truth_rank": item["v35_truth_rank_at_target"]}
            rows.append(seen[key][name])
        outcomes.append({"arm": name, "trace": str(Path(trace_path)),
                         "games": len(rows), "chosen_fatal": sum(x["immediate_fatal"] for x in rows),
                         "same_recorded_fatal": sum(x["matches_recorded_fatal_move"] for x in rows),
                         "choices": rows})
    result = {
        "classification": "four-case search/risk guard screen; not policy strength or Elo",
        "scope": "Same four v35 losses, same archive, inputs, seed, clock and exact belief prefixes; only MIST_KING_GUARD differs.",
        "arms": outcomes,
        "paired": [{"game": game, "ply": ply, "arms": arms}
                   for (game, ply), arms in sorted(seen.items())],
        "limits": ["Four selected fatal decisions only; all were chosen for diagnostic development.",
                   "Different candidate move is checked for immediate truth-board fatality only.",
                   "No changed action was branched through an opponent response; no strength claim."],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"arms": [{k: v for k, v in row.items() if k != "choices"} for row in outcomes],
                      "paired": result["paired"], "output": str(args.output)}, indent=2))


def true_attackers_after(board, move: str, us: int):
    post = board.copy()
    post.push(move)
    king_sq = post.king_square(us)
    symbols = "PNBRQK"
    attackers = []
    for uci in post.legal_moves():
        dst = (ord(uci[2]) - 97) + 8 * (int(uci[3]) - 1)
        if dst != king_sq:
            continue
        src = (ord(uci[0]) - 97) + 8 * (int(uci[1]) - 1)
        piece = post.piece_at(src)
        symbol = symbols[piece % 6]
        if piece // 6 == rules.BLACK:
            symbol = symbol.lower()
        attackers.append({"move": uci, "from": uci[:2], "piece": symbol})
    return attackers


if __name__ == "__main__":
    main()
