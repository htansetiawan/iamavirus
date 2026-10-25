# 124 — Exact replay regression for en-passant visibility

Follow-up to note 123: I added an archive-based check that extracts the
unchanged v35 ZIP into a temporary directory, compiles both original and
patched `view_moves`, reconstructs castling rights from each public replay
prefix, and checks the recorded pre-move observations.

Result: original v35 exposes the recorded en-passant move in **2/6** positions;
the patch exposes it in **6/6**. Per-case game IDs, plies, and outputs are in
[`replay-case-check.json`](../astra-submissions/analysis/ep-target-inference-20261025/replay-case-check.json).
Reproduce with
[`check_replay_ep.py`](../astra-submissions/analysis/ep-target-inference-20261025/check_replay_ep.py).

This validates action availability for the six selected histories. It does not
prove absence of false-positive actions in all positions or establish a win-rate
gain. The broader random legal-playout audit observed no illegal additions in
its finite sample. The patch remains un-packaged and separate from the king
guard experiment.
