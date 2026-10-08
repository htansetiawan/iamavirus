# Root chance aggregation: controlled result

Changing adversarial hidden-board aggregation to posterior expectation did not
improve the replay safety gate. All three paired intervals cross zero. Keep
the current default; this experiment has no arena release or Elo result.

The frozen r2 benchmark evaluated 453 development games / 906 seats with the
same repairs-plus-v4 neural graphs, 2,048 particles, hand opponent prior,
legacy prediction, history mode 0, seed 777, 400,000 nodes and one search
thread. The benchmark does not load an opening book. The 1,338 decisions
include 906 initial positions and **432 terminal positions**, 68 of which have
no safe legal action. Terminal decisions are the relevant denominator here.

| Mode | Sample | Aggregation | Fatal / 432 | Avoidable fatal / 364 |
| --- | --- | --- | ---: | ---: |
| 0, default | Representative plus strided entries | Matrix regret matching | 165 | 97 |
| 1 | Posterior population entries | Matrix regret matching | 160 | 92 |
| 2 | Same posterior sampling as mode 1 | Maximum mean payoff | 166 | 98 |

| Paired comparison | Saved | Newly fatal | Fatal-rate change, percentage points | Game-bootstrap 95% interval |
| --- | ---: | ---: | ---: | --- |
| Sampling: 1 minus 0 | 18 | 13 | −1.16 | −3.70 to +1.39 |
| Aggregation: 2 minus 1, primary | 10 | 16 | +1.39 | −0.93 to +3.70 |
| Combined: 2 minus 0 | 20 | 21 | +0.23 | −2.78 to +3.24 |

The primary comparison changes 97/432 terminal moves, so the experiment did
alter behavior. It does not establish a safety improvement. The IAmAVirus
subset has only 33 terminal decisions: mode 0 and mode 2 both lose 20, with two
saves offset by two new fatalities. This subset is too small for an opponent
strength claim.

The current algorithm's pessimistic aggregation can explain particular choices,
but simply replacing it with a posterior mean does not resolve the broader
failure pattern. The posterior and the determinized future search values can
both be wrong. This test does not measure offensive success, complete-game
outcomes or more sophisticated information-set planning. Those questions are
still open; the present result gives no reason to switch defaults or launch a
parameter sweep around this selector.

## Verification

- 129 focused objective, probability-mass, determinism and new-mode legality
  checks pass; the original 622 engine checks also pass.
- All **1,338 default decisions** match every recorded decision field from the
  previous frozen r3 runtime, not just the total number of losses.
- On three diagnostic histories, modes 1/2 receive identical sampled indices,
  searched node counts and **496 full-precision payoff cells**, with no clock
  fallback. Six original control decisions also match exactly.
- An initial test invocation used the evolving shared opening book and failed
  two assertions. Tests now use the pinned book from the historical source
  revision and an isolated working directory; the failed attempt is retained
  in `correctness.json`. This book is not used by the replay benchmark.
- `correctness-r2.json`, `parity-r2.json`, `default-full-parity.json` and the
  three `*-comparison.json` files retain hashes and exact checks.

The implementation and predeclared design are in
[`../../candidates/posterior-root/`](../../candidates/posterior-root/).
Large frozen binaries, models and logs are under
`/media/henrytan/seagate/iamavirus/astra/belief/posterior-root-remaining453-20261008/`.
Observed wall times are not isolated CPU speed measurements. One seed and
reused development games do not support a general verdict on Bayesian planning.
