# Current terminal motifs: look before the final king move

**In this selected strong-opponent cohort, nine of our thirteen losses were
already forced at the last decision; eleven had a material deficit of at least
three points before that move.** A final-move veto cannot save those nine
fixed positions. This supports examining earlier decisions, not reviving a
blanket king-walk penalty. It does not identify which earlier choice caused
the loss or prove that a different policy would win.

All300sealed307games,600team-game seats,25,906course-checked frames;12:01–16:10UTC
on10November. These exact trajectories are already excluded from running326.
All outcomes retained, played versions separate; this selected cohort is not
the full arena schedule or a causal skill ranking. Our9W–13L here must not be
compared directly with our full v38record.

| Team / played version | Games | W–D–L | King losses | No one-ply escape | Down3+ before final move |
| --- | ---: | --- | ---: | ---: | ---: |
| IAmAVirus v38 | 22 | 9–0–13 | 13 | 9 | 11 |
| Instructors v4 | 70 | 39–0–31 | 31 | 11 | 26 |
| duck v11 | 39 | 25–4–10 | 10 | 1 | 9 |
| HYPOTHERMIA v4 | 26 | 12–2–12 | 12 | 2 | 11 |
| HYPOTHERMIA v10 | 8 | 5–1–2 | 2 | 2 | 0 |
| Greek Gift v25 | 30 | 29–0–1 | 1 | 0 | 1 |
| Crimson Fog v4 | 39 | 26–0–13 | 13 | 0 | 9 |
| Farsight v28 | 20 | 11–0–9 | 9 | 4 | 8 |

The twelve color-mirrored geometry fixtures pass. Original87760runs once for
11.32seconds on cores4–5 and exits0, releasing its lease. All4,873terminal
candidate actions have C/course one-ply survival agreement. The independent
310-pin/600-seat/count/geometry/material/opportunity audit passes. This is
offline hindsight data, not a benchmark or a learned model.

## What the opportunity denominators actually say

| Target / version | Optional hidden king baits taken / offered | Distinct games with offers | Hidden checks missed / avoidable checks |
| --- | ---: | ---: | ---: |
| Instructors v4 | 3 / 50 | 21 | 5 / 51 |
| duck v11 | 1 / 20 | 7 | 5 / 24 |
| HYPOTHERMIA v4 | 1 / 22 | 6 | 7 / 19 |
| HYPOTHERMIA v10 | 0 / 2 | 2 | 0 / 1 |
| Greek Gift v25 | 0 / 4 | 2 | 0 / 4 |
| Crimson Fog v4 | 7 / 23 | 15 | 0 / 11 |
| IAmAVirus v38 | 1 / 7 | 4 | 1 / 18 |

Offers can repeat within one game; these are descriptive opportunities, not
independent Bernoulli trials or causal acceptance probabilities. Most victims
in the final-loss sample were already materially behind. HYPv10has only eight
games; do not pool it with v4or infer immunity. Greek Gift has only one loss
here, fourteen points down before its last king move: no convincing cheap
opening exploit is established by this sample.

## A concrete transferable pattern

In [xvrzyogn](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xvrzyogn),
TA Baseline S v3beats Instructors v4with a stacked-rook trap:
`...Ra8-e8`, `Rh1-h3`, `...Re4xe2`, `Ke1xe2`. The rook on e8is hidden and
covers the offered rook on e2. Instructors was **four material points ahead**
before accepting and had **two safe alternatives**. This is evidence that a
specific hidden-guard trap can overturn a material deficit; it is one observed
line, not a tested book or a guarantee that the opponent repeats it.

The role pattern is **hidden backing piece → checking offer → optional king
capture into the hidden guard**. It does not require a player name. Instructors
took3/8optional rook offers in seven games, but0/8queen offers in six games
in this cohort. That does not justify throwing queens at the same opponent.

Guards are not always sliders. Duck's one optional bait loss here was `Kg4xf3`
taking a knight guarded by an unseen king on e2([5pvc0t0g](https://www.mit.edu/~6.7980/fow/?tab=arena&game=5pvc0t0g));
Duck was already eight points down. Crimson Fog took a rook on g7guarded by
a hidden knight on f5while only two points down ([ix7rzd0o](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ix7rzd0o)).
A slider-only threat vocabulary misses those configurations.

## How this data can be used

[pattern-summary.json](pattern-summary.json) groups terminal events by move
kind, offered piece, guard types, prior attack, current visibility and existence
of a one-ply escape. No team identity enters the signature. These are oracle
facets for research fixtures and possible future auxiliary targets; they are
**not learned skills**, a runtime policy or proof the opponent forgot a piece.
Current-view hidden does not mean unknown after observation history.

The existing011SQLite actor-only index already implements indexed retrieval
and a bounded heap; do not call retrieval new or put these privileged labels
into its actor inputs. A future motif retriever needs a separate label/feature
boundary and whole-game held-out tests. No acceptance model, coefficient or
strategy selector is fitted here.

326remains the main pending gate: corrected teacher, unchanged weights, new
future games. This label refresh does not change that test, the live engine,
any guard or any model. It does not automatically reopen old hidden-threat,
value, capture-pricing or response-projection experiments.

[Aggregate results](result.json) · [independent review](independent-review.json) ·
[plan](plan.json) · [source](../../experiments/terminal-motifs-20261110/run.py).
Rich per-case labels remain local; code, aggregates, hashes and this explanation
are the public review materials.
