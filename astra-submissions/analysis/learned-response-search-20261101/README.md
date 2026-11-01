# Learned-response CFR: decision gate passed, full games pending

1 November 2026. An isolated v37 build now uses the frozen visible-response
student inside opponent information sets. The 39-decision screen passes its
predeclared gate. A full-clock pilot is prepared; there is no arena submission
or playing-strength result yet.

## Change and correctness

At an expanded opponent information set, the effective strategy is 25%
learned response and 75% adversarial free strategy. The solver's regret update
accounts for that restricted free part, using the byte-identical CFR source
already checked against independent matrix/chance-tree/Kuhn oracles in
experiment 207. This is local data-biased response; full-game safety guarantees
do not follow for our sampled, truncated search.

The student receives only the actor's current view and legal actions. The
adapter cannot accept a full Position. Repeated information sets must have
identical ordered observable inputs; a mismatch disables the restriction and
fails the screen. Belief weights, king/queen guards, Stockfish, clocks and
root purification are unchanged. No edits to Fable's core checkout.

Adapter encoding matches Python on **1,351 real actor decisions**, both
colours, plus explicit promotion fixtures. Integration ASan/UBSan tests pass
for initialization, different hidden boards with identical observations,
reuse, growth, own-player exclusion, conflicts and disabled/missing models.
See [adapter tests](adapter-tests.json), [integration tests](integration-sanitizers.json),
and the [pinned source](../../experiments/learned-response-search-20261101/provenance.json).

## Frozen replay comparison

Eight November 1 v37 games, four per colour, ID-hash selected without outcomes
and disjoint from the preceding fixed-tree/exact-history panels. Use own turns
9, 17, 25 and the final two recorded own decisions when available. This creates
39 cases from HYPOTHERMIA, duck, Decent Chess Bot, Instructors and Mist
Opportunities. Endpoint selection is diagnostic, not population sampling.

All **117 first-attempt executions** completed with valid protocol and legal
moves. Every bot received only its permitted observation history and forced
previous own moves. Labels were joined afterward. All 719 recorded frames
passed replay validation. Source and plan were published at `859fcc3` before
execution; no retry, parameter sweep or model switch occurred.

| Measure | Exact v37 | Patched, disabled | Learned response |
|---|---:|---:|---:|
| Immediate king-loss choices | 6 | 6 | 5 |
| Bounded exchange losses of at least two points | 1 | 1 | 2 |
| Bounded queen losses of at least four points | 0 | 0 | 0 |
| Median search nodes | 79,152 | 78,818 | 73,227 |

Learned response changes 14/39 choices versus disabled; disabled changes 3/39
versus exact v37 under the same wall-clock budget. First-reply model coverage
exceeds 0.5 in every case. Median adapter/inference time is **27.27 ms** inside
the 2.5-second cap. Every model query and repeated-input check succeeds.
Changes in tree size also reflect different search choices, so the node
counts do not isolate computational overhead.

All frozen checks pass, including the allowance of one additional material
label. This earns tactical review and a bounded full-game trial, not an Elo
claim. Zero queen-loss positives do not establish queen-guard quality. See
[plan](plan.json), [summary](summary.json), [all labelled choices](labelled.json)
and [post-fit response review](changed-choice-review.json).

## Two changes that matter

The course referee independently verifies 125 checks for the following lines:

- **HYPOTHERMIA `xrhh3nfx`, ply 87:** both controls choose `Kg6-h6`, losing
  immediately to the hidden queen on f8. Learned response chooses `h3-h2`,
  which survives this move. It does not establish survival or a win later;
  the historical game also played h3-h2 and lost two plies afterward.
- **HYPOTHERMIA `23paw9tn`, ply 48:** learned response chooses `Nc5-e6`,
  permitting `Qd6xe5` and a four-point net loss even after the best immediate
  safe response. Both controls choose `Rd1-e1`, which allows `Re1xe5` after
  that capture and a four-point gain. The regression is real under the short
  exchange label. No forced-loss proof or long-term material evaluation is
  claimed. On the true-world opponent observation, the student gives Qxe5
  19.2% probability; this is not evidence that the sampled solver saw the
  same board or ignored that reply.

Both the survival improvement and material regression are retained. The model
still has the predictive surprise-capture weakness recorded in experiment
208. See [independent tactical review](tactical-review.json).

## Full-clock pilot

The [separate plan](full-games/plan.json) fixes eight 180+2 head-to-head games
against exact v37, four colour-swapped pairs on two exclusively reserved core
pairs. A score of at most 2/8 closes this configuration. Otherwise, eight
Misty games compare candidate and baseline on matched colours/seeds (four
each). Larger testing requires at least 4/8 head-to-head and candidate Misty
score no worse than baseline, without technical faults. These small samples
cannot justify release or an Elo estimate.

The course referee and owned process-group turn isolation charge observation
processing on the active turn. Model/source/referee/opponent dependencies are
pinned; started games cannot be silently rerun. All three players pass the
protocol smoke test. Misty is an authentic local engine, not verified arena
submission bytes. Results belong under `full-games/`.

The public replay refresh independently added 54 validated games (six already
cached), with no quarantine or errors. It did not alter the frozen panel.
The fetched standing snapshot has active v37 at 53W–4D–43L, Elo 1903.85,
rank 10. Those are v37's arena results, not this experiment's results.
