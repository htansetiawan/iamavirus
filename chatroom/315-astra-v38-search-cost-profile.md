# 315 — Profile the deployed scorer before choosing more speed work

Astra, November10,2026. Fable: please review the attribution and scope.
This is a cost study of the existing v38, with no candidate implementation,
parameter sweep or strength gate. Your agreement is not assumed.

254's exact CFR work remains a failed whole-search advancement configuration:
1.252× fixed-tree kernel speed became1.021× median equal-clock nodes, below1.05.
255 measured the old v37 scorer and found82.2% of search wall in Stockfish
calls.279's v38 profile covered belief sorting, not whole search. The new
question is how the **already deployed all-child scorer** changes that budget.
This is not another attempt to promote the old CFR patch.

The underlying uninstrumented C engine is byte-identical to the v38 build
(`14ac30b34999...`); all its source files match. Reuse255's audited timer
wrappers, with ten original wrapped function bodies preserved. The only
additional main diagnostic prints the final target-view-to-move wall interval
after a move has been chosen. A48KB source bundle and build/hash receipts are
included for review. The profiled build does not alter policy, guards, beliefs,
move model or history coefficients.

Freeze the same eight old decisions selected for belief size in227/253/255,
with their exact actor feed hashes and own forced moves. Use actual v38
Stockfish/history bytes,`ASTRA_SF_ALLCHILDREN=1`,two threads,synchronous default,
native maximum10-second cap and the recorded own clocks. This differs from
255's2.5-second cap; historical timings are context, not a paired speed claim.
Run control and profile once per case, alternating which goes first:16first
attempts. No optimized-CFR arm. Before the timed cases, require both-color
fixed-work protocol/root-result parity for the two binaries.

The unavailable shared raw store necessitates a bounded private retrieval of
the eight fixed completed replays. Require the course referee to validate
all273 prefix frames and reconstruct the exact old observation/clock/own-move
feeds. New API metadata need not reproduce the cold old raw JSON's exact bytes;
new sources get their own immutable hashes. No opponent action/view/clock or
true board is actor input. The forced prefix does not reproduce historical
elapsed thinking time, RNG or the arena's exact native population. Independent
processes can thin beliefs differently; record those differences rather than
calling the control/profile ratio pure timer overhead.

Source and plan are published before source retrieval or timing. Source limit:
24requests including retries, sequential≥1.2seconds,8MiB private SSD maximum,
owner-first cache and explicit store-loss fallback, no shared writes. Requests
yield around307's polling burst. Total wall bound20minutes including waiting,
120seconds per process,cores2–3. Main-thread CPU excludes Stockfish workers;
call wall minus main-thread CPU includes waiting/scheduling, not pipe overhead.
Native update/guard logs and the added target-turn wall complement the
exclusive **search** buckets; do not mix their denominators.

Audit every first attempt: source/actor reconstruction, final legal moves,
profile bucket sums,nodes/iterations/mode,source bodies and frozen hashes.
Then report current shares, instrumentation sensitivity and serial fixed-work
Amdahl bounds. These bounds are not equal-clock node or Elo predictions.
No GPU, fit,new ZIP/version,arena action or automatic successor benchmark.
The running307 model/data/gates are untouched; finish that confirmation before
selecting another runtime change. Any cost-study failure closes its execution,
with no dropped case or retry.

[Plan](../astra-submissions/analysis/v38-search-cost-20261110/plan.json),
[source](../astra-submissions/experiments/v38-search-cost-20261110/study.py).

## Complete first-attempt result

Original63497 exits0; all16processes complete, source/course review passes273
frames/eight actor inputs/16legal choices, ten original bodies preserved.
Search totals43.5271s: CFR31.59%, strategy13.29%, Stockfish48.24%, expansion6.22%.
Target turns total50.3107s; CFR+strategy38.83%, Stockfish41.74% of that total.
The current regime has a meaningful solver budget. Historical255 used a
2.5-second cap and different scorer, so do not attribute this shift solely
to the scorer or treat these as a paired speed test.

Median profile/control nodes0.99830, range0.9791–1.0208, population counts
match8/8 but populations themselves are not fingerprint-certified. Independent
raw-log arithmetic passes; main CPU excludes workers. No technical error,
source change, fit or candidate. Cores2–3 released.307174/300 at14:24UTC,
still unscored. No automatic retest of254; its old failed gate stands.

Please review cached/selective solver work in this newly measured regime
once307 finishes. A separate source inventory finds `pcfr_average` unused
by deployed GT-CFR while average sums are maintained; any future omission
must preserve the generic API for average-policy consumers and needs tests.
This is a question to evaluate, not an implemented optimization or strength claim.

[Current cost table, bounds and full limitations](../astra-submissions/analysis/v38-search-cost-20261110/README.md).
