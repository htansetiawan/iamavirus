# Conditional confirmation plan — not launched

2 November 2026. This is the follow-up for experiment 234 **only if** its entire
16-game pilot reaches at least 10 points with no technical faults. The design
was drafted after observing six pilot results (4W–2L). It uses fresh seeds;
pilot outcomes will not be pooled into confirmation. No playing source,
candidate binary, model, guard, or initial acceptance criterion changed.

The fixed follow-up contains 80 full-clock first attempts at 180+2:

- 32 candidate games against exact v35, in 16 colour-swapped seed pairs.
- 32 against exact v37, also in 16 pairs.
- 16 Misty games: four matched blocks, each with candidate and exact v37 in
  both colours. Both arms use the same seeds and core pair within a block;
  arm order alternates. Misty does not guarantee that seeds control all its
  randomness. It is a local authentic engine, not verified arena bytes.

Release review requires each direct reference score >=50%, pooled direct
score >=60%, and the whole-pair, reference-stratified empirical-bootstrap
95% lower bound >50%. The interval uses the independently tested exact
convolution, rather than treating paired colours as independent games.
Candidate Misty points must be at least the matched v37 control on at least
three complete valid blocks. This small opponent check is not proof of
non-inferiority, and these local gates cannot establish arena Elo or success
against the actual Instructors, duck, or HYPOTHERMIA.

## Fault handling established before these games

Earlier confirmation had a Misty-only time forfeit in a baseline-control
game. Treating that as a playing win or as a candidate bug confounds the
comparison. Here a recorded Misty-only time/protocol failure invalidates its
entire four-game matched block for **both** arms. All first attempts remain
recorded, no game is replaced, no fault win contributes strength credit, and
fewer than three valid blocks makes the opponent panel inconclusive. This
block exclusion does not guarantee random missingness; it remains a limitation.

Any candidate, baseline, harness or integrity fault disqualifies the gate
and stops new jobs. An already-running game in the other lane may finish.
The whole batch has a 12-hour cap; each game has a 2,450-second wall cap.
The two timed lanes reuse cores 2–3 and 4–5 **after** the original pilot has
finished and all owned process groups are reconciled. No started game is
automatically repeated.

## Readiness and launch boundary

`design.json` fixes the 80 jobs, seeds, asset hashes, method and criteria.
It is not an execution plan yet. `run.py freeze` requires all 16 original
receipts, the qualifying score, verified replay hashes, and terminal original
lane receipts. `start` additionally requires a publication receipt confirming
the final plan on both Git mirrors. This prevents the publication/launch
ordering error recorded for the first pilot.

Four real protocol smokes passed (candidate, v37, v35 and Misty) on original
handle 40391, exit 0. Gate verification checks seven synthetic outcomes,
three bootstrap cases against exhaustive enumeration, the actual earlier
Misty-only forfeit, an actual candidate replay, and all colour/control/seed
blocks. These are harness checks, not new strength evidence. The inspected
Misty runtime dependencies still match all 99 existing pinned files.

No GPU, new ZIP, arena upload, or release number is used. A passing confirmation
earns a review of packaging, exact ZIP builds, runtime limits and arena trial
criteria. An upload remains the human's action. If the original pilot fails,
this prepared queue will remain unlaunched.
