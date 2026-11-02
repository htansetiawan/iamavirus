# Frozen recurrent risk model recovered

The old attention-small graphs are present under
`/media/henrytan/seagate/git/iamavirus-data/astra-legacy/representations/capacity-v4-full3766-20261008/attention-small-export/`.
The former `/seagate/iamavirus/...` and `/seagate1/iamavirus/...` paths are absent.
Manifest, observe graph and score graph exactly match the 11 October receipt.
A 6.7MB local cache is gitignored; it is an unchanged copy, not a new model.

Original smoke handle 98432 completed with exit 0. Single-thread CPU inference
passed on the first White and first Black games in the existing calibration
TRAIN partition: 218 observations, 108 decisions and 3,345 candidate scores.
Candidate permutation error is zero. Recurrent-state reset changes the state,
and altering oracle boards, opponent observations/actions, clocks and metadata
leaves the projected model input unchanged. Graph outputs are finite.

This verifies asset identity and compatibility with the current feature-v2
pipeline. It does not repeat the original PyTorch/native parity comparison,
measure prediction quality, fit any weights or integrate a playing engine.
The elapsed smoke time includes loading and repeated runs; it is not an arena
latency benchmark. The CPU core was released after the process completed.

The model already uses square attention and GRU history. Describing a
history-aware risk model as entirely new would ignore this experiment. Its old
fusion result belonged to the hybrid engine; the bounded follow-up in
`../recurrent-risk-complement-20261102/` asks whether the same frozen signal
adds useful information to mist-c risks on reused development games.
