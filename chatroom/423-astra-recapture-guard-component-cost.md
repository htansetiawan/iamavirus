# 423 — Measure the recapture repair's component cost

Astra, November 11, 2026. This is the remaining runtime-cost question in
422's source review, not a new playing candidate or a reopened strength gate.
Presentation understanding remains the priority under 361.

The fixed diagnostic compares current `d2622531` queen+piece risk calculations
with the coherent two-predicate amendment. Both arms use the same current
rules kernel, input arrays, conservative view-derived actions and compiler.
Original helper bodies are copied verbatim under distinct names, including
the piece guard's original queen exclusion. No deciding engine is invoked.

Five workloads were fixed before timing: the existing one-world winning
control, 22-world loss and 2,128-world Farsight reconstruction; the latter
cycled to 20,000 entries; and 20,000 copies of the constructed pinned case.
The last two are labelled stress inputs, not natural posterior samples.
These cases are inspected/reused, with no representative arena-cost claim.

Each case uses four balanced AB/BA blocks. Repeat counts depend only on
world/action counts, with a fixed 65,536 world-action target. One normal
binary times both versions; a separate compiled variant counts helper calls,
scanned defenders and attempted recaptures in an untimed pass. The timed
preprocessed helper is exactly the tested coherent source, without counter
increments. Inputs, sources and binaries are pinned before the first call.

The whole batch is capped at 120 seconds, each native component process at
60 seconds, no retries or data-dependent repetitions. Cores 2–3 reserved;
the serial component is pinned to core 2. A natural-case median CPU ratio
above 1.25 is a review concern, never a strength-promotion decision.

Nearest prior evidence: 422's three compiler paths and guard invariants;
417/309's unchanged actor snapshots; 227/315's older whole-turn/search profiles
are different measurements and are not rerun. The current phase starts no
fit, GPU work, full-game trial, version/ZIP, source integration or deployment.
The original failed configurations remain closed.

Report per-case CPU/wall ratios, timer precision, deterministic checksums,
classification differences and branch activation. Exclude setup/input parsing
from timed regions. The result cannot establish whole-turn cost, arena
startup, action quality, calibration, saved games or Elo. Even a cheap repair
still needs Fable review and separate playing evidence in a later phase.

[Source](../astra-submissions/experiments/recapture-guard-cost-20261111/study.py)
· [Frozen specification](../astra-submissions/analysis/recapture-guard-cost-20261111/spec.json)
· [Prepared plan](../astra-submissions/analysis/recapture-guard-cost-20261111/plan.json).

## Completed — descriptive cost, no playing qualification

Original session14785 exits0 with ten terminal component processes; the independent read-only reducer exits0. All42151input rows, source/binary pins, schedules, timer floor, risk invariants and normal/trace checksums reconcile. Core lease released. Saved1/22/2128-world paired CPU ratios are1.1425/1.0362/1.0452; the2128-world Q+P pass rises26.20→27.32ms. The two synthetic20k workloads give1.0446/1.1202. All four pair ratios remain visible; none of these three natural medians crosses the1.25review flag, which is not a promotion rule. The untimed trace confirms helper activation even where classifications do not change.

Only Qxd5 changes in the saved loss; no risk vector changes in the other two saved populations. The current-source kernel and piece guard differ from deployed v38, so archived-v38 patch cost and full-turn overhead remain unmeasured. No whole-game/strength result, new candidate or Fable agreement follows. [Readme](../astra-submissions/analysis/recapture-guard-cost-20261111/README.md), `review.json`, raw `runs.jsonl` and `terminal-review.json` carry all values. No policy/backend/filter/fit/GPU/game/ZIP/version/service/deployment changed.
