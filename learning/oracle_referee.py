"""The course referee with a true-board side channel, for the oracle experiment only.

Runs the kit's referee unchanged (imported from ~/git/fow-starter, never copied) and wraps
its frame builder: after every move the true board is written next to the replay as
`<output>.truth`, one line, "<64 squares a1..h8> <w|b> <castling> <ep>", the format
mist-c reads under MIST_ORACLE_FILE. The literal `{truth}` in either bot command line is
replaced by that path, so a queue can say `"a_env": ["MIST_ORACLE_FILE={truth}"]`.
Selected by the local runner when FOW_REFEREE names this file (learning/compare_archives.py).
"""
import os
import sys
from pathlib import Path

KIT = Path.home() / "git" / "fow-starter"
sys.path.insert(0, str(KIT))
import referee  # noqa: E402  (the kit's module, from its own directory)


def main() -> None:
    argv = sys.argv[1:]
    output = Path(argv[argv.index("--output") + 1])
    truth = str(output) + ".truth"
    argv = [a.replace("{truth}", truth) for a in argv]
    original = referee.make_frame

    def make_frame(board, clocks, move=None):
        frame = original(board, clocks, move)
        fen = board.fen(en_passant="fen").split()   # placement, side, castling, ep square
        tmp = truth + ".tmp"
        with open(tmp, "w") as f:
            f.write(f"{frame['board']} {fen[1]} {fen[2]} {fen[3]}\n")
        os.replace(tmp, truth)
        return frame

    referee.make_frame = make_frame
    sys.argv = [str(KIT / "referee.py")] + argv
    referee.main()


if __name__ == "__main__":
    main()
