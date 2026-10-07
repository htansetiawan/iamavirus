"""A cheap, learned prior over the opponent's moves for the particle filter.

    python -m learning.opponent_model --raw data/raw --output releases/opponent-v1 \
        --players "Knight Vision" "Greek Gift" "Strongly Invisible" "Decent Chess Bot"

The particle filter weights each hypothesis' successors by how plausible the
opponent's move is. v5 hand-set that prior with three constants (capture x2.5,
giveaway x0.06, attacks-our-king x3). This module fits a conditional-logit
model P(move | board) = softmax(w . f(board, move)) over the legal moves, on
the recorded decisions of strong arena players, using the true board (the
hypothesis stands in for it at play time). The features are deliberately
cheap -- a handful of attack tests per move -- because the prior is evaluated
for every successor of every particle, i.e. tens of thousands of times per
ply. `opponent_model.cc` computes the same features; the parity test drives
both over the same positions.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

import numpy as np

from . import ingest, rules

FEATURE_NAMES = [
    "capture", "captured_value", "mover_pawn", "mover_knight", "mover_bishop", "mover_rook",
    "mover_queen", "mover_king", "promotion", "castle", "dest_attacked", "dest_defended",
    "hanging_value", "exchange", "attacks_king", "escapes_attack", "king_escape",
    "pawn_advance", "centrality", "dest_visible_to_opponent", "from_visible_to_opponent",
    "invisible_king_attack", "mover_value", "king_distance",
    # Persistence: does this move pick up the piece the player moved last ply,
    # and was that last move a capture? (The gold data says the pieces that
    # punish us are ones we saw capture a few plies earlier; the filter needs
    # to know whether such a piece tends to stay or to move on.)
    "moves_last_mover", "moves_last_capturer",
]
NUM_FEATURES = len(FEATURE_NAMES)
VALUE = [1.0, 3.0, 3.0, 5.0, 9.0, 0.0]
MODEL_VERSION = "opponent-logit-v2"


def move_features(board: rules.Board, uci: str, last_to: int = -1, last_was_capture: bool = False) -> np.ndarray:
    """Features of `uci` for the side to move on `board` (the full board).
    `last_to` is the destination square of this player's previous move (-1 if none)."""
    side = board.side
    other = side ^ 1
    f = np.zeros(NUM_FEATURES, dtype=np.float32)
    fr, to = rules.square_index(uci[:2]), rules.square_index(uci[2:4])
    mover = board.piece_at(fr) % 6
    target = board.piece_at(to)
    ep = board.en_passant == to and mover == 0
    captured = VALUE[target % 6] if target >= 0 else (1.0 if ep else 0.0)
    f[0] = 1.0 if (target >= 0 or ep) else 0.0
    f[1] = captured / 9.0
    f[2 + mover] = 1.0
    f[8] = 1.0 if len(uci) == 5 else 0.0
    f[9] = 1.0 if (mover == 5 and abs(to - fr) == 2) else 0.0
    from_attacked = board.is_attacked(fr, other)
    opp_sees_before = (board.visible(other) >> fr) & 1
    king_before = board.king_square(side)
    king_attacked_before = king_before >= 0 and board.is_attacked(king_before, other)
    after = board.copy()
    after.push(uci)
    moved_value = VALUE[after.piece_at(to) % 6]
    attacked = after.is_attacked(to, other)
    defended = after.is_attacked(to, side)
    f[10] = 1.0 if attacked else 0.0
    f[11] = 1.0 if defended else 0.0
    hanging = attacked and not defended
    f[12] = moved_value / 9.0 if hanging else 0.0
    f[13] = (captured - (moved_value if hanging else 0.0)) / 9.0
    enemy_king = after.king_square(other)
    attacks_king = False
    if enemy_king >= 0:
        # Does the moved piece itself attack the king? Other own pieces must
        # still block rays, so they are recoloured as the opponent's pawns:
        # they keep blocking and can never count as attackers of their own king.
        bs = list(after.board_string())
        blocker = "p" if side == 0 else "P"
        for sq in range(64):
            p = after.piece_at(sq)
            if p >= 0 and p // 6 == side and sq != to:
                bs[sq] = blocker
        solo = rules.Board.from_board_string("".join(bs), side)
        attacks_king = solo.is_attacked(enemy_king, side)
    f[14] = 1.0 if attacks_king else 0.0
    f[15] = 1.0 if (from_attacked and not attacked) else 0.0
    f[16] = 1.0 if (mover == 5 and king_attacked_before) else 0.0
    if mover == 0:
        rank = to >> 3
        f[17] = (rank if side == 0 else 7 - rank) / 7.0
    fx, fy = to & 7, to >> 3
    f[18] = 1.0 - (abs(fx - 3.5) + abs(fy - 3.5)) / 7.0
    opp_sees_after = (after.visible(other) >> to) & 1
    f[19] = float(opp_sees_after)
    f[20] = float(opp_sees_before)
    f[21] = 1.0 if (attacks_king and not opp_sees_after) else 0.0
    f[22] = moved_value / 9.0
    if enemy_king >= 0:
        f[23] = max(abs((to & 7) - (enemy_king & 7)), abs((to >> 3) - (enemy_king >> 3))) / 7.0
    f[24] = 1.0 if fr == last_to else 0.0
    f[25] = 1.0 if (fr == last_to and last_was_capture) else 0.0
    return f


def hand_prior_logit(f: np.ndarray) -> float:
    """The v5 hand-set prior expressed as a logit, for a like-for-like comparison."""
    logit = 0.0
    if f[0] > 0:
        logit += math.log(2.5)
    if f[12] > 0 and f[13] < 0:
        logit += math.log(0.06)
    if f[14] > 0:
        logit += math.log(3.0)
    return logit


def build_examples(raw: Path, players: list[str], limit: int | None, seed: int = 0):
    """(features [M,K], chosen index) per decision made by one of `players`."""
    store = ingest.RawStore(raw)
    rows = [json.loads(line) for line in store.accepted.read_text().splitlines()]
    examples = []
    counts = {}
    for row in rows:
        sides = []
        if row.get("white") in players:
            sides.append(0)
        if row.get("black") in players:
            sides.append(1)
        if not sides:
            continue
        replay = json.loads((store.games / row["id"] / "replay.json").read_text())
        frames = replay["frames"]
        state = rules.GameState()
        last_to = {0: -1, 1: -1}
        last_capture = {0: False, 1: False}
        for t in range(len(frames) - 1):
            move = frames[t + 1]["move"]
            side = state.board.side
            if side in sides:
                legal = state.board.legal_moves()
                if move in legal and len(legal) > 1:
                    feats = np.stack([move_features(state.board, m, last_to[side], last_capture[side]) for m in legal])
                    examples.append((feats, legal.index(move), row["id"]))
                    name = row["white"] if side == 0 else row["black"]
                    counts[name] = counts.get(name, 0) + 1
            to = rules.square_index(move[2:4])
            captured = state.board.piece_at(to) >= 0 or (state.board.en_passant == to and state.board.piece_at(rules.square_index(move[:2])) % 6 == 0)
            state.push(move)
            last_to[side] = to
            last_capture[side] = captured
        if limit and len(examples) >= limit:
            break
    random.Random(seed).shuffle(examples)
    return examples, counts


def evaluate(weights: np.ndarray, examples) -> dict:
    nll = uni = hand = 0.0
    top1 = top1_hand = 0
    for feats, chosen, _ in examples:
        logits = feats @ weights
        logits -= logits.max()
        p = np.exp(logits)
        p /= p.sum()
        nll -= math.log(max(p[chosen], 1e-12))
        uni -= math.log(1.0 / len(feats))
        h = np.array([hand_prior_logit(f) for f in feats])
        h -= h.max()
        q = np.exp(h)
        q /= q.sum()
        hand -= math.log(max(q[chosen], 1e-12))
        top1 += int(np.argmax(p) == chosen)
        top1_hand += int(np.argmax(q) == chosen)
    n = max(len(examples), 1)
    return {"decisions": len(examples), "nll_model": nll / n, "nll_uniform": uni / n,
            "nll_hand_prior": hand / n, "top1_model": top1 / n, "top1_hand_prior": top1_hand / n}


def train(examples, epochs: int = 8, lr: float = 0.05, l2: float = 1e-4, seed: int = 0) -> np.ndarray:
    import torch

    torch.manual_seed(seed)
    w = torch.zeros(NUM_FEATURES, requires_grad=True)
    optimizer = torch.optim.Adam([w], lr=lr)
    # Pad to a ragged batch once.
    M = max(f.shape[0] for f, _, _ in examples)
    feats = np.zeros((len(examples), M, NUM_FEATURES), dtype=np.float32)
    mask = np.zeros((len(examples), M), dtype=bool)
    chosen = np.zeros(len(examples), dtype=np.int64)
    for i, (f, c, _) in enumerate(examples):
        feats[i, :f.shape[0]] = f
        mask[i, :f.shape[0]] = True
        chosen[i] = c
    feats_t, mask_t, chosen_t = torch.from_numpy(feats), torch.from_numpy(mask), torch.from_numpy(chosen)
    batch = 1024
    for epoch in range(epochs):
        order = torch.randperm(len(examples))
        total = 0.0
        for start in range(0, len(examples), batch):
            idx = order[start:start + batch]
            logits = feats_t[idx] @ w
            logits = logits.masked_fill(~mask_t[idx], float("-inf"))
            loss = torch.nn.functional.cross_entropy(logits, chosen_t[idx]) + l2 * (w * w).sum()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total += loss.item() * len(idx)
        print(f"epoch {epoch + 1}: train nll {total / len(examples):.4f}", file=sys.stderr)
    return w.detach().numpy()


def export(weights: np.ndarray, report: dict, output: Path, players: list[str]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "opponent_model.json").write_text(json.dumps({
        "version": MODEL_VERSION, "features": FEATURE_NAMES, "weights": [float(x) for x in weights],
        "players": players, "evaluation": report}, indent=1))
    lines = ["// Generated by learning/opponent_model.py; do not edit by hand.",
             "// Conditional-logit weights over OpponentMoveFeatures(), fitted on the",
             "// recorded moves of: " + ", ".join(players) + ".",
             "#ifndef FOW_OPPONENT_WEIGHTS_H_", "#define FOW_OPPONENT_WEIGHTS_H_", "",
             "namespace fow {", "", f"inline constexpr int kOpponentFeatures = {NUM_FEATURES};",
             "inline constexpr double kOpponentWeights[kOpponentFeatures] = {"]
    for name, w in zip(FEATURE_NAMES, weights):
        lines.append(f"    {float(w):+.6f},  // {name}")
    lines += ["};", "", "}  // namespace fow", "", "#endif  // FOW_OPPONENT_WEIGHTS_H_", ""]
    (output / "opponent_weights.h").write_text("\n".join(lines))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--players", nargs="+", default=["Knight Vision", "Greek Gift", "Strongly Invisible", "Decent Chess Bot"])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--output", type=Path, default=Path("releases/opponent-v1"))
    parser.add_argument("--epochs", type=int, default=8)
    args = parser.parse_args(argv)
    examples, counts = build_examples(args.raw, args.players, args.limit)
    print(f"{len(examples)} decisions by {counts}", file=sys.stderr)
    split = int(len(examples) * 0.9)
    train_set, held = examples[:split], examples[split:]
    weights = train(train_set, args.epochs)
    report = {"train": evaluate(weights, train_set), "heldout": evaluate(weights, held), "counts": counts}
    print(json.dumps(report, indent=1))
    for name, w in zip(FEATURE_NAMES, weights):
        print(f"  {name:26s} {w:+.3f}")
    export(weights, report, args.output, args.players)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
