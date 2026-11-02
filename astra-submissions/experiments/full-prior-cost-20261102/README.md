# 225: affordable full tactical likelihoods

Experiment 224 rejects replacing the deployed prior with the existing student.
It also measures a large gap between the full and cheap deployed models. V37
switches to cheap above 10,000 worlds, when ambiguity and expansion costs grow.
We first test whether existing exact speedups can pay for full features.

Three isolated implementations share the exact v37 model coefficients and
history table: original; Fable's bitboard and belief performance changes
14b22e9/382cbd2; those changes plus skipping the two zero-coefficient hidden
features **only when computing logits**. Public `move_features` continues to
export all features for training. If either hidden-feature coefficient is
nonzero, the scoring path calculates them too. No guard, cap, temperature,
selection rule, search or active candidate is changed.

Use the three exact pre-expansion snapshots already published in 223, each
with about 54,000 worlds. These are correlated captures of one selected game,
not representative strength or calibration data. Native preflight compares
public feature vectors and logits against the original model over every legal
move in one snapshot, plus Fable's rules differential test on pinned vectors.

After the preflight, publish before a fixed 18-call screen: three snapshots ×
three implementations × ordinary 10,000 threshold / full at all sizes. Rotate
arm order between snapshots; one execution per cell, no retries. Time only the
belief update, excluding parsing, truth labels and serialization. Every cell
records a canonical post-update hash and complete process receipt. Within each
threshold, all three implementations must yield identical canonical bytes;
ordinary outputs must also equal the original 223 post-update snapshots.

Advance only to a separately planned broader posterior/runtime test if parity
holds everywhere, the optimized full path costs at most 1.5 times original
ordinary in the median paired ratio, and no optimized-full cell exceeds 1.0 second. Otherwise
close this unconditional-full configuration at this cost screen. The thresholds
are engineering screens, not arena guarantees: prior-history changes, clock
thinning, endgame diversity and full-game results remain untested here.

Fixed scores on this chosen loss may explain a mechanism but cannot select a
variant. No model fitting, new full-game batch or release follows automatically.
Use cores 2–3, two belief threads, 3 GiB per child, 120-second child wall limit.
Existing 219 bytes and acceptance conditions remain frozen.
