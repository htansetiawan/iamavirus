# Arena standing and style trend, Oct 11–24

This is a reproducible summary of 14 saved daily reports, not a fresh API read.
The latest source snapshot was generated 2026-10-24 11:36 UTC; current standings
may have changed since.

## Who moved

| Team | Oct 11 rank / Elo / version | Oct 24 rank / Elo / version | Elo change | Rank change |
|---|---:|---:|---:|---:|
| IAmAVirus | #8 / 1761 / v30 | #8 / 1935 / v35 | +174 | 0 |
| Greek Gift | #1 / 2163 / v16 | #1 / 2418 / v25 | +255 | 0 |
| Knight Vision | #2 / 2079 / v36 | #2 / 2155 / v36 | +76 | 0 |
| Strongly Invisible | #3 / 2055 / v35 | #3 / 2096 / v37 | +41 | 0 |
| Decent Chess Bot | #4 / 2053 / v4 | #4 / 2034 / v7 | −19 | 0 |
| Mist Opportunities | #7 / 1896 / v2 | #5 / 1959 / v2 | +63 | +2 |
| Instructors | #6 / 1920 / v4 | #6 / 1957 / v4 | +37 | 0 |
| duck | #5 / 1976 / v5 | #7 / 1945 / v6 | −31 | −2 |

IAmAVirus gained 174 points but stayed eighth. Greek Gift gained 255 and
increased its lead over us by 81 points. Mist gained 63 and moved up two places
while remaining on v2 in these endpoint snapshots. Instructors gained 37.
Duck lost 31, so the gap to Duck narrowed over these two weeks. Daily Elo moves
reflect the arena schedule as well as bot strength; they do not isolate a
version's causal effect.

## Where v35's points went

In the Oct 18–24 report window, v35's largest negative rating-point flows were
Duck (−363 over 268 games, score .32 vs .48 expected), Decent Chess Bot (−179
/ 280, .28 vs .36), Strongly Invisible (−139 / 278, .22 vs .28), and Instructors
(−84 / 264, .43 vs .47). Mist was positive relative to expectation: +82 / 284,
score .50 vs .47 expected. The overall 7-day score was .52 over 3,433 games;
that aggregate hides matchup failures. The 24-hour score was .52 over 442 games.

## Behavior signal, with a necessary distinction

Own-side taxonomy rates changed between Oct 11 and Oct 24: king moves 13.19→
14.40 per 100 moves, home-leaving king moves 2.39→3.58, king threats
2.61→3.78, hidden king threats 1.36→2.03, and walking into unseen attacks
3.08→2.82. These are team-level rates from separate recent windows, not
paired decision samples. They show that v35's recent play is more active on
both king movement and threats; they do not establish whether king moves are
forced or mistakes.

A separate Oct 24 three-day head-to-head slice reports that in 732 games
against teams above us, our side made 17.2 king moves per 100 moves versus
11.5 for opponents; home-leaving moves were 4.5 vs 3.2, king threats 3.0 vs
4.6, and hidden king threats 1.3 vs 2.4. All 510 losses in that slice ended by
king capture. This matchup-conditioned contrast is more actionable than a
league-wide style comparison, but it still needs decision-level replay analysis
to tell forced king defense from avoidable king exposure.

## Next diagnostic

For v35 losses to Duck, Decent Chess Bot, Strongly Invisible, and Instructors,
classify each king move by: whether it was immediately fatal; whether the
replay's actor-legal set had a non-king move avoiding immediate fatality; the
change in hidden king-attack support; whether the move gained useful vision or
created king pressure; and whether the alternative preserves an attack. This
separates an overactive king penalty from a genuine safety-choice defect. Use
held-out losses and wins, matched by opponent version and color. Do not install
a global king-move penalty from the aggregate rates.

## Reproduction

```sh
python3 astra-submissions/tools/arena_trend_report.py \
  --reports data/reports/daily \
  --output astra-submissions/analysis/standing-trend-20261024/arena-trend.json
```

## v35 hidden-arrival and prior ablations (Oct 25)

The submitted v35 binary was replayed on 16 early fatal choices with a
true-board immediate-safe legal alternative, four per opponent (Duck, Decent,
Strongly Invisible, Instructors). This is the earliest-by-ply sample selected
from 492 audited decisions, not a random holdout. The same 16 prefixes were
run with default settings, the static history table disabled while retaining
the fitted model, all learned move priors disabled, and model temperature 1.
Exact referee labels found immediate-fatal choices in 16/16, 14/16, 12/16,
and 14/16 respectively. The true board was present at the target in 14/16,
14/16, 15/16, and 16/16. The result suggests learned weighting can affect
both support and selection, but these loss-only cases cannot establish a
strength improvement; the choices did not receive opponent-reply rollouts.

A second slice isolates a recurring tactic: the opponent's last move delivered
the eventual attacker onto a square hidden both before and after that move.
The source audit contained 347 such cases among the 492, and 91 were at or
before ply 70. Four per opponent were selected, again earliest by ply. On
these 16 positions, default v35 chose an immediately fatal move in 16/16.
Temperature 1 reduced this to 14/16 and raised median true-board posterior
share from 0.090% to 0.165%, but the attacker remained low probability. A
king-guard margin of 0.005 reduced fatal choices to 13/16; 0.0001 reduced
them to 8/16. On 12 additional recorded nonfatal king-move controls (five
from wins, seven from losses, against three opponents), both default and
0.0001 selected immediately nonfatal moves; the stricter guard changed two
choices and neither became fatal. This is a tiny one-ply control, not a
candidate strength result. No counterfactual continuation branch was
included, so the low guard could still suppress useful escapes, attacks, or
material play. Keep the shipped default unchanged until broader controls and
referee continuations pass.

Artifacts: `v35-prior-ablation-16-*.json`,
`hidden-arrival-cases-ply70.json`, `v35-hidden-arrival-16-*.json`,
`v35-hidden-arrival-16-referee.json`, and
`../../tools/select_hidden_arrival_cases.py`. The replay tool now supports
`--no-history-table` so table ablations do not silently reload the archive's
table. The runtime source and submission ZIP are unchanged.
