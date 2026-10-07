# Bounded history recovery on the current opponent-prior interface

Experimental and off by default. This is a source port, not an arena archive.
The immutable basis is Fable's arena-v13 archive; `basis.json` pins its complete
SHA256 and the original belief sources. Root/Fable implementation files are
not edited by this candidate.

The tracker can rewind up to 16 observations and reconstruct legal histories
when the sampled population disappears. It matches complete actor observations
and rejects histories in which the previous mover already lost its king.
Only our recorded actions are known: opponent actions are enumerated, never
read from replay truth. Each attempt has a 250,000-transition ceiling and
65,536 temporary-state limit. The intermediate weighted beam is
`clamp(2 * particles, 64, 8192)`; smaller intermediate supports remain intact.
The final population is an approximate unweighted resample. An incomplete
expansion is discarded, and an unsuccessful recovery restores the RNG state
before the ordinary random reconstruction runs.

Compared with the first Astra prototype, the key change is preservation of the
opponent model's state. Complete-state equality includes board placement,
castling rights, en passant, side, halfmove clock, **last opponent destination
and whether that move captured**. Both memory fields are carried through
checkpoints, pruning, resampling and own moves. Opponent successors update the
memory; own successors retain it. Priors 0 (uniform), 1 (hand) and 2 (learned)
all use the same interface as the archived engine.

Two related correctness repairs are active in every mode. `ApplyOurMove` now
filters the memory arrays along with the position array; a rejected castling
hypothesis can no longer shift memory onto a different board. If no hypothesis
can execute our action, all three arrays become empty and the next observation
triggers recovery. The old code retained the unchanged population in this case.

## Independent experiment switches

The staging builder adds `FOW_HISTORY_MODE` to the engine:

| Mode | Behavior |
| --- | --- |
| 0 | Original filter with the own-move memory repairs above |
| 1 | Mode 0 plus complete observation matching and previous-mover survival |
| 2 | Mode 1 plus bounded history recovery before random reconstruction |

Modes 1 and 2 also check random reconstruction proposals, with at most 32
attempts per requested particle. If none matches, the degraded fallback is
explicitly reported as `history_evidence_conflict`; it is never certified.
`history_full_certified` means that the retained states descend through a
compatible history from the known opening. It does **not** mean the true board
is in the finite population. A checkpoint following random reconstruction
certifies only the subsequently replayed window.

`../../tools/build_history_runtime.py` creates an isolated tree with the
archive's search, rule implementation and neural models. Use
`--expected-sha256` from `basis.json`, a new `--output` under
`astra-submissions`, and `--control` for the unchanged archived belief. The
engine's default history mode remains 0. The build manifest records source,
model and binary hashes. The runtime is compatible with the archived v1
features; it does not load Fable's newly changed root feature implementation.

## Evidence and open work

- Targeted suite: **2,053 checks, zero failures**, including memory identity,
  capture updates, both colors/all priors, special moves, impossible histories
  and transactional RNG behavior after a failed multi-step replay.
- Nine existing unit suites pass on the initial port. The final RNG-only change
  is covered by the revised targeted suite. The referee differential stage was
  explicitly skipped in that invocation; no new referee result is claimed.
- Default-mode action comparison against the archived belief: **40/40 identical
  decisions**, five complete histories, 400,000 nodes, one search worker, seed
  777. This is a compatibility check, not an improvement estimate.
- An executable using the original archived belief and a test-only friend
  accessor reproduces the alignment defect: after a castling rejection it has
  one position, two memory entries, and destination 17 where 22 is required.

The first six-seat pilot is mixed and predates RNG rollback. At 561 observations
per arm, hand-prior truth retention is 169 / 193 / 193 for modes 0 / 1 / 2;
learned-prior retention is 290 / 252 / 252. Strict modes remove view and
continuation mismatches, but no general belief-quality improvement is proven.
The failed-recovery RNG effect means its mode-1/mode-2 differences cannot be
attributed only to successful rescues. The traces are retained, not relabeled.

The broader run uses the corrected binary on **634 historical losing seats**
(360 Black, 274 White), three modes, two priors and seed 777: 3,804 runs. This
corpus is selected for losses, not representative of all arena play, and it is
not a held-out Elo test. The result journal and per-observation traces are at
`/media/henrytan/seagate/iamavirus/astra/belief/history-v2-corpus-20261007/`.
Completion, failure counts, calibration, truth retention and latency must be
inspected before selecting an action gate or changing any default. Clocked
paired games remain necessary before a playing-strength claim or archive.
