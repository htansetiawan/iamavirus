"""Illustrate two recorded duck games; highlights are retrospective annotations."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

PIECES = dict(zip("KQRBNPkqrbnp", "♔♕♖♗♘♙♚♛♜♝♞♟"))
VALUES = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 0}


def board(ax, text, title, truth=False):
    for square, piece in enumerate(text):
        x, y = square % 8, square // 8
        color = "#dededb" if piece == "?" else ("#ecece9" if (x + y) % 2 == 0 else "#fafaf9")
        ax.add_patch(Rectangle((x, y), 1, 1, facecolor=color, edgecolor="white", linewidth=.5))
        if piece not in "-?":
            ax.text(x + .5, y + .47, PIECES[piece], ha="center", va="center",
                    fontsize=25, fontfamily="DejaVu Sans", color="#252525")
        elif piece == "?":
            ax.text(x + .5, y + .5, "?", ha="center", va="center", fontsize=12, color="#8c8c87")
    for square, color in [(7, "#bd7b31"), (31, "#3b6b87")]:  # h1 / h4
        ax.add_patch(Rectangle((square % 8, square // 8), 1, 1, fill=False,
                               edgecolor=color, linewidth=2.3))
    ax.annotate("", xy=(7.5, 3.5), xytext=(6.5, 3.5),
                arrowprops={"arrowstyle": "->", "color": "#3b6b87", "lw": 2})
    if truth:
        ax.annotate("", xy=(7.5, 3.05), xytext=(7.5, .95),
                    arrowprops={"arrowstyle": "->", "color": "#bd7b31", "lw": 1.6, "linestyle": "--"})
    ax.set(xlim=(0, 8), ylim=(0, 8), aspect="equal", title=title)
    ax.set_xticks([i + .5 for i in range(8)], list("abcdefgh"))
    ax.set_yticks([i + .5 for i in range(8)], list("12345678"))
    ax.tick_params(length=0, labelsize=9, colors="#666660")
    for spine in ax.spines.values():
        spine.set_visible(False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spool", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    games = {game: json.loads((args.spool / f"{game}-replay.json").read_text())
             for game in ("abt27me2", "x0l4i8ns")}
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "text.color": "#252525", "axes.labelcolor": "#666660"})
    fig = plt.figure(figsize=(11, 9.5), facecolor="white")
    grid = fig.add_gridspec(2, 2, height_ratios=(3, 1.5), hspace=.43, wspace=.3)
    previous = games["abt27me2"]["frames"][-2]
    assert previous["ply"] == 139 and previous["move"] == "e1h1"
    assert previous["black"][7] == "?" and previous["black"][31] == "-"
    board(fig.add_subplot(grid[0, 0]), previous["board"], "True board after 70.Rh1", truth=True)
    board(fig.add_subplot(grid[0, 1]), previous["black"], "Duck's actual view before 70…Kh4")
    for index, (game, replay) in enumerate(games.items()):
        side = 0 if replay["white"] == "IAmAVirus" else 1
        material = [sum(VALUES[p.lower()] * (1 if p.isupper() else -1)
                        for p in frame["board"] if p != "-") * (1 if side == 0 else -1)
                    for frame in replay["frames"]]
        ax = fig.add_subplot(grid[1, index])
        ax.plot(range(len(material)), material, color="#3b6b87", linewidth=1.7)
        ax.axhline(0, color="#d2d2cd", linewidth=.8)
        ax.scatter([len(material) - 1], [material[-1]], color="#3b6b87", s=22)
        ax.set(xlabel="Ply (one player's move)", ylabel="Our material minus opponent",
               title=f"{game}: {'win' if replay['result'] == '1-0' else 'draw'}, final {material[-1]:+d}")
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["bottom", "left"]].set_color("#d2d2cd")
        ax.tick_params(colors="#666660", labelsize=9)
        ax.grid(axis="y", color="#f0f0ed", linewidth=.7)
    fig.suptitle("An empty visible square can be attacked from fog", fontsize=17, y=.985)
    fig.text(.5, .947, "h4 was visibly empty; the rook on h1 was hidden. Duck chose g4h4; g4f4 was safe on the true board.",
             ha="center", fontsize=10, color="#666660")
    fig.text(.5, .018, "Recorded v38 vs duck v11 · November 11 · Highlights are analyst annotations, not inputs supplied to either bot.\n"
             "Material uses P=1, N=B=3, R=5, Q=9. Two examples do not establish a matchup improvement.",
             ha="center", fontsize=9, color="#666660")
    args.out.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "svg"):
        path = args.out / f"duck-positive-controls.{extension}"
        if path.exists():
            raise FileExistsError(path)
        fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
        if extension == "svg":
            # SVG path line endings are whitespace separators. Normalize the
            # generated source without changing coordinates, labels or style.
            path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
        print(path)
    plt.close(fig)


if __name__ == "__main__":
    main()
