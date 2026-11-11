"""Export a presentation figure from the independently reconciled trace."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'astra-submissions/analysis/presentation-multistate-20261111'
ASSETS = ROOT / 'docs/assets/presentation'


def main():
    source = OUT / 'result.json'
    result = json.loads(source.read_text())
    assert result['status'] == 'complete' and result['retained_worlds'] == 128
    assert result['draws'] == 32 and result['distinct_sampled_worlds'] == 2
    worlds = sorted(result['sampled_worlds'], key=lambda w: -w['belief_weight'])
    assert [w['world'] for w in worlds] == [98, 36]
    colors = {98: '#52677b', 36: '#aab3bc'}
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.spines.left': False, 'axes.spines.bottom': False,
                         'text.color': '#32363a', 'axes.labelcolor': '#51565c',
                         'xtick.color': '#73797f', 'ytick.color': '#51565c',
                         'svg.fonttype': 'none'})
    fig = plt.figure(figsize=(11, 6.3), facecolor='white')
    grid = fig.add_gridspec(2, 2, left=.11, right=.96, top=.81, bottom=.12,
                           height_ratios=[1, 1.2], hspace=.68, wspace=.38)
    belief = fig.add_subplot(grid[0, 0])
    categories = ['W98', 'W36', 'Other 126']
    posterior = [worlds[0]['belief_weight'], worlds[1]['belief_weight'], result['unsampled_belief_mass']]
    empirical = [worlds[0]['chance_weight'], worlds[1]['chance_weight'], 0]
    for y, (p, q) in enumerate(zip(posterior, empirical)):
        belief.barh(y - .17, p, height=.25, color='#aeb7bf')
        belief.barh(y + .17, q, height=.25, color='#52677b')
        belief.text(max(p, q) + .025, y, f'{100*p:.3f}% / {100*q:.3f}%', va='center', fontsize=8.5)
    belief.set_yticks(range(3), categories); belief.invert_yaxis(); belief.set_xlim(0, 1.36)
    belief.set_xticks([0, .5, 1]); belief.xaxis.set_major_formatter(PercentFormatter(1))
    belief.tick_params(axis='both', length=0)
    belief.set_title('Retained weight / search chance share', loc='left', fontsize=10, pad=16)
    belief.text(0, -.21, 'Light: full belief    Dark: observed draw frequencies',
                transform=belief.transAxes, fontsize=8.5, color='#73797f')
    draws = fig.add_subplot(grid[0, 1]); draws.set_xlim(-.2, 16); draws.set_ylim(-.65, 2.35); draws.axis('off')
    draws.set_title('The actual 32 draws, in order', loc='left', fontsize=10, pad=16)
    for i, world in enumerate(result['draw_order']):
        col, row = i % 16, 1 - i // 16
        draws.add_patch(Rectangle((col, row), .84, .72, facecolor=colors[world], edgecolor='white'))
        draws.text(col + .42, row + .36, 'A' if world == 98 else 'B', ha='center', va='center',
                   color='white' if world == 98 else '#32363a', fontsize=8, weight='bold')
    draws.text(0, -.45, 'A = W98: 29 draws     B = W36: 3 draws', fontsize=9)
    draws.text(0, 2.08, 'Repeated draws become two weighted branches.', fontsize=9, color='#73797f')
    strategy = fig.add_subplot(grid[1, :])
    roots = sorted(result['final_strategy'], key=lambda r: -r['probability'])[:5]
    assert abs(sum(r['probability'] for r in roots) - 1) < 1e-12
    names = {'g1f3': 'Ng1–f3', 'f1d3': 'Bf1–d3', 'h2h4': 'h2–h4', 'c2c3': 'c2–c3', 'd2b3': 'Nd2–b3'}
    for y, root in enumerate(roots):
        probability = root['probability']
        strategy.barh(y, probability, height=.56, color='#52677b' if root['selected'] else '#b7bfc6')
        strategy.text(probability + .006, y, f'{100*probability:.2f}%', va='center', fontsize=9)
    strategy.set_yticks(range(5), [names[r['move']] for r in roots]); strategy.invert_yaxis()
    strategy.set_xlim(0, .56); strategy.xaxis.set_major_formatter(PercentFormatter(1)); strategy.tick_params(length=0)
    strategy.set_title('One shared root strategy after search; Ng1–f3 is executed', loc='left', fontsize=10, pad=13)
    strategy.grid(axis='x', color='#e7eaed', linewidth=.6); strategy.set_axisbelow(True)
    fig.text(.055, .945, '128 retained positions → 32 weighted draws → 2 search branches', fontsize=14, weight='bold')
    fig.text(.055, .903, 'White decision 5 · c8ozqj0m · 41 permitted moves → 2 guard exclusions → 39 root actions', fontsize=10, color='#73797f')
    fig.text(.055, .035, 'Two-second teaching reconstruction, seed 3831111. Action shares are not win forecasts. The recorded arena move was c2–c3.', fontsize=8, color='#73797f')
    ASSETS.mkdir(parents=True, exist_ok=True)
    files = []
    for suffix in ('svg', 'png'):
        path = ASSETS / ('multistate-sampling.' + suffix)
        assert not path.exists()
        fig.savefig(path, dpi=180, metadata={'Creator': 'IAmAVirus Astra; verified fixed trace'})
        files.append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size))
    plt.close(fig)
    receipt = dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                   plot_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), files=files,
                   scope='Static SVG/PNG generated from the verified original trace; no inference or search rerun.')
    with (OUT / 'figure.json').open('x') as stream: stream.write(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__': main()
