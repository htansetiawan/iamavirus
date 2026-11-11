# Recapture correction: valid, with limited true-history reach

The broader audit supports 417's correctness finding but does **not** make it
the main strength-improvement track. On every own-v38 seat in the existing
368-game reviewed corpus, the amendment changes 23 view-derived alternatives
at four decisions in two games. Only one changed action was actually played:
the previously identified Qxd5 in `ewav2dzr`. The other 22 alternatives occur
at three decisions in a game we won (`2cnre7yw`); none was played.

| Frozen cohort | Games, W/D/L | Recorded decisions | View-derived choices | Changed choices / decisions / games | Changed played moves |
|---|---:|---:|---:|---:|---:|
| Newer own-match window | 68, 43/1/24 | 2,852 | 89,287 | 23 / 4 / 2 | 1 |
| Older field-selected own seats | 22, 9/0/13 | 946 | 32,300 | 0 / 0 / 0 | 0 |
| Combined, descriptive only | 90, 52/1/37 | 3,798 | 121,587 | 23 / 4 / 2 | 1 |

The changed played move is 0.0351% of the newer cohort's decisions, or
0.0263% overall. These reused, time/field-selected games are not a random
arena sample or a new holdout. True-board occurrence does not bound how often
the guard changes on hypothetical boards, its effect on decisions, saved games
or Elo. Keep the repair for source review; do not package a successor, reopen
the old guard sweeps or claim a large Elo gain from these counts.

## Correctness controls

The native original/amended helper is checked on 121,590 actions: all 121,587
view-derived alternatives plus three recorded moves outside that conservative
generator. All immediate king outcomes agree with the course referee, and
the amended queen indicator never falls below the original. Every one of
the 23 changed alternatives has bounded course-reference queen-loss label 1;
none introduces a false alarm in this panel. Their capture children have no
opponent-king-terminal or promotion interaction.

There are 37 immediately king-losing recorded moves, excluded from the queen
exchange comparison as the helper intends. Among the other 3,761 played moves,
the original has five true positives, one missed queen loss and one false
positive. The amendment has six true positives, no missed queen loss in this
small panel, and the same one false positive.

That unchanged false positive is `do0s3j6i`, White frame 90, b8=Q. A promoting
pawn gains eight material points; after ...Rxb8 Nxb8 the bounded reference
is a four-point gain, whereas both versions flag it. This is 310's separate
promotion-ledger omission, not a regression from safe-recapture checking.
Do not describe the entire queen guard as exact or silently combine patches.
The reference also does not certify continuation beyond counterfactual draws.

## Legality and audit scope

The true board permits seven additional en-passant choices not returned by
the conservative single-view generator. Three were actually played and are
included in the primary comparison. They are legal according to the course
rules; this is not evidence of illegal arena play. Archived GT-CFR generates
root moves on a sampled consistent board, and the front end can accept a move
outside `view_moves` when `legal_everywhere` proves it in an uncapped belief.
The census does not reconstruct those live beliefs or certify which branch
ran in each game. Its supplemental denominator is the view-derived action
set, not every history-inferred search action.

The original audit (session 81317) exited 0; the independent saved-record review
(42598) exited 0. All 90 source hashes, 7,692 course frames, 3,798 primary
records, 23 changed-action labels, denominators and cohort aggregates verify.
The independent reviewer rechecks all played actions and changed exchange
references without invoking the native helper again. Private output is
141,810 bytes. No deciding engine, model fit, GPU, match, ZIP, version,
production source/default/service or website change occurred.

One postprocessing cleanup assertion compared a numeric PID across execution
namespaces and collided with the checker itself. It was not evidence that
the completed session remained live. The correction retains the original
exit-0 receipt and the source's lack of child-process launches; no process
was killed or audit repeated. Cores 2–3 are released.

[Frozen plan](plan.json) · [selected games](selected-games.json) ·
[result](result.json) · [independent review](record-review.json) ·
[terminal receipt](terminal.json) · [cleanup correction](cleanup-check-correction.json) ·
[census source](../../experiments/recapture-reach-20261111/census.py) ·
[review source](../../experiments/recapture-reach-20261111/review.py).
