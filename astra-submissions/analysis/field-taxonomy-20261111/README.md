# Field intelligence: refreshed behavior labels, unchanged arena bot

November 11, 2026 UTC. This is a local retrospective report, not a new
candidate or an untouched test set. Website publishing remains disabled.

The input is the complete reviewed **6,000-game** snapshot, covering
November 9, 10:57 a.m. through November 10, 8:51 p.m. Boston time. All
**453,622 moves / 459,622 frames** are included. The cohort contains
5,872 distinct full move sequences; repeated games remain actual arena
games, with no independence or training-split claim.

## What the fresh window shows

IAmAVirus v38 scored **184W–17D–144L** in 345 games, 55.8%, with
173 White and 172 Black seats. Selected matchup cells are below; these are
small descriptive samples, not version improvements or causal comparisons.

| Opponent | Played version | Our W–D–L | Our White / Black seats |
| --- | --- | --- | --- |
| duck | 11 | 2–4–12 | 9 / 9 |
| Greek Gift | 25 | 1–0–11 | 6 / 6 |
| Instructors | 4 | 8–1–7 | 8 / 8 |
| HYPOTHERMIA | 4 | 6–0–6 | 6 / 6 |
| HYPOTHERMIA | 10 | 5–0–3 | 4 / 4 |
| Knight Vision | 36 | 6–2–6 | 7 / 7 |
| Strongly Invisible | 41 | 3–0–7 | 5 / 5 |
| Crimson Fog | 4 | 4–0–10 | 7 / 7 |
| Decent Chess Bot | 7 | 2–0–6 | 4 / 4 |
| Mist Opportunities | 2 | 10–1–3 | 7 / 7 |

The saved leaderboard's top six are Greek Gift, Strongly Invisible, Knight
Vision, **Farsight**, Decent Chess Bot and Crimson Fog. Farsight is fourth;
duck is seventh. That cohort differs from older reports. Farsight played
versions 25–28 during this window; their aggregates are retained separately.
No current live ranking is inferred from this saved snapshot.

## Most final losses follow a material deficit

All 144 of our losses end with our king capturable. Immediately before
the final move, **125/144 (86.8%)** have us at least three material points
behind, 16 are within two points, and three have us at least three ahead.
Material uses pawn/minor/rook/queen values 1/3/5/9; the king is not priced.

Against duck, **10/12** losses already have that deficit; against Greek
Gift, **10/11**; against Instructors, **7/7**. These are terminal snapshots,
not a measurement of when the deficit began or what caused it. The earlier
[Duck loss-onset analysis](../../../chatroom/337-astra-duck-v11-material-loss-onset.md)
addresses timing on a different, overlapping cohort. This is not an
independent replication of that study.

| Geometry of our final move | Losses |
| --- | ---: |
| King moves into attack; its old square was not attacked | 55 |
| King moves while already attacked, but remains capturable | 40 |
| Another piece moves and an existing king attack remains | 47 |
| Another piece moves and opens a previously absent king attack | 2 |
| Total | 144 |

In **133/144**, every final attacker was hidden in the view supplied before
our move. Visibility afterward is a different question. Hidden does not mean
never previously observed, and visible does not establish what the bot's
belief assigned to the attack. No search replay or belief instrumentation
was run here. We also did not enumerate safe alternatives, so this table
does not establish that each final position could be saved.

The practical lesson is to retain the earlier exchange and material history
when explaining a loss. A final king-move penalty alone does not address
the demonstrated earlier deficits; its previous failed experiments remain
closed. The table does not identify a new winning policy.

## Existing behavior tags do not themselves rank strategic skill

The following are counts per **100 moves**, pooled over each version's
own schedule and both colors. They are not opponent-adjusted estimates.
Exact raw counts, color denominators and opponent cells remain in JSON.

| Team/version | Games | Moves | Captures from hidden origins | Threats with at least one hidden attacker | King moves |
| --- | ---: | ---: | ---: | ---: | ---: |
| IAmAVirus v38 | 345 | 15,292 | 8.32 | 2.09 | 14.19 |
| duck v11 | 371 | 16,619 | 9.02 | 1.88 | 13.65 |
| Greek Gift v25 | 234 | 10,907 | 8.90 | 2.50 | 11.71 |
| Instructors v4 | 398 | 18,137 | 9.25 | 1.86 | 13.32 |
| HYPOTHERMIA v4 | 230 | 10,644 | 8.70 | 1.62 | 14.86 |
| HYPOTHERMIA v10 | 104 | 4,798 | 8.34 | 1.19 | 15.49 |
| Strongly Invisible v41 | 290 | 14,042 | 8.72 | 2.02 | 14.11 |
| Knight Vision v36 | 341 | 14,903 | 9.43 | 2.29 | 11.21 |
| Farsight v28 | 154 | 6,678 | 9.12 | 3.34 | 11.67 |
| Decent Chess Bot v7 | 310 | 14,093 | 8.87 | 1.94 | 12.47 |
| Crimson Fog v4 | 328 | 12,681 | 10.35 | 2.42 | 12.92 |

We do create hidden threats; their raw frequency is not uniformly below
stronger opponents'. That does not establish equal quality, timing or
conversion. Game length, opponent mix, material imbalance and later losing
positions can all change these rates. Increasing a tag count is not itself
a justified training objective.

Definitions matter: a hidden-attacker threat can also have a visible
attacker. King moves include castling. The queen-exposure tag uses the
post-move view and is not a queen-loss rate. The legacy `king_capture` tag
is outside the 19 core report metrics; this EP-only correction does not
repair its inferred terminal semantics. Results come from replay metadata.

## The reporting correction is now quantified

The tested isolated `astra-ep-v1` identifies **352 en-passant captures in
345 games** that v0 labelled quiet. A full-history board independently
checks every capture, victim square and capture-chain classification.
All 5,655 games without en passant have identical v0/v1 output apart from
the version field. In this cohort, only those 352 move-label records change.

| Count changed by the EP correction | Delta |
| --- | ---: |
| Capture | +352 |
| Quiet | −352 |
| Victim arrived on the opponent's preceding move | +352 |
| Capturer hidden before the capture | +218 |
| Fog route | +207 |
| Capture chain of at least three moves | +42 |
| Total fog-route depth | +375 |

This is a label correction, not a change in game outcomes or engine rules.
Both versions' counts are saved. Historical reports are unchanged; a future
trend comparison must use consistent labeler versions on both windows.

## Verification and what remains unchanged

The original refresh completed once, exit 0, in **78.86 seconds** on one
reserved core, below its 1,800-second cap. An independent reduction checks
all game identities, per-move tag counts, the 116 team/version/color groups,
outcomes, denominators and EP deltas. It also checks material and recorded
input visibility directly against raw frames for all 144 of our terminal
losses. Source/artifact hashes match; the core lease is released.

The shared labeler, old reports and deployed v38 are unchanged. Taxonomy
diagnoses behavior; it does not automatically fit belief coefficients,
rebuild the empirical history file or update guards. This separate local
report also does not repair the external archive or daily automation.
No new model, training split, GPU run, candidate, game, ZIP, commit, push
or deployment is part of this work.

[Frozen plan](plan.json) · [Aggregates](result.json) ·
[Independent review](review.json) · [Execution](execution.json) ·
[Runner](../../tools/field_taxonomy_report.py).

Rich per-game labels, exact source hashes, terminal cases and full opponent
cells remain under `data/astra-spool/field-taxonomy-20261111/`. Many fields
use hindsight; they must not become actor inputs without an information
boundary review.
