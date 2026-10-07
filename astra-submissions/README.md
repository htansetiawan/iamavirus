# Astra workspace

## Release numbering

Before creating a new Astra archive, read the highest version in `../fable-submissions/` and use exactly that integer plus one. Recheck immediately before publication. Never overwrite an existing release. Record the Fable version used in each release manifest. The current target is **v10**, following Fable v9. This task publishes a ZIP to the repository; arena uploads and their server-assigned version numbers are separate.

Independent analysis and implementation for IAmAVirus, established 2026-10-07 at the user's request. Shared root source files, existing uncommitted work, and `fable-submissions/` are owned by the existing workflow; edit Astra's copy here. Coordination lives in `../chatroom/`.

| Path | Purpose |
|---|---|
| `implementation/` | Isolated source/model extraction of `iamavirus-v6-hybrid.zip`, the user's arena-v5 baseline. No strategy changes yet. Its original README is historical. |
| `implementation-origin.json` | ZIP and extracted-file hashes establishing the exact baseline. |
| `tools/audit_arena.py` | Independent offline implementation of version comparison, archive comparison, and terminal hidden-attacker diagnosis. |
| `snapshots/2026-10-07-initial/` | Public standings, 378 game listings, version records, relevant completed replays and diagnostics, with provenance/checksums. |
| `analysis/arena-audit.json` | Reproducible audit output; includes limitations and per-game evidence. |
| `analysis/baseline-smoke.json` | Build/protocol smoke results for the isolated baseline, once generated. |

## Working understanding of the codebase

The C++ runtime enters through `bot.cc`: initialize the arena protocol, consume each observation once, update both particle belief and recurrent history, and answer clock prompts with legal UCI moves. It loads two ONNX graphs for neural/hybrid mode and falls back to cpp if inference is unavailable.

`position.*`, `bitboard.*`, and `observation.*` implement rules, attacks, visibility, and observation-derived moves. Castling needs remembered rights; en passant needs successive views. In this variant a move that leaves the mover's king capturable ends the game immediately, so orthodox check/checkmate semantics must not replace the referee rules.

`belief.*` propagates full-board particles through opponent moves, filters against observations and own-piece constraints, resamples, and recovers when the population collapses. The archive baseline uses the hand-coded opponent prior; today's root additionally has an optional learned prior in `opponent_model.*`.

`engine.*` computes king risk over the particle population, shortlists with alpha-beta search on a representative board, and evaluates candidate/hypothesis matrix cells. `regret.*` solves the resulting finite matrix game and samples a move. This is a local robust decision procedure over sampled boards, not a solved equilibrium of the full imperfect-information game.

Hybrid mode adds neural-policy and low-particle-risk candidates subject to a row budget. Neural danger breaks ties in risk ordering. Neural value is logged; per-square neural belief does not update the particle filter. The interaction between candidate coverage, belief quality, search budget, and the sampled matrix is therefore central to actual playing strength.

The Python learning pipeline uses the C++ rules via `rules_capi.cc` and `learning/rules.py`. `api_client.py` and `ingest.py` collect/cache/validate completed replays. `histories.py` builds separate actor histories and truth-dependent targets; frame t's history predicts the move at frame t+1. `features.py` and the native neural tracker must stay in parity. Public board strings always retain a1-through-h8 order; the model's internal Black rank flip is a separate transform.

`model.py` is a CNN plus GRU with candidate policy, danger, value, and belief heads. `pretrain.py` performs supervised replay learning. `env.py`, `rollouts.py`, and `train_ppo.py` train recurrent PPO on fresh simulated policy trajectories, with same-player returns and recurrent prefix reconstruction. Public replays are not inserted into the PPO likelihood ratio. `export.py` produces ONNX releases; `evaluate.py` and `harness/` cover model, tactical, simulated-match, timed-arena, and measurement checks.

## Current assessment

The raw arena results show v5 ahead of v8, with a substantial opponent-mix difference. The two local hybrid archives have identical pretrained weights. The initial investigation therefore focuses on decision logic and imperfect-information king safety, while treating PPO as a separate experiment. No replacement has passed a strength gate.

Read [the detailed concerns sent to Fable](../chatroom/astra-concerns-2026-10-07.md) for verified numbers, code findings, uncertainties, and proposed checks. Several root README/handoff/version statements are historical; current API data and artifact hashes take precedence for this audit.

## Reproduce

```bash
python3 astra-fable-submissions/tools/audit_arena.py
cd astra-fable-submissions/implementation
ORT_HOME=/path/to/onnxruntime-sdk bash build.sh
```

The audit is offline and read-only. The source copy is independently buildable and does not depend on root working-tree engine changes. Compiled artifacts are local; future candidate archives belong under this workspace, not `../fable-submissions/`. Do not claim a source-copy smoke test establishes playing strength.
