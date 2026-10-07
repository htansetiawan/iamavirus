# Astra experiment contracts

2026-10-07. Proposed implementation, except the replay analyzer and archived-belief probe already in `tools/`. Implements the [24-hour plan](research-plan-24h.md). Prioritize a small deployable belief improvement; use the remaining specifications to prevent expensive, ambiguous experiments.

## A1: preserve capture evidence through recovery

Input: successive own observations, phase (initial/after-own/after-opponent), our chosen moves, and authoritative own rights/EP state. No replay truth or opponent true moves are available to this component.

Before an opponent update, compare known own occupancy with the new observation. Our pieces cannot become hidden from us. A disappeared own piece ordinarily implies an opponent capturer on that square immediately after the move. For a possible en-passant capture, the capturer instead lands on the EP destination; represent the disjunction until history resolves it. Missing pieces inconsistent with one legal opponent move must be diagnosed, not silently converted into fabricated certainty.

Represent the event as a compact constraint: observed ply, victim square/type, possible capturer landing squares and allowed piece types. Start with conservative type sets narrowed only by known piece census, geometry, previous observations and legal transitions. Do not infer "bishop" from the offline truth in `bluqrpex`. A new observation can further constrain the event.

Recovery must place a compatible enemy on a mandatory capture landing square before scattering remaining pieces; proposals must satisfy current visibility, own-piece state and the event. If no compatible proposal is found, expand/replay recent history or report uncertainty, not erase the event. On subsequent opponent turns the capturer can move: evolve its constraint jointly with legal states. A stale square cannot remain a permanent veto.

Acceptance cases: hidden rook capture; visible capturer; own capture of the threat; disappearance after castling (own phase, not enemy evidence); en passant on both colors; promotion captures; multi-update histories; a capturer legally moving away; incompatible observed histories. In every case validate against the course referee and test that live inputs contain only observations/own actions. Re-run all existing belief, engine and protocol checks.

Expose trace counters: constraints created, satisfied, contradicted, replayed; recovery count; retries; unique boards; successor ceiling hits. On the Duck diagnostic, seeds 3 and 777 must retain f1 occupancy at ply 58 without requiring the unknown capturer to be a bishop. That is a regression test, not the held-out strength test.

## A2: coverage and efficient belief updates

The current 20,000-successor prefix cap favors earlier particles. Instrument truncation before changing it. Deduplicate identical predecessor states with multiplicities and combine successor probability mass using a hash table; verify collisions by comparing full state. State identity includes board, side, castling and EP; draw/history context is additional state for rollout equivalence. Board equality alone is not information-set/history equality.

Retain exact support while it fits a measured budget. Above that budget, use a documented streaming sample or stratified proposal scheme that visits all predecessor groups. Account for inclusion/proposal probabilities and remaining mass; do not call a top-weight heap an unbiased posterior. A checkpoint/backlog can preserve recent support for recovery, subject to a hard memory/time limit.

Separate expected O(1) state lookup from O(M+P) resampling. The alpha-beta move picker currently uses repeated linear selection: O(Bk), worst O(B²). A heap costs O(B+k log B), but may lose when pruning makes k small. Benchmark fixed-node output and time-to-strength before adopting a heap or sort. Priority queues are most justified for bounded frontier expansion, not as a blanket replacement for every linear scan.

## Shared data and evaluation

Consume Fable's `gold/` labels and add Astra labels keyed by `(game_id, arena_version, side, ply, target_schema)`. Save the source replay checksum. Keep actor records (views, phases, own moves, clock) separate from privileged targets (true board, danger, outcome). Never let actual hidden opponent moves or future frames enter an actor feature.

Freeze train/development/test manifests before tuning. Split by game and duplicate complete trajectory; all positions and both colors of a game stay together. Do not group every shared opening into one giant duplicate cluster. Add opponent/version and chronological holdouts. Older weak versions and Duck losses must not dominate merely because they are numerous.

Fix replay sampling: an even global ply stride preferentially samples White. Sample by per-side decision index with equal color coverage, plus separately reported tactical strata. Compare on common histories with common seeds. Report king losses, safe-alternative availability, major-piece exposure, promotion threats missed, known-constraint retention, calibration, collapse and latency. Forced-history results do not predict the new distribution of positions a candidate creates.

Real games use immutable ZIPs, frozen opponent identities, paired color-swapped seeds and 180+2 clocks. Bootstrap or form intervals at the pair/game level, not as if every decision were independent. Preserve the original baseline, the Fable baseline and both single-change candidates. A learned best response gives an attack-strength diagnostic, not exact exploitability of full FoW chess.

## Native batched simulator prototype

Reuse a pinned copy of the existing C++ rules, not another implementation. Proposed C interface:

```c
Pool* pool_create(const Config* config);
int pool_reset(Pool*, const int* ids, const uint64_t* seeds, int count);
int pool_observe(Pool*, ObservationBatch* output);
int pool_legal(Pool*, MoveBatch* packed_moves, OffsetBatch* offsets);
int pool_step(Pool*, const ActionIndexBatch*, StepBatch* output);
int pool_snapshot(Pool*, int id, Snapshot* output);
int pool_restore(Pool*, int id, const Snapshot* snapshot);
void pool_destroy(Pool*);
```

Use contiguous positions and metadata, packed moves and ragged legal-action offsets. No UCI conversion in the hot loop. Each step emits the observations required by *both* trackers and explicit phase/episode identifiers. Terminal observations must precede reset; hidden states reset by episode, not by batch slot. Snapshot includes repetitions, clocks, rights/EP, tracker/history state, RNG and opponent identity; restoring only a board is insufficient for a Monte Carlo probe.

Batch danger labels in native make/unmake loops. Reuse buffers and expose validation errors at the ABI boundary. Start synchronous, complete-game, fixed-policy rollouts so PPO behavior probabilities remain correct. Release Python's GIL during the native batch, use deterministic per-game RNG, and avoid scheduling-dependent random draws. Four CPU threads maximum initially; profile contention with Fable.

Measure pure step rate, observation/feature rate, inference, transfer and learner time separately, then end-to-end learner decisions/s. First gate: identical transitions/targets and at least a 2× reduction in the measured CPU orchestration bottleneck, with at least 30% end-to-end gain if that bottleneck dominates. If not, profile before expanding. 20,000 decisions/s is a stretch target, not assumed.

## Later learner experiments, gated on GPU availability

Keep Fable's supervised model experiment separate from Astra's engine variant. For danger learning, sample enough positive hazards but calibrate on untouched natural-frequency validation data; rank recall at a fixed false-positive rate, not overall accuracy. A high false-positive rate can prevent useful attacks. Do not interpret per-square hidden-piece marginals as a jointly legal board distribution.

A privileged critic has its own recurrent history representation and true-state encoder: `V(h, s, opponent_context)`. Detach its privileged pathway from the actor. Full simulator context may include the frozen opponent's recurrent state and policy identity; a board alone is not always Markov for a history-dependent opponent. Actor invariance tests must show that changing privileged inputs while holding its observation history fixed cannot change policy logits.

Pilot the critic with 64 sampled states × 8 restored continuation rollouts against frozen opponents, then expand toward the memo's 300 × 16 only if useful. Compare history-only, state-only and history+state critics on matched data and Monte Carlo uncertainty. Predeclare explained-variance and move-ranking gains; replay outcome MSE alone is inadequate to diagnose bias.

For an MMD-inspired PPO arm, retain the control's legal mask, recurrent replay, return convention and sampled-action probabilities. Explicitly distinguish KL to the frozen previous policy from KL to the slower magnet policy. Record/reconstruct the **full legal-action distributions** for both references; a sampled old log-probability alone cannot compute these KL terms. Avoid double-counting entropy regularization. Label this an empirical regularized-PPO variant, not a convergent solver by theorem.

Run at most one matched control/variant pilot per available GPU budget before a sweep. Match decision counts and report wall time. Stop for invalid likelihood ratios, repeated KL explosions, collapsing entropy or consistent held-out regression. Expert replay cloning belongs in its own supervised stage, not in an on-policy PPO ratio.

League sampling can use a smoothed payoff table per frozen opponent/version/color, with an uncertainty or under-tested priority and a uniform sampling floor. Limit the initial pool to 6–8 diverse checkpoints. Assess forgotten opponents and cycles; do not require every new checkpoint to beat every prior checkpoint at 60%, which can be impossible in nontransitive games. Only add an exploiter after the basic controlled comparison is stable.

## Observation-aware search stretch

The existing root matrix treats hidden boards as adversarial columns; it is not an information-set solver. Evaluate posterior expectation, an explicit tail-risk term and the current robust matrix as separate arms, not a bundle of constants.

For a small information-set prototype, group nodes by observation **and action history**, preserving recall. States in one information set share one policy. Opponent private histories must be represented or the approximation documented; using their true board as if observed creates strategy fusion. Start depth two/four with bounded candidate sets and common board samples, alpha-beta leaves, and a strict deadline. PCFR+ and a retained expansion tree are later work after this abstraction is tested.

Information value should measure improved future decisions after a possible observation, not just more visible squares. Promotion prevention and hidden-attacker pressure enter those continuation values. Never infer a globally good heuristic from the single true continuation of one lost replay.

## Operations and artifacts

Large paths use `/media/henrytan/seagate/iamavirus/astra/`; confirm the mount before creating data. Write atomic run manifests, checkpoint best/latest, and save RNG/optimizer/dataset/opponent state for resumption. No GPU run starts while the existing service occupies it. Public API access stays read-only and paced across the campaign, with no credential use.

For release, record source ZIP SHA256, model graph hashes, build flags and local binary SHA256 where relevant. The arena compiles its own binary; a local binary hash does not prove arena runtime identity. Use the shared mapping table for arena version and uploaded-name aliases, and the ledger for changes of status. A repository checkpoint may contain provisional artifacts without implying an arena upload or an Elo improvement.
