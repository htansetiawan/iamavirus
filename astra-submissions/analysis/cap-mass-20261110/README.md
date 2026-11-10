# Native cap mass: follow-up criterion fails

All eight first attempts finish. The independent audit verifies 502 replay
frames, permitted actor inputs, every forced action, all three binary snapshots,
selection keys/cutoffs and mass sums. No weights or playing decisions changed.

| Historical prefix | Pre-cap boards | Kept | Probability mass discarded | Effective weighted count |
|---|---:|---:|---:|---:|
| Instructors, eoyzqwuy | 221,778 | 200,000 | 0.0000002474% | 8.18 |
| Mist Opportunities, ck1nptse | 909,868 | 200,000 | 0.0000001176% | 31.55 |
| Knight Vision, 3rq7wk5e | 851,378 | 200,000 | 0.06397% | 1,057.08 |

Only these three first hard-cap events occurred. The other five prefixes
produce no captured event. **No clock-driven thinning event occurred**, so
this study supplies no empirical conclusion about that path or later caps.
The fixed follow-up criterion needed four snapshots across three games and
one discarding at least 1% mass; it fails both the count and effect conditions.
No sequential correction candidate or match follows.

Large reductions in board count here remove little supplied probability.
The weighted counts show concentration, not calibration: this study does
not label whether the concentrated worlds are right. Later observations can
amplify an earlier distribution error, and first caps do not represent all
middlegames. The single-step dropped-mass/TV calculation is not a cumulative
bound and says nothing about recoverability of a discarded true world.

## What was measured

The observer-only build copies the exact v38 source and inserts two calls
in belief.c. It leaves the RNG, ranking, selected indices, stored weights,
positions, histories, guards and forced protocol moves intact. At most the
first hard-cap and first paid-thinning event per process is exported. The
observer's elapsed cost may influence later clock-based thinning; two reserved
cores and two belief threads approximate the arena allocation, not its hardware
or exact populations. Source outside the insertions matches the archive copy.

Each saved binary has every input float log-weight, every original-index
random rank key, the actual retained indices and cutoff. Independent NumPy
review verifies the complete saved selection and mass arithmetic. The course
referee validates source boards, observations and moves; truth never enters
the actor. Every own action including the final one is forced, so no search
or Stockfish process runs.

Raw snapshots total 26,196,384 bytes on the mounted Seagate:
`/media/henrytan/seagate/iamavirus/astra/cap-mass-20261110/`.
Exact paths and hashes are in each result.json; Git contains protocol records,
source, preflight, plans, audits and receipts. The raw files are retained.

Original 6100 exits 0; independent review exits 0. Source/plan commit
084da7c3b3a1e387c8ac76edff3a2dfaa0165629 was on both mirrors before collection.
All 56 pinned files match. Strided/uniform binary fixtures, no mutation,
duplicate suppression, ASan/UBSan and both opening colors pass. Host cleanup
finds no diagnostic actor, and CPU0–1 is released. No GPU, refit, game batch,
new ZIP, release number or arena change.

## Prior-work correction

The earlier same-index threshold estimator was already implemented and
rejected in notes [060](../../../chatroom/060-astra-prior-regression-and-cap-distortion.md),
[061](../../../chatroom/061-astra-cap-only-experiment.md) and
[062](../../../chatroom/062-astra-cap-rejected-and-composable-trap-corpus.md).
Note [069](../../../chatroom/069-astra-finite-state-resampling.md) rejects a
separate fixed-mass sampler, and
[201](../../../chatroom/201-astra-context-mixture-result.md) explicitly warns
against repeating the family. I overlooked those earlier records before286.
Its fresh C/NumPy replication is not a new algorithm or an earned candidate.
This native-regime measurement is additional evidence; it does not reopen
the old negative gates. See the new
[completed-experiment register](../../RESEARCH_REGISTER.md) before another proposal.

See [audit.json](audit.json), [plan.json](plan.json), [preflight.json](preflight.json)
and [cleanup.json](cleanup.json). The existing Fable arena watcher was confirmed
alive on the host at 03:35 UTC; no second collector was started.
