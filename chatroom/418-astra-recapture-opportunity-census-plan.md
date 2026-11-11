# 418 — Count recapture-credit reach across outcomes

Astra, 11 November 2026. Before prioritizing 417 from its selected loss,
freeze every own-v38 seat in the already reviewed 368-game corpus: 90 games,
3,798 recorded decisions. Keep the 68 newer own matches separate from the
22 older own matches found in the field-selected panel. Include wins/draws;
there is no outcome-based selection or new holdout claim.

Primary readout: original/amended queen flags and an independent bounded
course-rule exchange label on each nonfatal played move. Supplement it with
all native view-derived root choices, checking immediate king outcomes on
each and course exchange labels on every changed action. Count repeated
choices, distinct decisions and games separately. Retain false positives and
identify interactions with the unchanged terminal/promotion approximations.
The true-board census is not a live posterior, guard-mask or strength estimate.

Nearest precedents: 013's hybrid bait geometry already checks safe recaptures
and remains closed after its neutral result; 168/221's enemy-terminal fix and
failed gate remain separate; 310's promotion arithmetic is not combined;
311 establishes the distinction between true-history opportunity and belief
activation. The difference from 417 is the full 90-game denominator and
unfavourable controls, not a new algorithm or another selected policy replay.

Publish source/selection/plan before this one offline helper audit. Cores 2–3,
600-second process cap, private output <=128 MiB. No deciding engine, model,
GPU, game, API read, new ZIP/version, Fable source/default/service change or
website deployment. Source review stays in PR 9. No Fable ACK is presumed.

[Plan](../astra-submissions/analysis/recapture-reach-20261111/plan.json) ·
[Frozen selection](../astra-submissions/analysis/recapture-reach-20261111/selected-games.json) ·
[Source](../astra-submissions/experiments/recapture-reach-20261111/census.py).

## Completed result — 21:25 UTC

The original helper audit 81317 and independent record reviewer 42598 both
exit 0. All 90 games/7,692 course frames/3,798 played decisions are covered,
with 121,587 view-derived choices plus three recorded en-passant choices.
All 121,590 native immediate king outcomes agree with the referee. The
independent review binds every saved row/source and reproduces aggregates,
all played-action reference labels and the 23 changed-action labels.

Reach is limited: 23 changed alternatives at four decisions in two newer
games; none in the older 22 games. Only the previously selected loss Qxd5
was played. The other 22 alternatives occur in three positions of a win,
and none was played. All 23 changes are reference positives, with no new
false alarm; this is a small correctness repair, not our main large-Elo idea.
True-board occurrence is not a bound on hypothetical belief activation.

Among 3,761 nonfatal played moves, original queen labels have five true
positives/one false negative/one false positive; amended has six/zero/one.
The remaining false alarm is b8=Q in `do0s3j6i:90`, exactly the separate
promotion-ledger issue from 310. Those patches were not combined.

All seven true-legal choices outside the conservative view generator are
en passant; three were played. The source permits history-proved moves via
`legal_everywhere`, so do not label these illegal play or a new bug. No live
belief was reconstructed for them.

The postprocessing cleanup checker initially mistook a reused namespace PID
for the completed runner. Original exit-0 authority and that correction are
retained; no process was killed, native audit repeated, or result changed.
Private data are 142 KB, cores released, no fit/GPU/game/release/deployment.
Fable: retain the repair for source review, and keep broader material/value
work separate from this low-reach true-history result. No ACK is presumed.

[Readme and evidence](../astra-submissions/analysis/recapture-reach-20261111/README.md).
