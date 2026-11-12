# Correct benchmark resolution and the next learning decision

This review clarifies statistical units in the historical evaluation page,
makes old proposals visibly historical, and connects the new capture
curriculum to the current presentation/decision priorities. It runs no bot,
training, new replay query or strength experiment.

The human memo is
[What the next learning step must establish](../../../docs/learning-review-20261111.md).
The source review is PR 1; the separate catalogue/curriculum source is PR 8.
Website deployment stays disabled.

## Arithmetic correction

The old `docs/evaluation.md` said forty games resolve a 15-point gap without
specifying units. My initial commentary overstated this as an explicit Elo
claim. It could mean percentage points: a balanced 20/40 result has a 95%
Wilson score interval [0.3519953, 0.6480047], about ±14.8 percentage points.
Mapping its endpoints through `400*log10(p/(1-p))` gives [−106.02, +106.02] Elo.
The revised text disambiguates these quantities rather than asserting the
original author meant Elo. This does not establish formal detection power.

An independent ten-of-sixteen screen passes 22.7249% at equal strength.
At a hypothetical +100-Elo advantage it fails 34.2611%. These are exact
binomial tail calculations under the stated assumptions, not retrospective
selection-adjusted strength claims for any engine. Draws, paired games,
opponent shifts and stopping need appropriate separate treatment. Old gates
retain their outcomes; no closed candidate is reopened.

[Original result](result.json) · [exact original producer](calculator-original.py)
· [reproduction](reproduction.json) · [environment](environment.json).

The revised [calculator](../../tools/benchmark_resolution.py) reads the old
document from immutable commit `f744934e4e12ef9e4018893bd037184b23efae42`, so it
still works after the correction. Its numerical function ASTs are unchanged.
The original and reproduced numerical payloads match exactly; both Wilson
examples and four binomial tails agree with the existing SciPy installation,
with rational and zero/one controls. The original source/result stay intact.

```sh
.venv/bin/python astra-submissions/tools/benchmark_resolution.py \
  --output /tmp/iamavirus-resolution-copy.json
```

The command needs repository history containing the pinned old commit and an
unused output filename. No data or environment installation is performed.

## Current loss context, not a new experiment

A post-hoc reuse of 414's frozen current 68-game labels finds 24 own v38 losses:
three king-bait endings, only one with a true-board safe final alternative;
ten with no immediate non-losing final move; twenty already at least three
material points behind. These counts overlap and use exact previously audited
terminal labels. They are not an earlier causal diagnosis, a guaranteed game
rescue, a strategy-value target or a global Elo bound.

[Counts and pinned private sources](current-loss-context.json).
The review filters the source catalogue's `current68` IDs, locates team
`a2c35173659545c99752376a70418438` at played version 38 in each replay, derives
its result, and summarizes its existing terminal motif. It preserves the one
opponent process-failure win and does not reinterpret the cohort as a strength
confirmation.

The resulting priority is to identify an earlier decision mechanism before
using this capture subset as the next complete candidate. The full memo
separates risk prediction, capture-choice prediction and continuation value,
and preserves negative style/response/M4/prior/playing results.

## Source and rendering checks

- Historical `open-problems.md` and `plan-month.md` receive inserted notices
  only; their old bodies are unchanged. Navigation labels now identify their
  dates rather than advertising an active execution queue.
- The evaluation sentence now specifies units and numerical scope.
- The new review is linked from the presentation entry point and navigation.
- A standalone [PNG](../../../docs/assets/presentation/benchmark-resolution-20261111.png)
  and [SVG](../../../docs/assets/presentation/benchmark-resolution-20261111.svg)
  illustrate the arithmetic; the PNG was visually inspected. The exporter
  normalizes SVG trailing whitespace and its XML parses.
- The local static renderer produces 26 pages. All 917 checked relative
  file/anchor references resolve, including the new bench anchor. This is not
  browser or Mermaid JavaScript validation.

[Combined review](review.json) · [figure pins](figure.json) ·
[figure environment](figure-environment.json) ·
[primary sources and reading scope](research-sources.json) ·
[plot source](../../tools/plot_benchmark_resolution.py).

Original audit manifests/PDFs remain historical snapshots. No source option,
model, engine, GPU, game, ZIP/version, timer/service, production dataset or
website deployment changed.
