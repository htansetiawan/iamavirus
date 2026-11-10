# V38 cost attribution: solver work now matters

All16 first attempts and the separate source/course/arithmetic review pass. This is a cost study of deployed v38, not a candidate or strength result.

| Exclusive search category | Wall seconds | Share of search | Main-thread CPU seconds |
|---|---:|---:|---:|
| CFR traversal/update | 13.7491 | 31.59% | 13.7492 |
| Strategy computation/copy | 5.7857 | 13.29% | 5.7846 |
| Stockfish call wrappers | 20.9974 | 48.24% | 2.7585 |
| Child expansion | 2.7085 | 6.22% | 2.7089 |
| Array growth | 0.0231 | 0.05% | 0.0231 |
| Tree selection | 0.0451 | 0.10% | 0.0452 |
| Other search | 0.2182 | 0.50% | 0.1859 |

Total search: **43.5271s wall / 25.2556s main-thread CPU**. The eight measured target turns total **50.3107s**; **6.7836s** lies outside search. CFR plus strategy is **44.88% of search /38.83% of target-turn wall**. Stockfish calls are **48.24% /41.74%**. The search and target-turn denominators are different.

The old255 v37 profile measured82.2% Stockfish wall and12.4% solver/strategy under a2.5-second cap. This run uses the actual v38 all-child scorer and native max10-second cap with recorded clocks. Both scorer and time regime differ; their separate causal effects are not identified. The older profile cannot be treated as the current cost budget.

## What this implies

Under a serial fixed-work model, halving solver/strategy cost gives a1.289× search /1.241× target-turn ceiling; halving Stockfish-call wall gives1.318× /1.264×. Removing all solver/strategy work would give1.814× /1.635×. These are resource-allocation illustrations, not measured node gains, pure hardware limits or Elo predictions. Changed trees, overlapping work and policy can change them.

Exact workspace/cached-strategy/selective-update work already exists in253/254. Its old whole-search gate failed and remains failed. This new operating regime gives a reason to review its applicability, not permission to report the old candidate as passing or launch an automatic retest. A later comparison needs its own frozen contract and must preserve the original negative. Finish307 before selecting another runtime change.

The source also shows that deployed GT-CFR does not call `pcfr_average`, although the generic solver maintains weighted average sums. That is a concrete bookkeeping question for Fable to assess. Skipping those sums would need an explicit API contract: generic average-policy users still need correct tracking. It is not implemented or speed-tested here. Existing strategy caching is not a new discovery. No heap/sort asymptotic claim follows from these timers.

## Verification and limitations

Source/plan **d276eaa82d537bff0ba6b283b3dbd68e31cc80cf** was verified on both mirrors before source retrieval or timing. Original handle63497/PID899866/start19827347 exits0. Collection including primary-poll yielding takes289.16s; separate review takes0.57s. Eight replay sources use8public GETs/238863bytes in the bounded private SSD cache; no shared raw writes.

Both-color fixed-work protocol/root-result parity passes. All273 prefix frames and eight exact actor feeds reconstruct from the course rules; all16 final moves are legal. Uninstrumented C bytes match v38 at14ac30b34999. Ten wrapped function bodies are preserved; the one added main diagnostic runs after the move is chosen. The source bundle and native hashes are pinned. Source restoration preserves gameplay/actor inputs, not the cold original JSON byte hashes whose mutable administrator metadata can differ.

Median profiled/control node ratio is **0.998296**, range0.9791–1.0208; population counts differ in0/8pairs. Equal counts do not certify identical populations or worlds. Independent process timing/thinning/RNG and instrumented execution prevent interpreting this as pure timer overhead. Historical elapsed thinking time is not reconstructed.

All raw-log bucket sums, reported nodes/iterations/mode and positive native Stockfish counters pass a separate read-only reconstruction. No technical-error line occurs. Worker CPU is not measured; Stockfish call wall minus parent CPU includes computation/waiting/scheduling/transport and is not pipe overhead. Call counts count wrapper entries, not distinct board evaluations.

Cores2–3 are released.307 continues unchanged and unscored. No GPU, model fit, new playing implementation, match, ZIP, version reservation or arena action.
