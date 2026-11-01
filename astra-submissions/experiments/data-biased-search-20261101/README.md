# Data-biased response inside v37 search

1 November 2026. Isolated C experiment; no arena archive or default change.

The history table currently changes belief weights but does not constrain
opponent behaviour inside the game-tree solver. Test using its observed
action frequencies at matching opponent information sets:

```
q_I(a) = count(I,a) / N_I
c_I = 0.5 * N_I / (20 + N_I), if N_I >= 3 and every counted action is legal
c_I = 0 otherwise
effective_opponent(a|I) = c_I * q_I(a) + (1-c_I) * free_strategy(a|I)
```

The opponent optimizes the free part; our strategy remains unrestricted.
No fallback predictor is invented at an unseen history. Use one distribution
per information set, not one per true board. Keep belief, history table, root
guards, Stockfish, root purification, and clocks fixed to exact v37.

This implements the local restriction in equation 1 of
[Johanson and Bowling, AISTATS 2009](https://bowlingmh.github.io/papers/09aistats.pdf).
It is not the game-level hidden coin of
[Restricted Nash Response](https://poker.cs.ualberta.ca/publications/NIPS07-rnash.pdf).
The paper's full-game guarantees do not transfer to our sampled, truncated,
last-iterate search with heuristic leaves and a purified root.

At a restricted player's update, regret uses the controllable free policy:

```
instant_regret(a) = reach_others * (1-c_I) * (child_value(a) - free_value)
```

Subtracting the effective-policy value instead is wrong. The returned node
value and all opponent/chance reach factors still use the effective policy.
The unrestricted best-response diagnostic must remain unrestricted even
when solver constraints are installed.

## Advancement contract

1. Build from the immutable v37 archive in this directory only. Publish source
   and pins before policy diagnostics. Feature off must reproduce original
   CFR arrays bit-for-bit on fixed trees/iterations, including tree growth.
2. Independent normal-form linear-program and explicit chance-node oracles
   check constrained solutions, values and best responses. Include hidden
   information, zero confidence, confidence one, and new information sets.
   Run sanitizers and ordinary Kuhn coverage before any policy screen.
3. Freeze an outcome-blind 8-game v37 panel from completed games on 1 November
   (after the table's training cutoff), both colours, with early and middle
   decision prefixes. Compare exact v37, patched-off and enabled at the same
   seed and 2.5-second cap. No true boards or future replies enter the bots.
   Verify rules and protocol; record history matches, confidence, root-reply
   model coverage, actions, immediate king loss and bounded exchange labels.
4. Stop on any correctness defect. If no meaningful decision changes or
   history coverage exists beyond the opening, report that limit before a
   match trial. A small panel cannot establish strength. Any advancement to
   full-clock games requires a separately frozen paired plan and available
   cores. Do not relax guards to make a result pass.

One confidence setting, no sweep. This is new search behaviour, not a refit
of the failed stationary-style model or another root risk calibration.
