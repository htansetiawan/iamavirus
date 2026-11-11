"""Export the checked statistical illustrations; no games or inference jobs."""
import hashlib
import importlib.util
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "astra-submissions/analysis/measurement-resolution-20261111"
PNG = ROOT / "docs/assets/presentation/benchmark-resolution-20261111.png"
SVG = PNG.with_suffix(".svg")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    data = json.loads((OUT / "result.json").read_text())
    spec = importlib.util.spec_from_file_location("resolution_formulae", Path(__file__).with_name("benchmark_resolution.py"))
    calc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(calc)
    assert not PNG.exists() and not SVG.exists()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "svg.hashsalt": "iamavirus-benchmark-resolution-20261111"})
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.1), gridspec_kw={"width_ratios": [1.05, 1]})
    ink, gray, blue = "#30363a", "#737b82", "#526b87"
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color("#d6d9dc")
        ax.tick_params(colors=gray, length=3)
        ax.grid(axis="x", color="#eceeef", linewidth=.8)
        ax.set_axisbelow(True)
    for y, key, label in ((1, "20_of_40", "20 wins / 40 games"), (0, "9_of_16", "9 wins / 16 games")):
        row = data["wilson95"][key]
        lo, hi = row["elo_interval"]
        center = row["elo_point"]
        axes[0].plot([lo, hi], [y, y], color=blue, linewidth=5, solid_capstyle="round")
        axes[0].plot(center, y, "o", color=ink, markersize=6)
        axes[0].text(center, y + .22, f"{lo:+.0f} to {hi:+.0f}", ha="center", color=ink, fontsize=10)
    axes[0].axvline(0, color=gray, linewidth=1, linestyle=":")
    axes[0].axvspan(-15, 15, color="#e7e9eb", zorder=0)
    axes[0].set(yticks=[0, 1], yticklabels=["9 / 16", "20 / 40"], ylim=(-.4, 1.5),
                xlim=(-160, 240), xlabel="Score interval mapped to Elo difference",
                title="Small samples leave broad uncertainty")
    axes[0].text(0, -.28, "shaded: ±15 Elo", ha="center", fontsize=8.5, color=gray)
    xs = np.linspace(-100, 300, 201)
    ys = [calc.gate_pass_probability(10, 16, calc.score_at_elo(float(x))) for x in xs]
    axes[1].plot(xs, ys, color=blue, linewidth=2.3)
    for delta, yoffset in ((0, -.14), (100, -.15), (200, -.14)):
        row = next(r for r in data["fixed_ten_of_sixteen_gate"] if r["assumed_elo_difference"] == delta)
        probability = row["ten_of_sixteen_pass_probability"]
        assert abs(probability - calc.gate_pass_probability(10, 16, calc.score_at_elo(delta))) < 1e-14
        axes[1].plot(delta, probability, "o", color=ink, markersize=5)
        axes[1].text(delta, probability + yoffset, f"{probability:.1%}", ha="center", fontsize=9.5, color=ink)
    axes[1].set(xlim=(-100, 300), ylim=(0, 1.03), yticks=[0, .25, .5, .75, 1],
                yticklabels=["0%", "25%", "50%", "75%", "100%"],
                xlabel="Assumed true Elo advantage", ylabel="Probability of passing",
                title="Ten wins from sixteen is a screen")
    fig.suptitle("A screening result is not a precise strength estimate", fontsize=15, color=ink, x=.05, ha="left")
    fig.text(.05, .035, "Illustrative 95% Wilson intervals and exact binomial tails. Independent decisive games; no pairing, draws or selection adjustment.",
             fontsize=8.2, color=gray)
    fig.subplots_adjust(left=.075, right=.98, top=.79, bottom=.22, wspace=.36)
    PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(PNG, dpi=220, facecolor="white")
    fig.savefig(SVG, facecolor="white", metadata={"Date": None})
    SVG.write_text("\n".join(line.rstrip() for line in SVG.read_text().splitlines()) + "\n")
    plt.close(fig)
    with (OUT / "figure.json").open("x") as stream:
        json.dump(dict(result_sha256=sha(OUT / "result.json"), source_sha256=sha(Path(__file__)),
                       calculator_sha256=sha(Path(__file__).with_name("benchmark_resolution.py")),
                       png_sha256=sha(PNG), svg_sha256=sha(SVG),
                       limits="Arithmetic illustration, not an engine strength estimate or deployed website."), stream, indent=1)
        stream.write("\n")
    print(json.dumps({"png": str(PNG), "svg": str(SVG)}))


if __name__ == "__main__":
    main()
