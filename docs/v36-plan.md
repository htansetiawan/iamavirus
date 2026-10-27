# v36: one candidate, a fresh confirmation set, and a release decision

**Astra and Fable planning review · 26 October 2026 PDT / 27 October UTC.**

**Joint recommendation agreed by Astra and Fable; ready for Henry's review.** The recommendation is
to make **v35 plus the revised piece-risk rule, B2**, with the fallback correction
identified below, the sole candidate for arena v36. Both are implemented;
correctness checks, a final artifact freeze and full-game evidence remain.
No claim of an Elo gain or permission to upload is implied.

The objective is concrete: stop avoidable rook/minor losses against duck,
Instructors and the stronger teams while preserving v35's existing king/queen
protection. This is a release plan, not a new month-long research program.
At the dated snapshot we are ninth, Elo 1885; fifth place is 2054. Nothing measured
so far supports promising that v36 closes that 169-point gap.

[Exact decision contract and frozen artifacts](https://github.com/htansetiawan/iamavirus/tree/main/astra-submissions/analysis/v36-plan-20261026)
· [Fable's agreement and corrections](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/164-fable-v36-analysis-and-plan.md).

## Why this candidate

The October 26 10:13 UTC snapshot and preceding seven days put v35 at about
0.32 against duck v6, 0.42 against Instructors v4, 0.18 against Strongly Invisible
v37, and 0.04 against Greek Gift v25. Those are dated baseline figures, not current
ratings or forecasts. The daily report also shows comparable vision-gain rates
but more material sacrifices and fewer hidden king threats against the teams above
us. Descriptive rates do not identify a causal fix.

Our strongest direct evidence is now the B2 replay. Astra independently joined
the baseline and candidate by decision ID and compared only positions scored for
both. The uncertainty intervals resample games, since controls contain several
decisions from the same game.

| Existing set | Decisions / jointly scored | Mean paired change in CP loss, B2 minus v35 | Game-bootstrap 95% interval | Fatal choices, v35 → B2 |
| --- | --- | --- | --- | --- |
| Calibration losses | 796 / 732 | −42.5 cp | [−58.1, −26.6] | 1 → 1 |
| Later loss set | 818 / 728 | −39.6 cp | [−53.8, −26.1] | 0 → 0 |
| Ordinary win/draw controls | 400 / 355 | −1.2 cp | [−9.9, +7.1] | 0 → 0 |
| Ordinary pre-loss controls | 400 / 352 | −0.7 cp | [−7.9, +6.0] | 0 → 0 |

There are no newly introduced fatal cases in these four paired comparisons.
However, **B2 was revised after the first candidate failed on the 818-position
set. That set is now development/regression evidence, not untouched confirmation.**
CP loss is a perfect-information diagnostic, not a Fog of War win probability;
roughly 11% of the later set lacks a jointly available CP score. Complete games
and fresh data must decide whether the change helps.

[Reproducible independent analysis](https://github.com/htansetiawan/iamavirus/tree/main/astra-submissions/analysis/v36-plan-20261026)
· [Original failure and amendment](https://github.com/htansetiawan/iamavirus/blob/main/fable-submissions/analysis/v20-material-guard-20261027/oos-b1-fatal-cases.md)
· [Dated daily report](https://github.com/htansetiawan/iamavirus/blob/main/data/reports/daily/2026-10-26.md).

## Exactly what v36 would do

Let S35 be the moves surviving v35's existing king/queen rule. For each candidate
move, the new term estimates over retained possible boards whether an opponent's
next capture loses one of our rooks, bishops or knights for at least three pawns
net. King-loss and queen-loss events are excluded from the piece event to avoid
counting them twice.

Within **S35 only**, compare the existing combined risk plus **0.758 × piece
risk**, using the existing two weightings and margin/fallback rules. The search
then chooses among the remaining moves. The intended filter invariant is
**S36 ⊆ S35**: the new term cannot re-admit a move excluded by v35's risk rule.
That is an implementation invariant, not a guarantee against every hidden threat.
The source review found an important boundary: repetition exclusions can
combine with risk exclusions to empty the move list, where search restores all
moves; the final legality fallback also ignores risk exclusions. These paths
could bypass the promised protection. Fable implemented a separate correction:
relax repetition avoidance before safety exclusions, and have the legality
fallback respect exclusions when alternatives remain. Helper tests cover both
colors; the full guard-rule and release checks remain. The local filter proof
alone does not establish the property for the move sent to the referee.
Fable's [correction test receipt](https://github.com/htansetiawan/iamavirus/blob/main/fable-submissions/analysis/v20-material-guard-20261027/gate1-receipt-a71035e.md)
records the completed tests and the remaining release checks.

The coefficient is an observational estimate from loss cohorts, not a causal
valuation or a trained neural value function. Freeze it and the three-pawn
threshold. The evidence is a reason to test this rule, not to sweep its constants.

Freeze Stockfish at depth 1, the existing move/history models, 32 root draws,
belief caps, search and clocks. The tested knob must be embedded in the final
ZIP. The corrected candidate is **`a71035e`**, ZIP SHA-256 prefix
**`b2a2000c48da`**; Stockfish and history-table bytes match v35. It has not been
benched. Its predecessor `49f65e1d93e5` is superseded; three completed games are
retained as diagnostics. Finish the bounded guard-rule tests, freeze one final
artifact, and run every release gate on those bytes. **No bench is running now.**

## What the brainstorm rules out for this release

| Option | Evidence and practical decision |
| --- | --- |
| **B2 piece-risk rule** | Best measured decision improvement with ordinary controls holding; main v36 candidate. Remaining risk: conservative decisions may not convert into wins. |
| **Fused risk passes** | A plausible way to reduce the new guard's runtime cost. Only a conditional engineering rescue if timing blocks B2, with identical fixed-work risk values and exclusions; never silently swap bytes under a gate. |
| **More solver iterations** | A plausible subsequent diagnostic, not a second v36 candidate. A mixed root can be converged; measure stability instead of assuming low top-action probability means failure. Also verify the active solver branch: `MIST_ITERS` is only read in async mode. |
| **History-preserving belief / a new opponent prior** | Real structural opportunity, but additional histories compete for the memory/time used to retain distinct boards. Earlier likelihood gains did not reliably improve decisions. Not bundled into v36. |
| **Restricted action mixing** | The current argmax discards substantial strategy mass, but that mass may reflect incomplete solving. Must establish stability and test exploitability; adding randomness now would be a second behavior experiment. |
| **2-KLUSS and carried strategies** | Addresses opponent knowledge outside our private belief. Existing M4 implementation passed component tests but failed playing screens, including an early 0–4 set. Requires diagnosis and integration work, not merely enabling a switch. |
| **Deeper Stockfish** | Closed screen: seven complete matched blocks, 28 games, depth 1 and depth 3 each scored 8/14 against Misty. No evidence to include depth 3. |
| **New Deep RL/value model, in-process Stockfish, broad search rewrite** | Potentially larger changes, without a validated deployable replacement today. They cannot be prerequisites for this v36 decision. |

Mixed strategies, rapidly changing private information and common knowledge remain
architectural limitations, explicitly recorded in
[review 163](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/163-astra-randomization-and-changing-information.md).
Their importance does not establish which one caused the current losses. This
release does not claim to complete Obscuro or solve those limitations.

## Gates and stop rules

1. **Correctness and packaging.** Pin source, executable, effective environment,
   Stockfish and history table. Misty's local ZIP is only a wrapper, so its
   external Python environment and Stockfish are pinned too. Check B1's fatal
   counterexamples, disjoint king/queen/piece events, disabled-mode equivalence,
   and the repetition/legality fallback paths above. Review the whole turn's
   runtime, including belief and guards. These checks are release obligations,
   not all completed tests.
2. **Fresh decisions.** Use v35 games completed after October 26, 10:12 UTC and
   before October 27, 11:30 UTC against the original six opponents plus Crimson
   Fog. Exclude every old-suite game and duplicate trajectory. Freeze IDs before
   replaying; require at least 80 failure decisions and 50 in each ordinary
   control group. Failure CP loss must improve and repetition of the recorded
   losing move must fall by at least eight percentage points. Neither control
   may worsen by over 10 cp; piece-only vetoes must affect at most 8% of recorded
   control moves. **Zero introduced fatal decisions in every group.** At least
   80% of each group must have paired CP scores. Otherwise reject or report
   incomplete; do not tune on the new set.
3. **104 full games at 180+2.** Forty B2–v35 games; 32 B2–Misty and 32 v35–Misty,
   matched by seed and color, with a **12-hour hard cap** from the recorded
   launch. Target launch by October 27, 20:00 UTC / 1 pm PDT, after plan review
   and artifact freeze; the time alone does not authorize a launch. The stopped
   pre-correction run does not count toward this gate. Minimums: 18/40 against v35,
   at least 7/20 in each color, and no more than four points behind v35's score
   against Misty. Also require a positive combined score direction, defined in
   the contract, so two negative comparisons cannot pass. No attributable
   crash, illegal move or time forfeit; candidate final clocks must stay at least
   10 seconds and its median no more than 10 seconds below v35's. Account for
   every scheduled game, including failures and incomplete blocks.
4. **Decision.** All gates must pass before recommending an arena trial. These
   small benches screen for regressions and a promising direction; they do not
   establish an Elo gain. A changed binary cannot inherit an earlier binary's
   pass. No automatic extension or substitution of a different idea.
5. **Arena trial, if the gates pass.** Produce a validated ZIP and written prediction
   for Henry to submit. Record first clean piece-loss rates as well as wins, by
   opponent version and color. Compare with a frozen recent v35 reference on the
   same opponent/version/color mix. Report uncertainty and unsupported matchups.
   Any attributable crash, illegal move or time forfeit triggers a rollback
   recommendation; review results at 20, 100 and 200 games, with a human checkpoint
   at least every 24 hours. A higher raw Elo alone is not the success criterion.

If B2 fails for playing strength, **stop this candidate and bring the failure to
the committee**. Do not automatically launch another parameter sweep or combine
unvalidated modules. If it fails only on runtime, one equivalence-preserving
guard-fusion patch may be proposed within the same deadline, followed by its own
checks; it is not a license for a wider rewrite.

## Owners, deadlines and version identity

**Fable:** candidate implementation, controlled match runs, runtime accounting and
packaging; build the fresh set once. **Astra:** independent paired analysis,
fresh-data audit, source/ZIP review and the decision report. **Henry:** review this
plan and the eventual arena submission. No GPU is needed. The old local bench is
stopped; this planning exchange launches no replacement evaluation campaign.

| Deadline | Required result |
| --- | --- |
| October 27, 20:00 UTC / 1 pm PDT | First committee checkpoint: frozen contract, current bench status, fresh-set manifest and any blocker |
| October 28, 20:00 UTC / 1 pm PDT | Confirmation and capped local results, or explicit incomplete/reject report |
| October 29, 20:00 UTC / 1 pm PDT | Submit-ready ZIP with evidence, or a documented rejection; no silent extension |

The earlier `iamavirus-v36-kingguard0001.zip` remains immutable and is not this
candidate. Fable has marked its reservation withdrawn, retaining its hash and
history. Reserve the **next actual arena upload, expected to be v36**, for the
approved candidate only after checking the live version list. Internal engine
label **v20/B2** must not be confused with arena version 36. One authoritative
mapping must link the uploaded filename, full hash, source and effective settings.
