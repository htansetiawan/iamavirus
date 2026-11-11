# A numerical example of weighted worlds and regret

This is an **invented teaching game**, not a chess position or a bot match.
It runs the unchanged `cfr.c` and `cfr.h` extracted from the immutable v38
ZIP. It checks the presentation arithmetic; it does not validate our entire
FoW search construction or establish a playing-strength result.

## The hidden information

Imagine two possible worlds: W0 has probability **75%**, W1 **25%**. We
cannot tell which world we occupy. We choose A or B. The opponent knows
the world but cannot see our action before choosing X or Y.

The supplied utilities are for us; the opponent receives their negatives.
They are invented numbers, not calibrated win probabilities or Elo.

| World | Our action | Opponent chooses X | Opponent chooses Y |
| --- | --- | ---: | ---: |
| W0, probability 0.75 | A | +0.6 | −0.2 |
| W0, probability 0.75 | B | −0.4 | +0.4 |
| W1, probability 0.25 | A | −1.0 | +0.6 |
| W1, probability 0.25 | B | +0.6 | −0.2 |

Our two decision nodes share **one information set I**: we must choose
the same A/B probabilities in both worlds. The opponent has J0 and J1,
because it knows the world. Within each J, it must use the same X/Y
probabilities after A and B because our action is hidden.

The fixture has 15 nodes, three information sets and six action slots.
It starts uniformly; unlike the deployed growing-tree builder, it does not
initialize new information sets on a best-scored child.

## One actual update, with the arithmetic exposed

Initially everyone mixes 50/50. Against that opponent strategy:

```text
value(A) = 0.75 × (0.6 − 0.2)/2 + 0.25 × (−1.0 + 0.6)/2 = 0.10
value(B) = 0.75 × (−0.4 + 0.4)/2 + 0.25 × (0.6 − 0.2)/2 = 0.05
our current mixed value = 0.5 × 0.10 + 0.5 × 0.05 = 0.075
instantaneous regrets = [0.10 − 0.075, 0.05 − 0.075] = [+0.025, −0.025]
```

CFR+ clips negative cumulative regret to zero: `[0.025, 0]`. The predictive
step adds the latest instantaneous regret before normalizing positives:
`[0.025, 0] + [0.025, −0.025]`, giving probabilities `[1, 0]`.

The source then updates the opponent against our **new** strategy. After
the complete alternating iteration, its actual arrays are:

| Information set | Cumulative clipped regret | Latest instantaneous regret | Current strategy |
| --- | --- | --- | --- |
| I: our A/B | [0.025, 0] | [0.025, −0.025] | [1, 0] |
| J0: opponent X/Y in W0 | [0, 0.3] | [−0.3, 0.3] | [0, 1] |
| J1: opponent X/Y in W1 | [0.2, 0] | [0.2, −0.2] | [1, 0] |

The chance weights are included in those regrets. The resulting profile
is worth **−0.4** to us. Favoring A was appropriate against the previous
opponent mixture; it is bad against the newly updated response. The next
iteration changes our probabilities again. This is why the values and
strategies must be recomputed together.

These regrets compare alternatives inside the current calculation. They
are not differences between our move and a move in an old arena game.

## The mixed solution and two tempting mistakes

After the fixed 10,000 iterations, the shipped solver returns:

- Our A/B: **[0.5, 0.5]**.
- Opponent X/Y in W0: **[17/24, 7/24]**.
- Opponent X/Y in W1: **[1, 0]**.
- Utility: **0.025 = 1/40**.

An independent calculation enumerates the breakpoints of the worst-response
utility as a function of our A probability. Its maximum occurs at exactly
1/2 with value 1/40. Independent best-response calculations match the C
solver at every saved checkpoint; the final toy gap is below 10⁻¹².
This is a result about this finite fixture only.

**Mistake 1: choose separately for each imagined world.** If we incorrectly
let our strategy depend on the hidden world, we can mix A with probability
1/2 in W0 and 1/3 in W1. The apparent value rises to **11/120 ≈ 0.09167**.
That strategy uses information we do not have. Sharing an information set
prevents this particular form of strategy fusion in the fixture.

**Mistake 2: replace the mixed strategy with its largest entry.** Against
best responses, pure A is worth **−0.4**, pure B **−0.35**. Both are worse
than the mixed value +0.025. A large probability is not a guarantee that
purifying the strategy preserves its value.

V38 ultimately uses argmax, but its sampled worlds can vary between runs.
This fixture omits that randomness, guards and changing frontier values.
It does **not** quantify an arena penalty for argmax. The earlier failed
[restricted-mixing pilot](../../../chatroom/203-astra-stable-root-mixture-pilot.md)
remains negative evidence on that tested rule; this example does not reopen it.

## What carries over to our bot

The generic solver performs these updates on a larger constructed tree.
Its root chance probabilities come from represented worlds; its frontier
utilities come from Stockfish rather than this invented payoff table.
It groups represented indistinguishable decisions and updates both players.
The tree and regret arrays are discarded after the move. Offline opponent
model fitting is a different process with a different lifetime.

Arithmetic correctness of this tiny game does not certify that the FoW
builder contains the right private-history alternatives, perfect recall,
boundary values or the full Obscuro subgame construction.

Original verified command:

```bash
.venv/bin/python astra-submissions/experiments/presentation-pcfr-20261111/verify.py
```

The verifier creates outputs exclusively and refuses an existing build;
preserve the saved run rather than overwriting it. The first compile-only
preparation stopped because `-Werror` promoted an existing warning in the
unchanged shipped source. That preparation is retained. The successful
build records the same warning and exempts only `maybe-uninitialized` from
warning-as-error; the shipped source bytes are unchanged. No numerical
result was discarded or repeated before that correction.

[Source and checks](../../experiments/presentation-pcfr-20261111/verify.py)
· [Fixture](../../experiments/presentation-pcfr-20261111/demo.c)
· [Exact results](result.json) · [Iteration snapshots](trace.json).
