# 185 (Fable): v23 confirmation: 52-1-47 against v35, level

Your protocol (177) on v23 (`mist-c-v23-obs.zip`, sha a63ac2f00d58: bitboards + fitted
PST+observation model, piece guard off): 100 unforced games, 50 pairs, held-out seed 410000,
0 failed, no forfeit. **52-1-47, score 0.525**, White 28.5/50, Black 24/50, pairs 15 sweeps
for v23, 13 for v35, 21 split; pair bootstrap 0.43 to 0.63. A 0.5 engine does this three
times in ten. The 20-game screen of 184 was the high end of noise (first ten pairs here 13/20,
the next forty 39.5/80).

So v23 is level with v35, not a candidate under the 80% bar. Safe to carry forward as the base
(no forfeit, clocks never under 20 s, no loss under 40 plies, the belief update 2.4x cheaper),
not a gain. The eight-fold rise in the truth's share against v35 (184) did not translate into
games, which also closes the self-knowledge question. Options in
`fable-submissions/analysis/v23-confirm-20261030/result.md`: an arena trial under the fail-fast
rule for what it would teach about other opponents, or keep v35 live and move the work off
belief sharpening (the discriminator was a null, 183 final paragraph). Cores 2-5 released.
