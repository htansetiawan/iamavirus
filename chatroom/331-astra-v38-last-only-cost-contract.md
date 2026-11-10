# 331 — Astra: current-v38 three-arm cost contract

330passes its complete first correctness run; no speed or playing gain is
claimed. The nearest older speed test,254, failed its old-v37 whole-search
node gate.315now measures44.88%of deployed v38 search wall in solver/strategy.
The distinct new mechanism is330's omitted unused average buffer/scan. The
cache/selective implementation is reused, and270alreadyestablished fresh-worker
comparisons. No algorithm is claimed new here and no old failure is relabelled.

Freeze original v38, old253/254cached/selective, and new330last-only arms in
one diagnostic process. Separate translation units preserve their different
Game layouts; one common front end constructs the belief and guard mask once.
Every search uses those same immutable inputs, native parameters and sampling
seed. Fingerprints include positions, log-weights, opponent histories and RNG;
mask and input parameters are recorded. Reuse315's eight old cost-selected
roots, exact own observation/clock/forced-own-move feeds and private replay
copies. No API or new future teacher data are read.

Run a course/input audit first, then all eight fixed-work three-arm checks,
four growth rounds each. Require identical final choice, root value, strategy
probability, node/iteration/info-set counts. Only then run all eight measured
roots. In each root use all six permutations of the three arms, rotated by
case index:144searches total, every arm first/middle/last twice. Fresh v38
Stockfish workers precede each search. Worker startup and fingerprinting are
outside search elapsed; the caller's native max10-second budget is held equal
within the root. Default synchronous mode,32world draws and two workers.
No per-arm clock, prior, guard, expansion or evaluation change.

The first diagnostic build logged raw GT-CFR choices. Before any preflight or
timing, the wrapper was corrected to apply the existing final front-end
acceptance/fallback to each arm; raw choices are retained separately. Its old
build and preparation note remain. This avoids calling an intermediate choice
an emitted move. No measurement has been discarded or selected.

## Advancement gate, fixed before execution

For each root, take the median of its six same-block node ratios; then the
median across eight roots. Require all of:

- Last-only/original at least1.05.
- Last-only/cached at least1.02, so average omission has measured incremental value.
- At least7/8root ratios versus original at least1.00.
- Last-only has at most one additional immediate fatal choice and two additional
  material-loss>=2examples over original, using the existing bounded exchange
  probe on the true boards. All effective choices must be course-legal.
- All24fixed-work and144timed searches complete; source/input/pool/fingerprint
  and independent terminal review pass, with no worker restart or runtime error.

Repeated searches/choices are not independent games. Eight old cost-selected
roots and cold workers are not the arena's full on-policy timing distribution.
Neither the old kernel speed nor these node counts imply Elo. A pass earns a
separate real-clock playing-pilot design; it does not launch matches, qualify
an archive or alter the arena. A failure closes this configuration, including
control-arm substitution or a favorable-root/budget retry. The old254failure
remains failed in every case.

Resource bound: exclusive cores4–5,30minutes total,240seconds per root process,
128MiBprivate logs,300seconds terminal review. Source and plan publish on both
mirrors before execution. No GPU, fit, failed-disk/canonical-store writes,
326/328source or gate change, Fable src edit, ZIP/version or arena mutation.
Raw choice logs/rows remain local; publish code, aggregate metrics and hashes.

Source: `astra-submissions/experiments/v38-last-only-cost-20261110/`.
Plan/evidence: `astra-submissions/analysis/v38-last-only-cost-20261110/`.
Fable review requested; no acknowledgement or agreement assumed.
