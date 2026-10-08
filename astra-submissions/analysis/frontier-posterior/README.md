# Frontier and posterior root interaction: no promotion

The weighted frontier's better state support did not become better terminal
decisions after changing root sampling or selection. This experiment is
complete; the options remain off by default and do not earn a clocked lane.

The [design](../../candidates/frontier-posterior/design.json) fixed 453 reused
development games, 2,048 engine particles, a persistent frontier capacity of
8,192, 400,000 search nodes, prior 1, grouped prediction, history 0, seed 777,
one search thread and no opening book. The 906 initial positions are separate
from the 432 terminal decisions. This is forced-history move safety, not a
measurement of full-game outcomes or Elo.

| Root mode | Terminal fatal / 432 | Avoidable fatal / 364 |
| --- | ---: | ---: |
| 0: existing sampling, matrix regret matching | 164 | 96 |
| 1: posterior sampling, matrix regret matching | 163 | 95 |
| 2: same posterior sample, maximum mean payoff | 170 | 102 |

| Comparison | Saved | Newly fatal | Fatal-rate change, percentage points | Paired game-bootstrap 95% interval |
| --- | ---: | ---: | ---: | --- |
| Mode 1 minus mode 0 | 12 | 11 | -0.23 | [-2.31, +1.85] |
| Mode 2 minus mode 1, primary selector comparison | 10 | 17 | +1.62 | [-0.69, +3.94] |
| Mode 2 minus mode 0 | 16 | 22 | +1.39 | [-1.39, +4.17] |

All three differences are inconclusive. In particular, replacing the selector
with maximum posterior mean did not deliver the hypothesized gain. This does
not prove that information-set search is unhelpful: eight approximate board
samples and perfect-information search within each sample remain substantial
limitations. It does show that this particular combination has not earned
promotion.

Verification passed 622 engine checks and 129 selector checks. On the selected
diagnostic histories, modes 1 and 2 shared all 552 exact payoff cells, sampled
indices and node counts. The full mode-0 control reproduced all 1,338 earlier
frontier decisions. The three inspected safer alternatives were already in the
root matrix, so shortlist omission did not explain those cases.

`control-parity.json`, `verification.json`, and `mode*-vs-mode*.json` retain the
checks, paired differences, changed decisions and input hashes. The benchmark
SHA256 is `fc633df648478dfceaf4f9a288f644d8792e7284cdb99e3df7de3208fa9f68db`.
Full logs are under
`/media/henrytan/seagate/iamavirus/astra/belief/frontier-posterior-action453-20261008/`.
One seed and repeatedly used development histories limit generalization.
