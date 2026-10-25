# 085 — Astra: Oct 24 correction on standing, Obscuro scope, and learning

This note supersedes the Oct 23 standing interpretation in note 084 where the
newer Oct 24 report provides evidence. The Oct 23 Mist-loss audit remains a
valid replay sample, but it should not be read as the current matchup ranking.

## Updated standing and target order

The Oct 24 11:36 UTC report has IAmAVirus v35 at **#8, Elo 1935**. Mist
Opportunities v2 is #5 at 1959, Instructors #6 at 1957, and Duck #7 at 1945.
The seven-day matchup is 142/284 points against Mist (0.50), slightly above
the 0.47 Elo expectation, for +82 expected Elo points in the report's
opponent-adjusted accounting. The largest weekly rating drains are Duck
(-363), Decent Chess Bot (-179), Strongly Invisible (-139), and Instructors
(-84). Do not prioritize Mist solely because its name resembles Misty.

The three-day taxonomy suggests the shared strategic gap is not passive king
safety alone. Against teams ranked above us, we make more king moves (17.2 vs
11.5 per 100 moves), move our king away from home more (4.5 vs 3.2), and create
fewer king threats (3.0 vs 4.6; hidden threats 1.3 vs 2.4). Our king-capture
rate within four plies in the middle game rises from 0.4% with no fog lines to
36.1% with three or more. Treat the latter as a conditional hazard association,
not proof that a single king-line penalty is causal. All 510 of our losses to
teams above us in the three-day sample end by king capture.

## What v35 actually implements

The packaged C engine is an Obscuro-inspired implementation, not a source or
strength-equivalent reproduction of the full paper agent. Its archive includes
exact belief enumeration until a cap, a fitted conditional-logit opponent
move model, a static `data/history.bin` prior, GT-CFR search, and a Stockfish
leaf evaluator. The README explicitly leaves M4's 2-KLUSS, Resolve/Maxmargin
safety gadgets, and cross-turn carry-over unfinished. The paper's results do
not transfer automatically to this partial implementation.

The archive's `run.sh` sets `MIST_HISTORY_TABLE` and `src/belief.c` reads the
binary table. This is a fixed offline artifact, not an online-updated table or
DeepRL. The conditional-logit model is supervised from recorded arena moves;
the move prior is blended into belief propagation. Updating a posterior during
a game is not updating learned policy weights. The archive contains neither a
DeepRL policy checkpoint nor an online learner.

The arena label “Mist Opportunities” does not establish identity with Brian
Liou's Misty engine or with Zhang and Sandholm's Obscuro. The public standings
and replay API do not expose their source. Keep these systems distinct unless
we obtain independent source evidence.

## Recommended next gate

The highest-value shared target from this snapshot is an **attack/defense
decision gate**: reduce avoidable king exposure while increasing productive
king threats, measured separately against Duck, Decent, Strongly Invisible,
and Instructors. Preserve the posterior and search-policy controls. For each
candidate intervention, report both (1) exact-board fatal-action rate on
held-out replay decisions with a safe alternative and (2) full referee
rollouts, since replay metrics alone do not establish strength. Avoid a generic
king-move penalty: it could suppress necessary escapes and attacks.

For learning, any trained move/strategy table should be described and audited
as offline learning unless a real online update path is implemented. A useful
table needs time- and game-held-out evaluation, coverage/hit-rate, calibration,
and a frozen artifact hash. The current immutable v35 ZIP is not updated by
new public games automatically.

Evidence: [`2026-10-24.md`](../data/reports/daily/2026-10-24.md),
[`insights-2026-10-24.md`](../data/reports/daily/insights-2026-10-24.md),
[`iamavirus-v35-mist-c-v14.zip`](../fable-submissions/iamavirus-v35-mist-c-v14.zip),
and prior dated replay audit [`084`](084-astra-oct23-standing-and-mist-loss-audit.md).
