# Astra workspace

## Release numbering

Use the [shared version table](../fable-submissions/README.md) to identify actual arena uploads by artifact hash. Before creating a new Astra release archive, read the highest version in `../fable-submissions/` and use exactly that integer plus one; recheck before publication and never overwrite a historical artifact. The existing Astra **v10/v11 labels are provisional safety candidates**, not arena version numbers or the output of the new 24-hour campaign. v11 was packaged when Fable's highest label was v10; its manifest preserves that fact. Repository checkpoints preserve these earlier artifacts without reserving an arena version. The human performs arena uploads.

Independent analysis and implementation for IAmAVirus, established 2026-10-07 at the user's request. Shared root source files, existing uncommitted work, and `fable-submissions/` are owned by the existing workflow; edit Astra's copy here. Coordination lives in `../chatroom/`.

| Path | Purpose |
|---|---|
| [specs/research-plan-24h.md](specs/research-plan-24h.md) | Research-based campaign, responsibilities, resource limits and fail-fast gates. |
| [specs/technical-spec.md](specs/technical-spec.md) | Belief, simulation, evaluation and later training implementation contracts. |
| [analysis/duck-bluqrpex/README.md](analysis/duck-bluqrpex/README.md) | Duck game diagnosis, 32-game snapshot and four-seed archived-belief probe. |
| `tools/analyze_duck.py`, `tools/probe_belief.cc` | Reproducible offline diagnosis; no live truth input or arena upload. |
| `implementation/` | Astra v11 candidate fork of the user's arena-v5 baseline. See `implementation/RELEASE.md`; the original README inside the source copy is historical. |
| `implementation-origin.json` | ZIP and extracted-file hashes establishing the exact baseline. |
| `tools/audit_arena.py` | Independent offline implementation of version comparison, archive comparison, and terminal hidden-attacker diagnosis. |
| `snapshots/2026-10-07-initial/` | Public standings, 378 game listings, version records, relevant completed replays and diagnostics, with provenance/checksums. |
| `analysis/arena-audit.json` | Reproducible audit output; includes limitations and per-game evidence. |
| `analysis/baseline-smoke.json` | Build/protocol smoke results for the isolated baseline, once generated. |
| `iamavirus-v11-hybrid.zip` | Independently modified Astra candidate, following Fable v10. Repository publication only. |
| `v11-manifest.json` | Archive checksum, source/model hashes, and version provenance. |
| `analysis/v10-tests.log` | Nine unit suites and differential rules validation. |
| `analysis/v10-hybrid-corpus/summary.json` | Node-limited baseline/candidate comparison with the actual hybrid model. |
| `analysis/v10-referee/summary.json` | Complete color-swapped protocol smoke games. |

## Working understanding of the codebase

The C++ runtime enters through `bot.cc`: initialize the arena protocol, consume each observation once, update both particle belief and recurrent history, and answer clock prompts with legal UCI moves. It loads two ONNX graphs for neural/hybrid mode and falls back to cpp if inference is unavailable.

`position.*`, `bitboard.*`, and `observation.*` implement rules, attacks, visibility, and observation-derived moves. Castling needs remembered rights; en passant needs successive views. In this variant a move that leaves the mover's king capturable ends the game immediately, so orthodox check/checkmate semantics must not replace the referee rules.

`belief.*` propagates full-board particles through opponent moves, filters against observations and own-piece constraints, resamples, and recovers when the population collapses. The archive baseline uses the hand-coded opponent prior; today's root additionally has an optional learned prior in `opponent_model.*`.

`engine.*` computes king risk over the particle population, shortlists with alpha-beta search on a representative board, and evaluates candidate/hypothesis matrix cells. `regret.*` solves the resulting finite matrix game and samples a move. This is a local robust decision procedure over sampled boards, not a solved equilibrium of the full imperfect-information game.

Hybrid mode adds neural-policy and low-particle-risk candidates subject to a row budget. Neural danger breaks ties in risk ordering. Neural value is logged; per-square neural belief does not update the particle filter. The interaction between candidate coverage, belief quality, search budget, and the sampled matrix is therefore central to actual playing strength.

The Python learning pipeline uses the C++ rules via `rules_capi.cc` and `learning/rules.py`. `api_client.py` and `ingest.py` collect/cache/validate completed replays. `histories.py` builds separate actor histories and truth-dependent targets; frame t's history predicts the move at frame t+1. `features.py` and the native neural tracker must stay in parity. Public board strings always retain a1-through-h8 order; the model's internal Black rank flip is a separate transform.

`model.py` is a CNN plus GRU with candidate policy, danger, value, and belief heads. `pretrain.py` performs supervised replay learning. `env.py`, `rollouts.py`, and `train_ppo.py` train recurrent PPO on fresh simulated policy trajectories, with same-player returns and recurrent prefix reconstruction. Public replays are not inserted into the PPO likelihood ratio. `export.py` produces ONNX releases; `evaluate.py` and `harness/` cover model, tactical, simulated-match, timed-arena, and measurement checks.

## Current assessment

The raw arena results show v5 ahead of v8, with a substantial opponent-mix difference. The two local hybrid archives have identical pretrained weights. Astra v11 implements one isolated final-shortlist safety repair using the same pretrained model. No replacement has passed a playing-strength gate; v11 is an experimental trial candidate.

Read [the detailed concerns sent to Fable](../chatroom/astra-concerns-2026-10-07.md) for verified numbers, code findings, uncertainties, and proposed checks. Several root README/handoff/version statements are historical; current API data and artifact hashes take precedence for this audit.

## Reproduce

```bash
python3 astra-submissions/tools/audit_arena.py --archives fable-submissions
cd astra-submissions/implementation
ORT_HOME=/path/to/onnxruntime-sdk bash build.sh
```

The audit is offline and read-only. The source copy is independently buildable and does not depend on root working-tree engine changes. Compiled artifacts are local; future candidate archives belong under this workspace, not `../fable-submissions/`. Do not claim a source-copy smoke test establishes playing strength.
