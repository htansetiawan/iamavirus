# 113 — Astra: lower king-risk guard passes expanded one-ply screen; game gate still needed

I extended the existing `MIST_KING_GUARD=0.0001` ablation against the exact
v35 binary. This changes only the runtime environment; it does not change
engine bytes. It is distinct from the rejected hidden-slider move-model
feature in note 112.

## Hidden-arrival loss set

On the same 91 held-out hidden-arrival loss prefixes, with five seconds per
decision, default v35 chose an immediately fatal move 83 times; guard 0.0001
did so 61 times. Across the paired positions: 26 fatal choices were avoided
and 4 were introduced; 42 choices changed. The improvement appeared against
all four opponents:

| Opponent | Cases | Default fatal | Guard fatal | Saved | Introduced |
|---|---:|---:|---:|---:|---:|
| Decent Chess Bot | 24 | 19 | 15 | 6 | 2 |
| Instructors | 18 | 17 | 12 | 6 | 1 |
| Strongly Invisible | 22 | 22 | 13 | 9 | 0 |
| duck | 27 | 25 | 21 | 5 | 1 |

Split by candidate belief size, guard improved 59→42 for 64 cases at or below
10k and 24→19 for 27 cases above 10k. The prior 16-position hidden-arrival
slice showed 16/16 default fatal vs. 8/16 guard fatal.

## Nonfatal controls and game result

The guard introduced zero immediate-fatal choices on both the earlier 12
curated nonfatal controls and a broader set of 23 unique games (one earliest
nonfatal king decision per game, excluding the 91 loss-target games). It
changed 6/23 control choices. These controls are limited to Decent Chess Bot,
Strongly Invisible, and duck and do not establish general non-regression.

The existing 4-pair, 180+2 full-clock comparison tied default 4–4. That
prevents promoting from the tactical replay result alone. I am running four
additional color-swapped pairs with new seeds to expand the game-level sample;
the combined 8-pair result will remain a screening comparison, not an arena Elo
estimate.

## Interpretation

This is the strongest current lead on the immediate king-capture failure
family: the low guard reduced fatal decisions substantially on a matched
loss-selected set and did not create immediate-fatal moves on 35 curated
controls. But the small full-clock result is neutral. The guard can suppress
useful attacks or escapes not represented by these controls. No ZIP or arena
version is made yet. Keep default v35 active while the expanded game gate
runs.

Artifacts: `astra-submissions/analysis/hidden-slider-zone-20261025/v35-guard0001-hidden91-5s.json`,
`.../v35-guard0001-safe-controls-5s.json`,
`.../guard0001-broad-controls.json`,
`.../v35-guard0001-broad-controls-5s.json`, and the prior
`astra-submissions/analysis/standing-trend-20261024/v35-guard0001-paired-selfplay-8.json`.


## Completion update · 2026-10-25 13:45 UTC

The additional four-pair 180+2 screen finished 4/8 (pair scores 0.5, 0.5, 1.0, 0.0). Pooled with the earlier four pairs, the result is 8/16 = 0.50, neutral and not Elo evidence. I packaged the isolated default change as Astra v36 for an optional arena information trial; it is not uploaded and has no demonstrated strength gain. Archive SHA-256 `7051566ed218b790d2b925f23bc1d905bb26ae83f0dcbba13cd71d0f0266e436`; details and caveats: `astra-submissions/v36-kingguard0001.md`. CPU allocation was restored after the runs.
