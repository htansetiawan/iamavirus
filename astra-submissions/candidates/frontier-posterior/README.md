# Weighted frontier with posterior root selection

This experiment combines two existing, unpromoted research changes. It asks
whether chance-weighted root selection can use the frontier's improved hidden
state support. It is not a new arena release or a stronger bot claim.

The frontier alone reduced zero-support events but increased terminal fatal
choices from 158 to 164 on the reused development set. Its risk audit found 19
new fatal choices with higher estimated king-loss risk than the safe move
chosen by the control. The three largest risk disagreements were reproduced
with the old binary's row trace: all three safe alternatives were present in
the matrix. Shortlist omission therefore does not explain those three cases.
Other evaluation charges and downstream search also matter; selecting minimum
immediate risk has not been demonstrated to improve complete games.

The [predeclared design](design.json) compares three root modes at frontier
capacity 8,192, grouped prediction, prior 1 and unchanged search/safety terms:

| Mode | Sampled boards | Final choice |
| --- | --- | --- |
| 0 | Existing representative plus strided entries | Matrix regret matching |
| 1 | Posterior-distributed entries | Matrix regret matching |
| 2 | Same sample as mode 1 | Maximum mean payoff |

Mode 2 versus mode 1 isolates the selector. Mode 1 versus mode 0 isolates
sampling. The earlier experiment without this frontier found all three modes
inconclusive. This follow-up is motivated by the observed interaction; it is
not independent confirmation. Eight sampled boards remain noisy, the belief
is approximate, and alpha-beta still assumes full information within a board.
This is not extensive-form CFR.

`basis.json` reconstructs the same pinned root and committed frontier sources.
The only new engine option is the existing `FOW_ROOT_MODE`, combined with the
frontier option. Both remain off by default. `FOW_DEBUG_ROOT=1` additionally
prints exact final row probabilities for diagnosis; it changes no decisions.

```sh
taskset -c 2 .venv/bin/python astra-submissions/tools/build_posterior_runtime.py \
  --source astra-submissions/candidates/frontier-posterior \
  --output astra-submissions/build/NEW_DIRECTORY
```

Before the full 453-game comparison, require the original engine/selector
tests, mode-0 decision parity, and identical mode-1/mode-2 sampled indices,
node counts and exact payoff cells on the three selected histories. Full
control parity is checked again over all 1,338 decisions. The 432 terminal
positions are reported separately from the 906 initial positions. No clocked
lane is earned by a three-position diagnostic or an average belief metric.

The first build passes 622 original engine checks and 129 selector checks.
Mode 0 reproduces all six selected control decisions. Modes 1 and 2 share all
552 payoff cells, sampled indices and node counts over those six decisions,
with no clock fallback. Each alternative selector saves one of the three
fatal positions, but a different one; two remain fatal in each arm. This
does not establish a better selector. Receipts are in
`../../analysis/frontier-posterior/`. The full three-arm comparison is running.
