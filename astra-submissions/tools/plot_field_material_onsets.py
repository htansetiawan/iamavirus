"""Standalone presentation figure from already reviewed retrospective cases.

Uses system Python's matplotlib; neither a browser nor a website is involved.
The explicit illustration selection is not an experimental sampling rule.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'astra-submissions/analysis/field-material-onsets-20261111'
ROWS = ROOT / 'data/astra-spool/field-material-onsets-20261111/rows.json'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    review = json.loads((OUT / 'review.json').read_text())
    assert review['status'] == 'complete' and sha(ROWS) == review['original_rows_sha256']
    rows = json.loads(ROWS.read_text())
    losses = [r for r in rows if r['score'] == 0 and r['onset']]
    wins = [r for r in rows if r['score'] == 1 and r['onset'] and r['first_later_even_ply'] is not None]
    loss = min(losses, key=lambda r: (abs(r['onset']['ply'] - 51) + abs(r['plies'] - r['onset']['ply'] - 29), r['game']))
    win = min(wins, key=lambda r: (r['plies'], r['game']))
    cases = [loss, win]
    assets = OUT / 'assets'
    assets.mkdir(exist_ok=False)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': '#333333',
                         'axes.labelcolor': '#555555', 'xtick.color': '#666666', 'ytick.color': '#666666',
                         'svg.hashsalt': 'iamavirus-material-onsets-v1'})
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.2), sharey=True, layout='constrained')
    lo = min(min(r['material_trajectory']) for r in cases) - 2
    hi = max(max(r['material_trajectory']) for r in cases) + 2
    for ax, row in zip(axes, cases, strict=True):
        values = row['material_trajectory']
        onset = row['onset']['ply']
        ax.axhspan(lo, -3, color='#f3f3f3', zorder=0)
        ax.axhline(0, color='#c6c6c6', linewidth=.8)
        ax.axhline(-3, color='#8b8b8b', linewidth=1, linestyle=(0, (3, 3)))
        ax.axvspan(onset, onset + 4, color='#a9b9c9', alpha=.38, linewidth=0)
        ax.plot(range(len(values)), values, color='#3f3f3f', linewidth=1.5, drawstyle='steps-post')
        ax.scatter([onset], [values[onset]], color='#4e6c88', s=27, zorder=5)
        ax.annotate(f'Five-frame deficit starts\nat ply {onset}', (onset, values[onset]),
                    xytext=(-75, 36), textcoords='offset points', fontsize=9, color='#3e5970',
                    arrowprops={'arrowstyle': '-', 'color': '#70899f', 'linewidth': .8},
                    bbox={'facecolor': 'white', 'edgecolor': 'none', 'alpha': .9, 'pad': 2})
        end = row['plies']
        ax.scatter([end], [values[-1]], color='#222222', s=25, zorder=5)
        if row['score'] == 1:
            recovery = row['first_later_even_ply']
            ax.scatter([recovery], [values[recovery]], color='#517b63', s=27, zorder=5)
            ax.annotate(f'At least even\nat ply {recovery}', (recovery, values[recovery]), xytext=(-64, 30),
                        textcoords='offset points', fontsize=9, color='#466c56',
                        arrowprops={'arrowstyle': '-', 'color': '#73937f', 'linewidth': .8},
                        bbox={'facecolor': 'white', 'edgecolor': 'none', 'alpha': .9, 'pad': 2})
        outcome = 'Loss' if row['score'] == 0 else 'Win'
        ax.set_title(f'{outcome} vs {row["opponent"]} v{row["opponent_version"]}\n{row["side"].capitalize()} · {row["game"]} · ends at ply {end}',
                     fontsize=10, loc='left', pad=11)
        ax.set_xlabel('Ply (one half-move)')
        ax.set_xlim(0, end + 3)
        ax.set_ylim(lo, hi)
        ax.grid(axis='y', color='#e9e9e9', linewidth=.6)
        ax.set_axisbelow(True)
        ax.spines[['top', 'right']].set_visible(False)
        for side in ['left', 'bottom']:
            ax.spines[side].set_color('#cccccc')
    axes[0].set_ylabel('Our material balance (simple points)')
    fig.suptitle('A material deficit can precede a loss — or be recovered', fontsize=12, x=.01, ha='left')
    svg, png = assets / 'material-timelines.svg', assets / 'material-timelines.png'
    fig.savefig(svg, metadata={'Date': None})
    fig.savefig(png, dpi=190)
    plt.close(fig)
    record = dict(at=datetime.now(timezone.utc).isoformat(), purpose='Two selected teaching cases, not an experimental or causal comparison.',
                  selection='Loss minimizes distance to cohort loss medians onset=51 and onset-to-end=29; win is shortest with a five-frame deficit and later even material. Lexical game-ID ties.',
                  cases=[dict(game=r['game'], side=r['side'], opponent=r['opponent'], opponent_version=r['opponent_version'], score=r['score'],
                              onset=r['onset']['ply'], plies=r['plies'], later_even=r['first_later_even_ply'], replay_sha256=r['replay_sha256']) for r in cases],
                  matplotlib_version=matplotlib.__version__, rows_sha256=sha(ROWS), source_sha256=sha(Path(__file__)),
                  figures={str(p.relative_to(ROOT)): sha(p) for p in [svg, png]},
                  caption='Material is P/N/B/R/Q/K=1/3/3/5/9/0; gray below -3, blue band marks five consecutive recorded frames. Both axes share scale. All numbers are true-board hindsight; these two histories do not establish causes or bot strength.')
    with (OUT / 'figure-selection.json').open('x') as stream:
        stream.write(json.dumps(record, indent=2) + '\n')
    print(json.dumps(dict(cases=record['cases'], figure=str(svg.relative_to(ROOT))), indent=2))


if __name__ == '__main__':
    main()
