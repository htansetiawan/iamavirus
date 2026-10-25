#!/usr/bin/env python3
"""Apply the measured EP observation and one-ply-history candidate to v35 source."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent

HISTORY_HELPER = r'''

/* Add an en-passant action when the immediately preceding own-side view,
 * followed by exactly one opponent move, proves the opponent's double push.
 * The referee supplies a view after every ply, so `previous_view` is the view
 * immediately before that opponent move. */
int view_moves_with_history(const char view[65], const char previous_view[65],
                           int us, bb_t our_castle, MoveList *out) {
    view_moves(view, us, our_castle, out);
    if (!previous_view) return out->count;
    char board[65];
    for (int sq = 0; sq < 64; ++sq) board[sq] = view[sq] == '?' ? '-' : view[sq];
    board[64] = '\0';
    Position p;
    if (pos_from_board_string(&p, board, us, our_castle, -1) != 0) return out->count;
    const int us_dr = us == WHITE ? 8 : -8;
    const int fifth = us == WHITE ? 4 : 3;
    const char enemy_pawn = us == WHITE ? 'p' : 'P';
    for (bb_t pawns = p.by_type[PAWN] & p.by_color[us]; pawns; pawns &= pawns - 1) {
        const int from = __builtin_ctzll(pawns), file = from % 8;
        if (from / 8 != fifth) continue;
        for (int df = -1; df <= 1; df += 2) {
            if (file + df < 0 || file + df > 7) continue;
            const int beside = from + df, to = beside + us_dr;
            const int start = beside + 2 * us_dr, middle = beside + us_dr;
            if (view[beside] != enemy_pawn || view[to] != '-') continue;
            if (previous_view[start] != enemy_pawn || previous_view[middle] != '-' ||
                previous_view[beside] != '-') continue;
            const Move m = MAKE_MOVE(from, to, NO_PIECE);
            int found = 0;
            for (int i = 0; i < out->count; ++i) found |= out->moves[i] == m;
            if (!found && out->count < (int)(sizeof out->moves / sizeof out->moves[0]))
                out->moves[out->count++] = m;
        }
    }
    return out->count;
}
'''


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    if old not in text:
        raise RuntimeError(f"expected source block not found in {path}")
    path.write_text(text.replace(old, new, 1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=Path, required=True,
                    help="extracted v35 root containing src/belief.c and src/main.c")
    args = ap.parse_args()
    root = args.source_root.resolve()
    if not (root / "src/belief.c").is_file():
        raise SystemExit("source root must contain src/belief.c")
    subprocess.run(["patch", "-p1", "-i", str(HERE / "belief-ep-observation.patch")],
                   cwd=root, check=True)
    h = root / "src/belief.h"
    replace_once(h, "int view_moves(const char view[65], int us, bb_t our_castle, MoveList *out);",
                 "int view_moves(const char view[65], int us, bb_t our_castle, MoveList *out);\n"
                 "/* Also use the immediately preceding own-side observation to prove a double push. */\n"
                 "int view_moves_with_history(const char view[65], const char previous_view[65],\n"
                 "                           int us, bb_t our_castle, MoveList *out);")
    belief = root / "src/belief.c"
    with belief.open("a") as f:
        f.write(HISTORY_HELPER)
    main_c = root / "src/main.c"
    replace_once(main_c, '    char view[65] = "";\n    int views = 0, moved = 0, decisions = 0, rebuilds = 0;',
                 '    char view[65] = "", previous_view[65] = "";\n'
                 '    int previous_view_valid = 0;\n'
                 '    int views = 0, moved = 0, decisions = 0, rebuilds = 0;')
    replace_once(main_c, '        if (is_view(line)) {\n            memcpy(view, line, 65);',
                 '        if (is_view(line)) {\n'
                 '            previous_view_valid = views > 0;\n'
                 '            if (previous_view_valid) memcpy(previous_view, view, 65);\n'
                 '            memcpy(view, line, 65);')
    replace_once(main_c, '        view_moves(view, us, front.castle, &allowed);',
                 '        view_moves_with_history(view, previous_view_valid ? previous_view : NULL,\n'
                 '                                us, front.castle, &allowed);')
    paths = [root / "src/belief.h", root / "src/belief.c", root / "src/main.c"]
    print("\n".join(f"{p.relative_to(root)} sha256={sha(p)}" for p in paths))


if __name__ == "__main__":
    main()
