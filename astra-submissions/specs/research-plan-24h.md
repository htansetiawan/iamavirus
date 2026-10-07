# Astra: 24-hour improvement campaign

Date: 2026-10-07. Status: **plan plus completed Duck diagnosis; new strength experiments pending**. The user authorizes implementation, common data and collaboration with Fable, separate variants, and a tested repository ZIP for the human to submit. No arena upload is authorized here. Times below are experiment budgets, not a claim that 24 hours have elapsed.

## Direction

Keep search as the action selector. The largest plausible gain is better reasoning about hidden threats across time: retain evidence, protect the whole position, and value information and promotion threats before the king is trapped. Faster simulation makes learning experiments affordable; a larger PPO run alone does not address the demonstrated failure.

Our [Duck investigation](../analysis/duck-bluqrpex/README.md) establishes a useful split. The game ends in an unavoidable immediate loss, but earlier there is a visible passed pawn we could capture and hidden pressure on pieces away from the move destination. A four-seed replay of the archived belief code also demonstrates that recovery discards a known capture-square occupancy constraint.

## Research already done by Fable

Read and use the [research memo](../../reports/Deep%20RL%20for%20Fog%20of%20War%20chess.md), its [policy-gradient](../../research_notes/Deep%20RL%20for%20Fog%20of%20War%20chess/policy_gradient_methods.md), [equilibrium](../../research_notes/Deep%20RL%20for%20Fog%20of%20War%20chess/equilibrium_self_play.md), [search/belief](../../research_notes/Deep%20RL%20for%20Fog%20of%20War%20chess/search_belief_offline.md) and [systems](../../research_notes/Deep%20RL%20for%20Fog%20of%20War%20chess/systems_and_scaling.md) notes, plus `DESIGN.md` and `HANDOFF.md`. These inform the plan; the following qualifications matter:

- [Obscuro](https://arxiv.org/html/2506.01242v2) motivates stronger belief support and sampled information-set search. Transferring its design requires the course rules, not assuming chess.com and this referee are identical. A complete retained CFR tree is beyond a reliable one-day promise.
- [Magnetic Mirror Descent](https://arxiv.org/abs/2206.05825) motivates a regularized learner experiment. Adding a KL term to deep, clipped, recurrent PPO against a changing league does not inherit the paper's convergence guarantees. Preserve a matched PPO control.
- [Asymmetric actor-critic analysis](https://arxiv.org/abs/2105.11674) motivates a history-plus-state critic. Our existing value head already receives recurrent observation history. Its poor replay MSE does not establish a state-only critic bias; test credit assignment, targets and opponent nonstationarity separately.
- [A large imperfect-information policy-gradient comparison](https://arxiv.org/abs/2502.08938) supports evaluating competent policy-gradient baselines rather than ruling out the family categorically.
- The current simulator already uses native rules. The prospective gain is batching orchestration, features and labels, not replacing an all-Python chess engine.
- The earlier learned opponent prior improved move likelihood without improving king-loss frequency. Reuse that negative result; likelihood alone is not a release gate.
- At 800 decisions/s, 100 million decisions takes **34.7 hours of generation alone**. Three such runs plus best-response training cannot fit this campaign. The memo's 20,000 decisions/s target is an aspiration to measure, not a capacity assumption.

## Two variants and common evidence

| Track | Owner / proposed responsibility | Isolated change |
|---|---|---|
| A: evidence preservation | Astra, independent source under `astra-submissions/` | Capture-event constraints during recovery; then successor coverage/deduplication if profiling supports it. Preserve opponent-motion uncertainty. |
| B: tactical scoring | Fable, already underway | Population-wide exposure instead of destination-only material risk; its promotion/retention and model experiments remain separate toggles. |
| Shared infrastructure | Astra offers native batch simulator prototype; Fable owns current gold curation and supervised model training | Same referee, cached games, artifact hashes, locked evaluation manifest and reporting conventions. No duplicate GPU run. |
| Combined candidate | Joint, only after A and B are measured separately | A+B, and optionally a new model as a distinct additional ablation. |

The split was proposed in `chatroom/ledger.jsonl`; read Fable's response before overlapping its per-particle last-mover prior work. Hard capture constraints and a heuristic persistence prior serve different roles. This document does not assert Fable accepted work it has not acknowledged.

## Schedule and decisions

| Budget from campaign checkpoint | Work | Exit condition |
|---|---|---|
| 0–3 hours | Finish provenance, Duck report, support probes, baseline manifests and both-color sampling. Index Fable's gold data. | Every headline has reproducible evidence; failures separated into unavoidable terminal states, selection failures and history-constraint violations. |
| 3–8 hours | Implement A1 capture-constrained recovery in Astra's fork, with adversarial EP/castling/capture tests. Review Fable's exposure scoring. | Zero new referee/protocol errors; known hard constraints retained; measured CPU cost. Stop or revise on the first correctness failure. |
| 8–13 hours | A1 held-out replay comparison; A2 successor dedup/coverage only if cap hits or duplicate work justify it. Start small matched real-clock games for A and B. | Reject clear regressions; keep the simplest surviving change. Replay survival alone is not a strength result. |
| 13–19 hours | Native batch simulator vertical slice and profile; continue paired games in a reserved CPU lane. Optional model evaluation only when Fable's model is ready. | Demonstrate parity and actual end-to-end improvement before expanding simulator scope. No GPU is required for this phase. |
| 19–24 hours | Test the best separate and combined candidates, validate clean ZIP build, protocol, clocks and runtime memory; prepare human upload recommendation. | Report W/D/L and game-pair uncertainty. Publish an experimental candidate if evidence is promising but not decisive; keep the known baseline available. |

If 24 hours leaves an inconclusive strength comparison, say so. A 48-hour extension can deepen the matches or investigate the surviving training idea; it is not an excuse to label noise a breakthrough. A +100 Elo ambition corresponds to about 64% expected score against a fixed equal starting reference under a simple Elo model, not a promise about the live arena's mixed schedule.

## Fail-fast gates

1. **Correctness:** any illegal move, observation mismatch, lost hard constraint, truth-to-actor leakage or new protocol failure stops the variant.
2. **Mechanism:** recover the demonstrated capture fact across seeds and improve calibration/coverage on games not used to design the fix. Do not optimize only `bluqrpex`.
3. **Cost:** compare both fixed-node quality and real-clock behavior. A better estimator that spends the move budget before searching may lose games.
4. **Strength pilot:** use at least 20 color-swapped seed pairs as a screening stage; do not promote on its point estimate alone. Reject an obvious loss trend, timeouts or major opponent-specific collapse.
5. **Confirmation:** aim for at least 200 pairs for the strongest finalist if observed game time permits. Predeclare the evaluation set, analyze by paired seed/game, and report uncertainty and total wall time. Do not manufacture certainty when the clock budget only permits fewer games.

No Duck executable is available through the public API. Completed replays support diagnosis and offline tests, not faithful local games against Duck. Local baselines, Fable variants, and frozen league opponents are proxies until the human submits and new arena games arrive.

## Data and hardware

Use `gold/` and the existing cached replay collection first. Add targeted recent losses, wins, draws and strong-opponent examples only when they cover a missing failure family. Public requests remain sequential, at most one per second, with pages of 100 and bounded Retry-After-aware backoff. At that pace 5,000 uncached replays take at least 83 minutes, excluding listing/retries; measure value before collecting them.

Store large Astra datasets, checkpoints and logs at **`/media/henrytan/seagate/iamavirus/astra/`**, as the user authorized. The mount had approximately 1.2 TB free; the root disk only about 11 GB. Check that the mount is present before writing, set an initial 50 GB campaign cap, and retain at least 5 GB free on root. Keep compressed records and best/latest checkpoints, not every expanded tensor batch. Never move or delete Fable's artifacts.

This host has eight CPU cores and about 31 GiB RAM. Coordinate CPU lanes with Fable; begin with two Astra workers, then increase only after checking contention. Arena acceptance remains the course's two-core/4-GiB setting. **Leave the occupied vLLM GPU service running.** Do not interpret available residual VRAM as permission to compete with it. Training begins only once the GPU is free and the CPU/data gates justify it.

## Recording and release

Every run records source/archive/model hashes, dataset manifest, opponent IDs, seeds, clocks, core allocation, command, elapsed time and peak memory. Append findings, ownership and corrections to the [ledger](../../chatroom/ledger.jsonl), linking detailed notes. A finding changes our next experiment only when its evidence supports it.

Use the shared [arena/archive table](../../fable-submissions/README.md) as the mapping authority. Arena version numbers are assigned by upload; build labels are not evidence of an upload. New Astra artifact labels still check the user's Fable+1 requirement at packaging and publication, with collisions reported rather than overwriting historical artifacts. Existing provisional v10/v11 ZIPs are earlier safety experiments, not the output of this new 24-hour campaign.

The implementation contracts and later training experiments are in [technical-spec.md](technical-spec.md).
