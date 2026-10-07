# Previous-mover continuation evidence

Experimental and **off by default**. Not included in the immutable Astra v12
archive (a5f806d0039f). This is a belief-consistency experiment, not a new release.

The course referee calls outcome before delivering observations. A noninitial
observation therefore proves that the previous mover's king was not missing or
attacked. It does not prove the current player's king is safe: hidden checks
are allowed, and the defender still has a move. The new filter applies this
phase-correctly after either player's move, keeping all legal actions in the
opponent prior's normalization before conditioning on continuation.

Recovery proposals satisfy the same fact, with a limit of 32 proposals per
target particle. A partial valid population is refilled. If no proposal survives,
the engine reports `continuation_evidence_conflict` and falls back to an explicitly
inconsistent population to remain operational. This is not a valid posterior or
a solved recovery problem; a release gate must require zero such conflicts.

All nine suites pass, including **1,153 belief checks**, and **18,625/18,625**
referee checks pass. Controlled tests cover both colors, hidden checks by either
mover, both prediction paths, recovery, and exhausted contradictory observations.
The older random audit is not a continued-play proof because it can run past
king exposure with this option off. See `full-tests.log` and `belief-tests.log`.

The replay probe now excludes the completed terminal frame for every arm;
feeding it as a live observation would invent false continuation evidence.
Four seeds (1, 2, 3, 777), 2,048 particles, capture anchoring and pawn deductions
on, only continuation/grouping varied. Every arm matches current visibility and
capture constraints. New continuation arms have zero previous-mover-invalid
particles and zero recovery conflicts in these three histories.

| Replay / live updates | Control truth held / collapses | Continuation | Grouped | Grouped + continuation |
|---|---:|---:|---:|---:|
| bluqrpex / 260 | 131 / 3 | 131 / 4 | 136 / 3 | 136 / 3 |
| qyzsbfdc / 208 | 69 / 7 | 69 / 9 | 112 / 6 | 112 / 6 |
| dlhy2zfg / 720 | 185 / 4 | 193 / 4 | 176 / 8 | 252 / 5 |

These are correlated updates along three selected games, not independent matches.
The mixed results do not establish better play. In particular, ungrouped
continuation adds collapses in two histories. Per-game raw traces, probability
scores and timings are in each named directory; timings were measured under
other host work and are diagnostic only.

The older Astra research engine differs from the current release in other ways.
`tools/build_belief_runtime.py` therefore stages the immutable v12 ZIP and overlays
only the experimental belief/observation code, with all four new options default
off. It rejects learned prior 2 because this overlay currently supports only
prior 0/1. It is a research harness, not a packaged arena artifact.

On the previously opened five-game/40-decision release corpus, this staging with
all flags off selects **40/40 identical moves** to the archived v12 benchmark.
`runtime-parity/summary.json` pins binaries, model hashes and overrides. The
stage resides in `build/modern-runtime-v2`; an earlier failed staging remains in
`build/modern-runtime` and must not be used.

The next action gate toggles continuation within the same modern binary, with
capture/deductions/grouping enabled in both arms. It is pending while Fable's
timed match lanes occupy the agreed CPU cores. No new strength claim is made.
