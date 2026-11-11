"""Make a two-page local PDF and matching Markdown from verified source facts.

Uses the existing Matplotlib installation. No new dependencies, bot execution,
service changes, live arena query or website publication.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
NAME = 'presentation-handout-20261111'
OUT = ROOT / 'astra-submissions/analysis' / NAME
PDF = ROOT / 'docs/assets/presentation/iamavirus-v38-review-20261111.pdf'
MD = ROOT / 'docs/presentation-handout.md'
INK, BODY, MUTED, LINE, PALE = '#2f3437', '#4c5359', '#737b82', '#dfe3e6', '#f4f5f6'


def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, value):
    with p.open('x') as stream: stream.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def content():
    inventory = ROOT / 'astra-submissions/analysis/presentation-audit-20261111/inventory.json'
    trace = ROOT / 'astra-submissions/analysis/presentation-multistate-20261111/result.json'
    confirmation = ROOT / 'astra-submissions/analysis/compact-mass-confirmation-20261111/result.json'
    pilot = ROOT / 'astra-submissions/analysis/compact-mass-playing-20261111/result.json'
    arena = ROOT / 'fable-submissions/analysis/v38-arena-20261108/result.md'
    release = ROOT / 'astra-submissions/v38-release.md'
    confirmation_note = ROOT / 'chatroom/355-astra-compact-mass-confirmation.md'
    inv, case, posterior, play = map(read, (inventory, trace, confirmation, pilot))
    assert inv['archive_sha256'] == 'ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f'
    assert inv['history']['records'] == 359889
    assert [inv['move_model']['coefficient_vectors'][name]['count'] for name in ('full', 'cheap')] == [28, 28]
    assert (case['retained_worlds'], case['draws'], case['distinct_sampled_worlds'], case['root_actions']) == (128, 32, 2, 39)
    assert (play['wins'], play['draws'], play['losses'], len(play['unstarted']), play['native_frames_verified']) == (1, 0, 8, 7, 901)
    later = arena.read_text().split('## 620 games (11 Nov 03:27Z)')[-1]
    record = re.search(r'\b(\d+)-(\d+)-(\d+), score', later)
    assert record
    w, d, l = map(int, record.groups()); assert (w, d, l) == (339, 27, 254)
    raw_score = (w + .5 * d) / (w + d + l)
    assert '1.57–1.68×' in release.read_text() and '38% more search nodes' in release.read_text()
    assert '63 unique trajectories' in confirmation_note.read_text() and 'two IAmAVirus observers' in confirmation_note.read_text()
    sampled = sorted(case['sampled_worlds'], key=lambda r: -r['belief_weight'])
    dependencies = [inventory, trace, confirmation, pilot, arena, release, confirmation_note,
                    ROOT / 'docs/presentation-20261203.md', ROOT / 'docs/presentation-tables.md',
                    ROOT / 'docs/presentation-experiments.md', Path(__file__)]
    data = dict(title='IAmAVirus: one move through fog', reviewed='11 November 2026', archive='v38',
        scope='Source-checked review of the immutable v38 package; presentation preparation, not a new release.',
        rule='The arena ends when a mover leaves its own king capturable. Attacking the other king alone does not end the game.',
        cards=[
            ['Observe', 'Read our 64-square private view and clock. A hidden square is unknown; it is not a visibly empty square.'],
            ['Infer', 'Advance weighted possible positions through compatible moves. Merge native position keys. The configured retained-population cap is 200,000.'],
            ['Screen and sample', 'Apply root king/queen risk guards. Normally draw 32 worlds by weight with replacement; merge repeated draws into chance branches.'],
            ['Grow and evaluate', 'Build one local game tree. Stockfish depth-1 child scoring sees both sides on each complete imagined board, not the live true board.'],
            ['Update the strategy', 'PRM+ compares each action with the current mixture using counterfactual values. These regret updates happen inside this move, not across old games.'],
            ['Act', 'Execute the highest-probability permitted root action. Retain belief/front-end history. Discard the FoW tree and regret arrays before the next move.']],
        example_title='A real prefix: 128 positions → 32 draws → 2 branches',
        sample_rows=[[f"W{r['world']}", f"{100*r['belief_weight']:.4f}%", str(r['draws']), f"{100*r['chance_weight']:.3f}%"] for r in sampled]
                    + [['Other 126', f"{100*case['unsampled_belief_mass']:.4f}%", '0', '0%']],
        example='Both branches share one root strategy across 39 actions. The sampler keeps all 128 positions in belief for later observations.',
        example_limit='Fresh two-second reconstruction of c8ozqj0m, White decision 5. Both local runs choose g1f3; the recorded arena action is c2c3. This is a teaching trace.',
        memory='Belief and front-end history survive between moves. Stockfish can retain its own cache. The FoW tree is rebuilt; coefficients and history counts stay frozen between uploads.',
        evidence=[
            ['Scoring', '1.57–1.68× scorer throughput; about 38% more equal-time nodes on the fixed panel. Scores change: the scorer is approximate. The failed Misty gate remains failed; the arena trial was separately authorized.'],
            ['Inference → play', f"Replay panel: 63 games, only two IAmAVirus observers; truth-log-share gain +{posterior['gain']:.5f} nats. The full-engine pilot ends 1W–8L under futility, seven legs unstarted; all 901 frames pass rules checks. Configuration closed."],
            ['Arena snapshot', f"11 Nov, 03:27 UTC: {w}W–{d}D–{l}L in 620 games; raw score {100*raw_score:.1f}%. The later 493 games track v37's historical same-opponent level. Changing opponents and scheduling limit causal claims."]],
        limitations=[
            ['Belief and sampling', 'Capping can lose the real position; weighting can underrate it; a small sample can omit it. These are separate failure modes.'],
            ['Information model', 'One representative opponent history per position. Opponent-compatible past alternatives, full 2-KLUSS gadgets and cross-turn blueprint reuse are absent from v38.'],
            ['Continuation values', 'Stockfish is a perfect-information evaluator on imagined boards. No qualified learned FoW frontier value replaces it.'],
            ['Strategy output', 'The root takes an argmax. World-sampling randomness is distinct from drawing an action from the computed mixed strategy. No full-game Nash certificate.'],
            ['Data lineage', 'Raw collection, taxonomy, exported examples, fitting and packaged models advance separately. Historical metadata and holdout limitations remain explicit.']],
        learning=f"Shipped: two 28-coefficient move models and one {inv['history']['records']:,}-record history file; borrowed Stockfish NNUE. The historical CNN–GRU/PPO policy and neural regret approximation do not play in v38.",
        stance='Our contribution is native implementation, replay instrumentation and measured engineering around published ideas. Faster scoring is established on its panel; a lasting arena strength gain is not established.',
        sources=[['Runtime and table inventory', 'astra-submissions/analysis/presentation-audit-20261111/'],
                 ['Real multi-world trace', 'astra-submissions/analysis/presentation-multistate-20261111/'],
                 ['Speed and release decision', 'astra-submissions/v38-release.md'],
                 ['Confirmed prior and rejected playing pilot', 'chatroom/355 and chatroom/357'],
                 ['620-game reading', 'fable-submissions/analysis/v38-arena-20261108/result.md'],
                 ['Information-set example and source comparison', 'docs/presentation-knowledge.md and chatroom/358']],
        source_sha256={str(p): sha(p) for p in dependencies})
    return data


BOUNDS = []


def text(fig, x, y, value, width=.86, size=10, weight='normal', color=BODY, group=''):
    renderer = fig.canvas.get_renderer()
    prop = FontProperties(family='DejaVu Sans', size=size, weight=weight)
    limit = width * fig.bbox.width
    lines = []
    for paragraph in value.split('\n'):
        line = ''
        for word in paragraph.split():
            candidate = (line + ' ' + word).strip()
            pixels = renderer.get_text_width_height_descent(candidate, prop, ismath=False)[0]
            if line and pixels > limit:
                lines.append(line); line = word
            else: line = candidate
        lines.append(line)
    artist = fig.text(x, y, '\n'.join(lines), fontproperties=prop, color=color,
                      va='top', linespacing=1.25)
    box = artist.get_window_extent(renderer).transformed(fig.transFigure.inverted())
    assert box.x0 >= .025 and box.x1 <= .975 and box.y0 >= .025 and box.y1 <= .99, (group, box.bounds)
    BOUNDS.append(dict(page=int(fig.get_label()), group=group, lines=len(lines), font_points=size,
                       bounds=list(box.bounds)))
    return box.y0


def heading(fig, x, y, value, width=.86):
    return text(fig, x, y, value, width, size=11.5, weight='bold', color=INK, group='heading')


def page(number, title):
    fig = plt.figure(figsize=(8.5, 11), dpi=150, facecolor='white'); fig.set_label(str(number)); fig.canvas.draw()
    text(fig, .065, .974, 'SOURCE REVIEW  /  11 NOVEMBER 2026', size=8.3, color=MUTED, group='badge')
    text(fig, .065, .941, title, size=21, weight='bold', color=INK, group='title')
    fig.lines.append(Line2D([.065, .935], [.058, .058], transform=fig.transFigure, color=LINE, lw=.7))
    text(fig, .065, .042, 'IAmAVirus v38 · ZIP ba6610f299c15891… · Local review copy', size=8, color=MUTED, group='footer')
    text(fig, .89, .042, str(number) + ' / 2', width=.06, size=8, color=MUTED, group='page number')
    return fig


def draw_first(data):
    fig = page(1, data['title'])
    text(fig, .065, .895, 'C engine · 180 seconds + 2 seconds per move · December 3 presentation brief', size=9.8, group='subtitle')
    text(fig, .065, .868, data['rule'], size=9.5, group='rules')
    for i, (title, body) in enumerate(data['cards']):
        col, row = i % 2, i // 2
        x, top, width, height = .065 + col * .447, .812 - row * .116, .423, .105
        fig.patches.append(FancyBboxPatch((x, top - height), width, height,
                          boxstyle='round,pad=0.004,rounding_size=0.006', facecolor=PALE,
                          edgecolor='none', transform=fig.transFigure))
        text(fig, x + .013, top - .012, f'{i+1}  {title}', width - .026, size=10.5, weight='bold', color=INK, group=f'card {i+1} title')
        bottom = text(fig, x + .013, top - .039, body, width - .026, size=9.5, group=f'card {i+1} body')
        assert bottom >= top - height + .004, ('card overflow', i+1, bottom)
    text(fig, .065, .463, 'Tree growth, scoring and regret updates alternate within the move budget.', size=9, color=MUTED, group='loop caption')
    heading(fig, .065, .423, data['example_title'])
    xs, widths = [.075, .39, .62, .77], [.30, .21, .12, .15]
    for x, width, label in zip(xs, widths, ['Retained position', 'Belief weight', 'Draws', 'Search share']):
        text(fig, x, .385, label, width, size=9.1, weight='bold', color=MUTED, group='sample header')
    for i, row in enumerate(data['sample_rows']):
        for x, width, label in zip(xs, widths, row):
            text(fig, x, .354 - i * .030, label, width, size=10, group='sample cell')
    text(fig, .065, .261, data['example'], size=9.6, group='sample meaning')
    text(fig, .065, .219, data['example_limit'], size=9.1, color=MUTED, group='sample limitation')
    heading(fig, .065, .158, 'Memory and learning lifetimes')
    bottom = text(fig, .065, .130, data['memory'], size=9.5, group='memory')
    assert bottom >= .070, ('page one memory overflow', bottom)
    return fig


def draw_second(data):
    fig = page(2, 'Evidence, contribution and limits')
    text(fig, .065, .895, 'Component performance, prediction quality and playing strength are separate measurements.', size=9.8, group='subtitle')
    heading(fig, .065, .853, 'What the record supports')
    y = .817
    for title, body in data['evidence']:
        text(fig, .065, y, title, width=.17, size=10, weight='bold', color=INK, group='evidence label')
        bottom = text(fig, .25, y, body, width=.685, size=9.6, group='evidence body')
        y = bottom - .024
    assert y >= .50, ('evidence block overflow', y)
    heading(fig, .065, .505, 'Main architectural limits')
    y = .470
    for title, body in data['limitations']:
        bottom = text(fig, .065, y, title + ': ' + body, size=9.5, group='limitation')
        y = bottom - .014
    assert y >= .220, ('limitations block overflow', y)
    bottom = text(fig, .065, .211, data['learning'], size=9.4, group='deployed learning')
    assert bottom >= .145
    text(fig, .065, .131, data['stance'], size=9.4, group='contribution')
    return fig


def markdown(data):
    lines = ['# IAmAVirus: two-page human review', '',
             '[Download the printable PDF](assets/presentation/iamavirus-v38-review-20261111.pdf).', '',
             '*Local source-checked review, 11 November 2026. The website deployment remains disabled.*', '',
             '## How one move works', '', data['rule'], '']
    for i, (title, body) in enumerate(data['cards'], 1): lines += [f'{i}. **{title}.** {body}', '']
    lines += ['Tree growth, evaluation and regret updates alternate within the move budget.', '',
              '## ' + data['example_title'], '', '| Position | Belief weight | Draws | Search share |',
              '| --- | ---: | ---: | ---: |']
    lines += ['| ' + ' | '.join(row) + ' |' for row in data['sample_rows']]
    lines += ['', data['example'], '', data['example_limit'], '', data['memory'], '', '## Evidence and limits', '']
    for title, body in data['evidence']: lines += [f'**{title}.** {body}', '']
    for title, body in data['limitations']: lines += [f'- **{title}.** {body}', '']
    lines += [data['learning'], '', data['stance'], '', '## Evidence paths', '']
    for title, path in data['sources']: lines += [f'- {title}: `{path}`.', '']
    lines += ['Read next: [runtime and tables](presentation-tables.html), [real move trace](presentation-move.html),',
              '[experiment record](presentation-experiments.html), [who knows what](presentation-knowledge.html).', '',
              'This handout does not report a new experiment, candidate, live rating, model update or deployment.', '']
    return '\n'.join(lines)


def main():
    OUT.mkdir(exist_ok=True)
    assert not PDF.exists() and not MD.exists()
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'pdf.fonttype': 42})
    data = content(); save(OUT / 'content.json', data)
    PDF.parent.mkdir(parents=True, exist_ok=True)
    figures = [draw_first(data), draw_second(data)]
    with PdfPages(PDF, metadata={'Title': 'IAmAVirus v38 — Human review', 'Author': 'IAmAVirus / Astra',
                                'CreationDate': datetime.now(timezone.utc),
                                'Subject': 'Source-checked runtime, evidence and limitations; local review copy'}) as output:
        for fig in figures: output.savefig(fig); plt.close(fig)
    MD.write_text(markdown(data))
    save(OUT / 'result.json', dict(at=datetime.now(timezone.utc).isoformat(), status='generated', pages=2,
          text_blocks=len(BOUNDS), layout=BOUNDS, pdf_sha256=sha(PDF), markdown_sha256=sha(MD),
          content_sha256=sha(OUT / 'content.json'), source_sha256=data['source_sha256'],
          scope='A local presentation handout from existing verified records. Generation checks layout bounds; external PDF parse and visual review follow. No bot, model, game, service, commit, push or deployment.'))
    print(json.dumps(dict(pdf=str(PDF), markdown=str(MD), pages=2, text_blocks=len(BOUNDS))), flush=True)


if __name__ == '__main__': main()
