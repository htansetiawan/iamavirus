# Current-view action backoff probe

## Question

Can an actor-visible board observation retrieve useful actions after v35's
exact history key stops matching? This offline probe trains a frequency table
on the game-disjoint training IDs and checks it on the same 12,923 held-out
replays as the exact-history audit. Black observations are rank-reflected and
piece colors swapped; Black actions are rank-reflected into White-relative
coordinates. It compares exact history, current-view-only retrieval, and
exact-history-first with current-view fallback.

## Aggregate results

There are 991,287 held-out decisions. At each gate, an entry is eligible only
when its table contains at least that many training actions.

| Retrieval | Gate | Eligible decisions | Actual action present | Most frequent action agrees | Actual in top 4 |
|---|---:|---:|---:|---:|---:|
| Exact history | 3 | 13.47% | 95.56% | 54.71% | 84.47% |
| Current view | 10 | 18.02% | 97.70% | 53.16% | 85.54% |
| Exact then view fallback | 10 | 18.44% | 95.07% | 54.49% | 84.63% |

On the Oct 24 top-six team subset (464,128 decisions), exact history is active
on 12.76%; current-view at gate 10 is active on 16.19%, and exact-then-view
fallback on 16.73%. For exact history the top-1/top-4 replay-action agreement
is 60.34%/89.90%; for the fallback it is 58.71%/88.99%. Thus the fallback
covers more positions, but slightly weakens action ranking on this subset. It
is not an unambiguous improvement.

Opponent subsets vary. At current-view gate 10, Mist Opportunities has 18.9%
coverage, 99.0% action support, and 67.4% top-1 agreement, versus exact-history
13.5%, 97.8%, and 68.0%. Duck has 19.4%, 97.4%, and 54.9%, versus 13.3%,
96.7%, and 56.3%. Instructors has 15.6%, 96.8%, and 43.0%, versus 11.6%,
95.7%, and 50.6%. So the additional examples do not yield consistently
better top-1 actions against opponents we most need to beat.

The exact cache is concentrated in plies 0–9 (83.8% eligible) and nearly
absent after ply 20 (1.04% at plies 20–39; 19 eligible positions at ply 40+).
The view fallback extends coverage but remains sparse in later positions; for
Mist it activates on 4.7% of plies 20–39 and 2.1% after ply 40 at gate 10.

## Interpretation and limits

This supports the exact-history table as an opening specialist and shows that
a coarse current-observation lookup can extend retrieval coverage. It does not
show that either lookup improves decisions or Elo. The actual replay action is
not necessarily a good action; counts omit tactical context, belief-state
risk, legal moves across particles, the v35 conditional-logit blend, and the
engine's final selection. The lookup is not a composable strategy model or
DeepRL update.

The split is game-disjoint, but this probe has not established a strict
chronological holdout or a state-disjoint split: repeated positions/observations
can appear across different games. Treat these scores as retrieval diagnostics
for this corpus, not future performance. Also, actor-visible board text alone
omits observation history and the opponent's inferred hidden state. A safer
next test is to build causal, compact context features and compare exact-only,
feature-model-only, and blended scores on a chronological game split, then
measure legal-action NLL/calibration, tactical-stratum recall, and which chosen
moves actually change in referee rollouts. Do not ship this table into the
runtime based on these retrieval scores alone.

## Reproduction

The raw metrics, team breakouts, ply bins, split hashes, and data counts are in
[`context-backoff.json`](context-backoff.json). The auditor is
[`audit_context_backoff.py`](../../tools/audit_context_backoff.py); its focused
canonicalization tests are in
[`test_audit_context_backoff.py`](../../tools/test_audit_context_backoff.py).
