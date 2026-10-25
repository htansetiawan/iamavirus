#!/usr/bin/env python3
"""Compare archived and patched view move sets against true replay positions."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ARCHIVE = ROOT / "fable-submissions/iamavirus-v35-mist-c-v14.zip"
EVENTS = HERE / "top-opponent-ep-action-coverage.jsonl"
PIECES = {"P": (0, 0), "N": (0, 1), "B": (0, 2), "R": (0, 3), "Q": (0, 4), "K": (0, 5),
          "p": (1, 0), "n": (1, 1), "b": (1, 2), "r": (1, 3), "q": (1, 4), "k": (1, 5)}
START_CASTLE = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)


def square(text: str) -> int:
    return (ord(text[1]) - 49) * 8 + ord(text[0]) - 97


def state_metadata(frames: list[dict], ply: int) -> tuple[int, int]:
    rights = START_CASTLE
    ep = -1
    for i in range(1, ply + 1):
        move = frames[i].get("move")
        if not move or len(move) < 4:
            continue
        before = frames[i - 1]["board"]
        src, dst = square(move[:2]), square(move[2:4])
        piece, captured = before[src], before[dst]
        if piece == "K": rights &= ~((1 << 0) | (1 << 7))
        if piece == "k": rights &= ~((1 << 56) | (1 << 63))
        if src in (0, 7, 56, 63): rights &= ~(1 << src)
        if captured in "Rr" and dst in (0, 7, 56, 63): rights &= ~(1 << dst)
        if piece in "Pp" and abs(dst - src) == 16:
            ep = (src + dst) // 2
        else:
            ep = -1
    return rights, ep


def compile_probe(source_dir: Path, out: Path) -> None:
    subprocess.run(["cc", "-O2", "-std=c11", "-D_POSIX_C_SOURCE=199309L", "-pthread",
                    "-I", str(source_dir), str(HERE / "audit_replay_move_sets.c"),
                    str(source_dir / "src/board.c"), str(source_dir / "src/belief.c"),
                    str(source_dir / "src/movemodel.c"), str(source_dir / "src/eval.c"),
                    "-lm", "-o", str(out)], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, default=ARCHIVE)
    ap.add_argument("--events", type=Path, default=EVENTS)
    ap.add_argument("--games", type=int, default=0, help="limit unique replay IDs; 0 means all")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    event_rows = [json.loads(x) for x in args.events.read_text().splitlines() if x]
    game_ids = sorted({row["game"] for row in event_rows})
    if args.games:
        game_ids = game_ids[:args.games]
    inputs: list[str] = []
    labels: list[tuple[str, int, int]] = []
    skipped = 0
    for game_id in game_ids:
        path = ROOT / "data/raw/games" / game_id / "replay.json"
        try:
            replay = json.loads(path.read_text())
            frames = replay["frames"]
            for ply, frame in enumerate(frames):
                board = frame["board"]
                view = frame["white"] if ply % 2 == 0 else frame["black"]
                if len(board) != 64 or len(view) != 64 or any(c not in "PNBRQKpnbrqk-" for c in board):
                    continue
                castle, ep = state_metadata(frames, ply)
                side = "w" if ply % 2 == 0 else "b"
                inputs.append(f"{side} {castle:x} {ep} {board} {view}\n")
                labels.append((game_id, ply, ep))
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            skipped += 1
    text = "".join(inputs)
    with tempfile.TemporaryDirectory(prefix="astra-ep-replay-moves-") as td:
        work = Path(td)
        base = work / "v35"
        base.mkdir()
        with zipfile.ZipFile(args.archive) as zf:
            for name in zf.namelist():
                if name.startswith("src/"):
                    zf.extract(name, base)
        patched = work / "patched"
        shutil.copytree(base, patched)
        patch_root = work / "patch-root"
        (patch_root / "src").mkdir(parents=True)
        (patch_root / "src/belief.c").write_bytes((base / "src/belief.c").read_bytes())
        subprocess.run(["patch", "-p1", "-i", str(HERE / "belief-ep-observation.patch")],
                       cwd=patch_root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (patched / "src/belief.c").write_bytes((patch_root / "src/belief.c").read_bytes())
        outputs = []
        for name, source in (("baseline", base), ("patched", patched)):
            binary = work / f"{name}-probe"
            compile_probe(source, binary)
            proc = subprocess.run([str(binary)], input=text, text=True, capture_output=True, check=True)
            lines = proc.stdout.splitlines()
            if len(lines) != len(labels):
                raise RuntimeError(f"{name}: got {len(lines)} rows, expected {len(labels)}")
            outputs.append(lines)
    result_rows = []
    aggregate = {name: {"false_candidates": 0, "false_ep_candidates": 0, "false_other_candidates": 0,
                        "missed_true_moves": 0, "missed_ep_moves": 0, "missed_other_moves": 0,
                        "positions_with_false": 0, "positions_with_missed": 0, "ep_positions": 0}
                 for name in ("baseline", "patched")}
    examples = {name: [] for name in aggregate}
    for idx, label in enumerate(labels):
        row: dict = {"game": label[0], "ply": label[1], "ep_target": label[2]}
        for name, lines in zip(("baseline", "patched"), outputs):
            parts = lines[idx].split("\t")
            count, false_count, missed_count, false_ep, false_other, missed_ep, missed_other = map(int, parts[:7])
            false_moves, missed_moves = parts[7], parts[8]
            stats = aggregate[name]
            stats["false_candidates"] += false_count
            stats["false_ep_candidates"] += false_ep
            stats["false_other_candidates"] += false_other
            stats["missed_true_moves"] += missed_count
            stats["missed_ep_moves"] += missed_ep
            stats["missed_other_moves"] += missed_other
            stats["positions_with_false"] += false_count > 0
            stats["positions_with_missed"] += missed_count > 0
            stats["ep_positions"] += label[2] >= 0
            if false_count and len(examples[name]) < 30:
                examples[name].append({"game": label[0], "ply": label[1], "false_candidates": false_moves,
                                       "count": false_count})
            row[name] = {"candidate_count": count, "false_count": false_count,
                         "false_ep_count": false_ep, "false_other_count": false_other,
                         "missed_count": missed_count, "missed_ep_count": missed_ep,
                         "missed_other_count": missed_other, "false_moves": false_moves,
                         "missed_moves": missed_moves}
        result_rows.append(row)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if args.out.suffix == ".gz" else open
    with opener(args.out, "wt") as f:
        for row in result_rows:
            f.write(json.dumps(row, separators=(",", ":")) + "\n")
    try:
        archive_name = str(args.archive.relative_to(ROOT))
    except ValueError:
        archive_name = str(args.archive)
    summary = {"archive": archive_name, "unique_game_ids_requested": len(game_ids),
               "games_unavailable_or_invalid": skipped, "positions_checked": len(labels),
               "positions_with_ep_right": sum(ep >= 0 for _, _, ep in labels),
               "aggregate": aggregate, "false_examples": examples,
               "event_rows_source": str(args.events.relative_to(ROOT)) if args.events.is_relative_to(ROOT) else str(args.events),
               "position_rows": str(args.out.relative_to(ROOT)) if args.out.is_relative_to(ROOT) else str(args.out),
               "meaning": "Compare observation-derived candidate move sets with true replay legal moves; not an Elo estimate."}
    summary_path = args.out.with_suffix("") if args.out.suffix == ".gz" else args.out
    summary_path = summary_path.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
