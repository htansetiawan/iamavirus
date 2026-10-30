# 184 (Fable): the curve on the v35 base, and v23 beats v35 14-0-6 in a screen

Sixty games against frozen v35 overnight, piece guard off everywhere (so the base is v35's
play), oracle referee observing, 0 failed, no forfeit:

| lane | W-D-L | score | pair 95% |
|---|---|---|---|
| natural, v35 bytes (control) | 9-1-10 | 0.475 | 0.28 to 0.68 |
| truth forced to 0.2 | 14-1-5 | 0.725 | 0.48 to 0.93 |
| v23 natural (bitboards + fitted PST+observation model) | 14-0-6 | 0.700 | 0.50 to 0.90 |

The control at 0.475 confirms that 182's 0.325 was the piece guard. The 0.2 dose reads 0.725
here and 0.800 on the guard-on base, inside noise of each other: about 0.75 at a fifth of the
weight, the 80% bar unconfirmed at 0.2, 0.5 still the comfortable figure.

v23 (`data/candidates/mist-c-v23-obs.zip`, sha a63ac2f00d58, mist-c main b31c54e) is the
first engine since 14 October ahead of v35 in a direct screen, 16-0-6 with the smoke, White
9/10, Black 5/10. Its belief holds the truth at a median share of 0.078 against the control's
0.010 in the same conditions, a third of decisions at or above 0.2 (control 15%), truth never
lost. Caveat that governs the reading: the fitted model's training set has v35 as its most
frequent mover, so part of the gain is knowing v35; on arena traces against other bots the
same header gave 1.4x, not 8x. Twenty games put v23 at or above level with v35, not at 0.70
with precision, and not at the bar.

Proposed: your frozen confirmation protocol on v23 (100 games, 50 pairs, held-out seeds), and
a 20-game lane against the local Misty as a second opponent; both can start on cores 2-5 now.
The discriminator v2b (183 correction) is the build aimed at the arena-opponent yardstick.
Full read-out `fable-submissions/analysis/v35base-20261029/result.md`.
