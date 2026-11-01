# V37 fixed-tree solver audit — 1 November 2026

**More final solver iterations did not repair the measured failures.** Do not
promote a settling-only candidate from this work. The useful follow-up is two
earlier material decisions against duck and HYPOTHERMIA, described below.

## What was tested

The exact v37 archive (`41e02e280b61…`) was extracted into an isolated build.
After its original move choice, instrumentation records the current root
strategy and counterfactual action values, then performs 20, 200 and 1,000
additional PCFR iterations. Sampled boards, chance weights, tree structure,
information sets and leaf values are unchanged. Their structural hash is
checked at every checkpoint. The original move is still emitted.

Search is capped at 2.5 seconds, seed 11012026, pinned to reserved cores 0–1.
Extra diagnostic solver work has a three-second loop budget; all 37 decisions
reached 1,000 iterations. This is **extra computation after the decision**,
not a same-clock playing policy or an arena-strength test.
"Original" means the choice before extra iterations in this diagnostic run,
not necessarily the historical arena move. The 2.5-second cap is shorter than
some arena decisions, and prefix belief thinning depends on wall-clock cost.

The first manifest was committed in `00efd50`, before results: 22 late
decisions from 11 v37 games, stratified by opponent and game outcome. The
observed coverage problem led to one separately frozen supplement in
`7675ea6`: 11 opening controls at ply 18/19 and four first material-loss
decisions at ply 8–60, selected while our material deficit was no worse than
three points. These 15 cases use the **same games**, not independent validation.
No model weights, guards or search parameters were tuned between panels.

Seven opponents are represented: Crimson Fog, Decent Chess Bot, HYPOTHERMIA,
Knight Vision, Mist Opportunities, Strongly Invisible and duck. The cached
Instructors v37 games were excluded because the preceding temporal/context
experiments had already used them. No claim of coverage against Greek Gift.

| Diagnostic | Late: original → settled | Earlier: original → settled |
|---|---:|---:|
| Decisions | 22 | 15 |
| Highest-probability move changes | 2 | 0 |
| Immediate king-loss choices | 6 → 6 | 0 → 0 |
| One-exchange material loss ≥2 | 0 → 0 | 2 → 2 |
| Queen exchange loss ≥4 | 0 → 0 | 0 → 0 |
| Errors / illegal moves | 0 / 0 | 0 / 0 |
| Median root strategy total variation | 0.00044 | 0.00543 |
| Median root one-deviation gain | 5.07e-7 → 7.90e-7 | 0.00050 → 0 |

Root one-deviation gain is `max_a Q(a) - sum_a pi(a) Q(a)` against the
recorded continuation strategies. It is not full-game exploitability. A stable
solver can solve an inaccurate or shallow game. The study does not establish
that extra computation, deeper trees or a different solver can never help.

## Where the measured failures are

Four of the six late king losses have **no immediate escape on the true
board**. In `j2m5dxhp:97`, both immediately safe alternatives are absent from
the search root, and we are already down 19 material points. In
`ypq192zu:103`, one safe alternative remains, but we have a bare king against
17 points; its searched value differs from the fatal choice by only 0.000125.
Immediate survival is not proof of a winning continuation. These positions
should not be used to reward a model merely for delaying terminal loss.

The earlier panel identifies two more actionable investigations:

| Position | Original choice and true tactical consequence | What search represented |
|---|---|---|
| duck, `tjds234d:54`, material −2 | `Rb1xb7`, then hidden `Nd6xb7`: net loss 4. `Rb3` has no loss in the same limited probe. | Knight on d6 has 9.375% sampled mass. Root gives `Rxb7` probability 1; additional iterations do not change it. |
| HYPOTHERMIA, `92px495s:26`, material −2 | `Qd1xd5`, hidden `Be6xd5`, `Bf3xd5`: net loss 3. Immediate `Bf3xd5` has no loss in the probe. | The true board and bishop on e6 carry 31.25% sampled mass. Root mixes `Qxd5` 54.8% / `Bxd5` 45.2%, then purification always selects the queen. |

The queen example is **below the existing four-point queen-loss threshold**;
it is not evidence that the current guard missed an event its definition
promises to prevent. Lowering that threshold is not justified by one case.
The rook example is outside king/queen protection. Sample attacker mass is
not the full belief probability; zero exact-board mass does not establish
that the true board was absent from the larger belief.

These observations separate posterior/action-risk questions from solver
convergence. Before a fix, measure the relevant reply and exchange in each
sampled world and compare its leaf/search value. A limited full-board probe
does not prove that `Rb3` or `Bxd5` wins or is better under the bot's information.

## Root randomization: an explicit hypothesis, not a release

A post-hoc calculation evaluates the **already recorded** root mixture on
the true board. It does not rerun search or fit a temperature. Expected
immediate king-loss counts on the 22 late cases are 5.534 versus the six
argmax choices, with the reduction in the already badly lost endgame. In the
earlier panel both give zero king losses; expected material-loss events are
1.548 versus two, driven by the HYPOTHERMIA queen/bishop choice. The duck
decision is pure and unchanged. These are selected-case tactical expectations,
not match scores, independent evidence or a claim that a mixed policy wins.

This narrowly motivates checking actual v37 root-mixture play in a separate
same-clock experiment, subject to reviewing the earlier M4 mixed-policy
negative results. It does not justify another global risk multiplier, a
larger final iteration count, or automatic removal of guards.

## Evidence and reproduction

- `plan.json`, `early/plan.json`: immutable inputs, case selection, archive and
  instrumented binary hashes. Exact permitted protocol inputs are retained.
- `receipts.jsonl`, `early/receipts.jsonl`: all 37 first process exits and
  output hashes, including stdout/stderr and every strategy checkpoint.
- `summary.json`, `early/summary.json`, `labelled.json`: results and offline
  labels. `material-focus.json` and `mixture-diagnostic.json` retain follow-ups.
- `referee-audit.json`: all 987 frames and 31,671 legal-move immediate-loss
  labels in these 11 games agree with the independent course referee.
- Implementation: `astra-submissions/experiments/frozen-tree-20261101/`.
  The exact toy covers unequal world weights, zero-probability alternatives,
  opponent signs, initial leaf values, tree immutability and solver behavior.
  Optimized and ASan/UBSan runs pass. LeakSanitizer initially could not run
  inside the traced sandbox; the unchanged tests pass outside it with leak
  detection enabled. This is an environment failure, not a suppressed check.

The engine subprocess receives only its own observations, clocks and prior
own moves. Redacting true boards, opponent observations and hidden moves
leaves its inputs identical. Full-board labels are joined after exit. No
recorded opponent continuation is used after a counterfactual move.

Build and test with `build.py` and `test_audit.py`. `run.py` accepts `freeze`,
`run` and `summarize`; its output directory is pinned in source. Make a new
dated experiment/output path for a new run. Exclusive files prevent
overwriting first receipts. `early_panel.py` preserves the separate follow-up.
The reference validation is `verify_replays.py`; descriptive follow-ups are
`mixture_diagnostic.py` and `focus_material.py`.

No GPU use, new ZIP, arena upload or Fable core-source edit. The campaign
remains open; this is a completed diagnostic and a narrower next hypothesis.
