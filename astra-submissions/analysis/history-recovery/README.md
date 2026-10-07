# Bounded history recovery — first prototype

**Experimental, off by default. No arena release or Elo claim.**

The filter can lose a true hidden piece after rebuilding a collapsed population.
The prototype tries to explain recent observations through legal move histories
before it scatters the remaining enemy census across unseen squares.

It retains 16 actor-view checkpoints, deduplicated with weights. Recovery tries
rewinds of 2, 4, 8 and 16 plies when available (plus the oldest shorter window).
Each attempt has a 250,000-transition ceiling, a 65,536-state temporary-pool
ceiling, and a beam width of `clamp(2 * particles, 64, 8192)`. Every returned
path matches the complete observation at every step and survives previous-mover
king adjudication. Own moves are replayed exactly; hidden opponent moves are
enumerated and weighted by the existing prior. A partially enumerated level
that exhausts its budget is discarded, not reported as a completed posterior.

Small weighted supports stay intact; larger supports are systematically
resampled. A checkpoint descended from an earlier random rebuild certifies only
the retained window. The `history_full_certified` flag is true only while the
support descends through validated transitions from the common-known opening.
This is a bounded smoother, not exhaustive inference or a permanent graph of
every discarded trajectory. It can still fail and fall back to random recovery.

## Correctness and provenance

- `belief-tests.log`: **2,170 checks**, zero failures. New tests cover both colors,
  recovery from the opening, a bishop becoming hidden and subsequently moving,
  castling, en passant, knight promotion, metadata retention, and contradictory
  own-action history.
- All nine unit suites passed in `full-tests.log`. That combined invocation's
  referee stage failed because `FOW_KIT` was omitted. It is preserved as a failed
  command, not relabeled as success.
- The isolated referee rerun with the correct kit path passed **30,100/30,100**
  checks; see `referee-tests.log`.
- Flag-off runtime parity: **40/40 identical choices** on five previously opened
  histories, `runtime-parity/summary.json`.
- The modern search gate overlays the immutable Astra archive `a5f806d0039f`
  with research belief/observation sources. It is not the live Fable worktree.
  Gate binary SHA: `29fad62293b3947a5e22b3bccddb73d248099b99b92c90f39b52fcd0f3722576`.
- `build-manifest.json` pins probe source and binary hashes. The generated
  `build/modern-runtime/integration-manifest.json` pins the staging build.

## Selected-history probe

Four seeds (1, 2, 3, 777), 2,048 particles. Control and history use capture
anchoring, deductions, grouped prediction and continuation. History additionally
checks full rendered observation equality before saving a checkpoint. This
combined experiment does not isolate re-expansion from that stricter filter.

| Replay | Updates | Random rebuilds, control → history | Truth held, control → history | History rescues |
|---|---:|---:|---:|---:|
| xidde3fz, Black | 344 | 11 → 9 | 56 → 78 | 3 |
| ea9ds6vw, Black | 536 | 8 → 3 | 68 → 228 | 2 |
| al0xlrqe, White | 380 | 8 → 2 | 106 → 101 | 5 |
| Total | 1,260 | **27 → 14** | **230 → 407** | 10 |

All history-arm updates match the full actor view. The control has mismatches
in two histories, which the new full-render check removes. Mean per-seed hidden
square Brier improves in all three histories, but al0xlrqe log loss worsens from
0.938 to 1.109 and truth retention falls. The hardest bishop failure is not
reliably repaired. Largest observed update was 192 ms, under shared CPU work;
this is a diagnostic measurement, not an isolated speed benchmark or arena
clock guarantee. Source: `probes-v1/state.json` and its per-run traces.

## Action gate

Same modern binary, model and flags in both arms except `FOW_HISTORY_RECOVERY`.
37 target seats, 274 decisions, hybrid, 400,000 nodes, seed 777, every sixth own
decision plus losing terminal positions. These are forced histories, not games
played by the candidate.

| Metric | History off | History on |
|---|---:|---:|
| King-losing choices | 16 | 14 |
| Avoidable king-losing choices | 4 | 2 |
| Survived recorded losing terminal position | 10 / 26 | 12 / 26 |

50 choices changed; 3 became safe and 1 became fatal. This warrants broader
testing, not promotion. It is not a comparison with active arena v10.
`action-gate/summary.json` records the exact inputs and overrides.

## Correction to the earlier deployed probe

The first frozen Fable-source probe omitted the engine's
`set_visibility_deductions(true)` call. Its four-argument constructor alone
leaves deductions disabled. The failed batch remains under
`../continuation-evidence/followup-probes/traces-v1/`, with an explicit invalid
release-configuration status. Its reported observation mismatches were a probe
configuration error, not evidence that the submitted build violated visibility.

Corrected probes against exact archive `68a89006f6c2` have zero full-view
mismatches on xidde3fz. They still demonstrate memory erosion: at seed 1, Bc3
has 2,048/2,048 support at ply 52, falls to **4/2,048 at the ply-59 reset**, and
ends at 1/2,048 before Kh7g7. These are controlled seeded reproductions, not the
arena bot's unavailable internal particle trace.

## Next gates

Isolate the full-view filter contribution, inspect the newly fatal decision,
port with Fable's per-particle move-prior metadata included in state identity,
then run the balanced corpus and real-clock paired matches. A merge key valid
for this Markov hand prior is not sufficient for a history-dependent prior.
The flag remains off until those gates justify changing it.

## Port to Fable's current prior interface

The subsequent implementation is in
[`../../candidates/history-v2`](../../candidates/history-v2/README.md). It carries
the learned prior's per-particle destination/capture memory through every
checkpoint and transition, separates strict filtering from recovery, and
restores RNG state after failed speculative replay. It also repairs own-move
filtering that previously misaligned positions and memory. The port has 2,053
focused checks and an archived-runtime compatibility gate; the full 634-seat
comparison is in progress. See the port README and `port-checks/correctness.json`
for the precise test scope. Neither prototype is enabled in an arena release.
