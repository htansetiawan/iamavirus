# Conditional-value expansion: passes replay screen, full-game test next

2 November 2026. Isolated search change from exact v37. Its expansion policy
uses conditional action values and visit variance where the baseline uses
current strategy probability plus a visit bonus. Belief, guards, leaf values,
solver and final root selector remain unchanged. No GPU, trained weights or
new release. Source/methods and the predeclared gates are in
`../../experiments/value-expansion-20261102/README.md`.

## Completed fixed-input comparison

51 decisions from 25 existing development games against Instructors, duck and
HYPOTHERMIA. Every case reconstructs one belief and guard mask, then searches
both arms for 2.5 seconds with the same sampled boards, weights and exclusions.
Order alternates. True-board labels are computed after exit. This avoids
attributing differing clock-driven belief thinning to the expansion policy.

| Diagnostic | Original expansion | Conditional-value expansion |
|---|---:|---:|
| Immediate king loss | 12 | 11 |
| Bounded material loss >=2 | 4 | 4 |
| Bounded queen exchange loss >=4 | 0 | 0 |

12 choices change; one immediate loss is repaired, none newly appears. The
changed fatal case is `i3xv2i71`, frame79: Kh6 becomes Kh5. This single repair
is not statistical evidence of greater strength. Zero queen-loss cases do not
validate queen safety. The reused selected panel has no population-rate or
Elo interpretation.

All51 pairs exercised the new rule. All moves are legal; beliefs, sample
weights, action identities and exclusions match within every pair. Independent
course-referee checks agree on2,193 frames,63 distinct choices and5,749 bounded
transitions. Native source/plan dependencies verify. Original run handle16729
and review38649 exited0; no retry. The run took337.80seconds.

Median node ratio(candidate/control) is0.9958, iteration ratio0.9863. The new
value passes total2.127seconds across109.497seconds of enabled searches,
including diagnostic export overhead in the latter. This shows modest cost
on this panel, not a general speed or strength result.

## Correctness and provenance

The independent value oracle checks640 profiles, including751 zero-reach
infosets,128 rejected invalid-recall merges and257 actions; maximum error is
2.23e-16. Observing values preserves1,200 solver iterations byte-for-byte.
Native selection fixtures verify the changed branch, unchanged support
sampling, fallbacks and non-explorer. Address/undefined/leak sanitizers pass,
including2,000 growing-tree observations. Eight protocol/rules smoke checks
cover both colours and both scheduler paths. A separate paired-export smoke
checks sample/mask equality and root values. This evidence establishes
correctness of the tested implementation, not an equilibrium guarantee.

Exact v37 binary: `14ac30b34999a6a667e4dcdfb1b4606b184dbacbdc2fcfdf7f6b257513543fcd`.
Playing candidate: `aacd1be050159d0b8bf79168a6ffeb9598a47b2e27aed559d83a8e23e86950fd`.
Diagnostic build has separate bytes and is not used for full games.
Pre-run publication: `e0819ca6015f9b465965b1222621971a91836f86`.
Plan SHA: `64d297bce82956bf8b57bf8beb0204b45da337a9eacd34ba2a9f8c1319fc9a61`.
Original extraction/build failures and pre-command-alignment hashes remain
recorded. Raw compiler logs and the valid unified diff are losslessly gzipped
with their original hashes in `raw-text-archives.json`.

## Authorized next stage

The frozen fail-fast screen passes and its independent review is complete.
The separate queue is16 games, eight colour-swapped pairs versus exact v37 at
180+2. Its source is `full_games.py`; it reuses the existing turn-isolated
referee controller. Candidate enabled, baseline disabled, no model updates,
no diagnostic teacher export. Two exclusive lanes, cores2–3 and4–5, four-hour
batch cap. Every first attempt is retained; a started game is not repeated.

At least10/16 points with no technical faults/forfeits is needed to justify a
separate opponent gate. This small pilot cannot earn release by itself. No
Misty phase, new ZIP or archive version is reserved by this plan. See
`full-games/plan.json` for exact hashes, seeds and jobs.
