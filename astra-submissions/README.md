# Astra workspace

## Current campaign — November 2, 2026 UTC

The verified public snapshot at 05:28 UTC has **arena v37** active, at 1874.30
Elo and rank 12 among visible rated teams. Fable's
[release note](../chatroom/192-fable-v37-allgames-refit.md) identifies the
all-games move-model/history refresh; v35 remains the historical comparison.
The 100 unique local games score 56W–2D–42L, with a paired interval that includes
equal strength. See the [recovery audit](analysis/v37-recovery-20261101/README.md).
The shared [version map](../fable-submissions/README.md) now records the actual
v36 r4 and v37 archives, separately from Astra's withdrawn local-v36 label.
The [mapping audit](analysis/version-map-20261102/README.md) verifies public
creation times and all 19 C/header files in each archive against its source
commit. The public API does not expose uploaded ZIP checksums.

The latest completed [posterior-objective comparison](analysis/posterior-fit-20261102/README.md)
uses the same 26 coefficients under two training objectives. Direct posterior
training improves held-out hidden-board NLL by 0.02052 nats, below its frozen
0.10 requirement; ordinary move training improves move prediction slightly
but worsens the posterior. The configuration is closed. The earlier
[interaction prior](analysis/interaction-prior-20261102/README.md) improved
average prediction but failed its surprise-capture safeguard.

[Experiment 232](../chatroom/232-astra-posterior-capacity-screen.md) completed the CPU development screen of nonlinear interactions under the posterior
objective. Its gain over the baseline was 0.01696 nats, only 0.00718 beyond
the matched linear posterior control; all minimum-effect requirements failed.
It is closed, with the old test untouched. See the
[verified result](analysis/posterior-capacity-20261102/README.md).

The [feature-equivalence audit](analysis/feature-equivalence-20261102/README.md)
proves some rook moves are indistinguishable to the existing scorer, even
with a known parent. Its modest average lower bound does not establish the
main strength bottleneck; Fable already tested richer spatial features with
level match results. No further prior fit follows from this audit alone.

The [conditional-value expansion candidate](analysis/value-expansion-20261102/README.md)
passes its same-belief replay screen: 11 immediate losses versus 12, with
material events unchanged. The independently verified result advances only
to a frozen 16-game test against exact v37; no release is earned yet.
Its [conditional confirmation design](analysis/value-expansion-confirmation-20261102/README.md)
is prepared and smoke-tested, but cannot launch before the full original pilot
qualifies. It tests both historical references plus a matched Misty control.

Earlier learned-response full-game pilots did not earn promotion: the first
search integration finished 0W–8L against v37; its observable-loss variant
finished 2W–6L. The persistent-response confirmation also failed to establish
an upgrade and retains its technical-failure receipt. See
[search results](analysis/learned-response-search-20261101/README.md) and
[confirmation](analysis/persistent-confirmation-20261102/README.md).
The [intelligence loop](../docs/arena-intelligence-loop.md) records the complete
sequence, including failed ideas and verified corrections.

The latest bounded data refresh added [282 replays and 22,981 move annotations](analysis/arena-refresh-20261102-search/README.md).
These include queen-capture visibility and en-passant supplements, with replay
hashes and independent rules checks. Updating this evidence does not update
the arena model automatically.

**[Astra v36 king-guard candidate](v36-kingguard0001.md): do not promote.** Its
fixed 20-pair test finished 16W–0D–24L against v35; the archive is retained as
an experimental artifact. No new Astra release is recommended.

Fable's highest numbered archive is v37 at this check, so a future Astra
release would use **v38**, subject to the required recheck at packaging and
publication. No number is reserved here. Current coordination is in
[the chatroom](../chatroom/README.md).

The sections below document earlier C++/hybrid work; they do not describe the
current C search architecture or a current submission recommendation.

## Historical v12 release

The earlier conservative trial was **[Astra v12](iamavirus-v12-hybrid.zip)**
(`a5f806d0039f`): arena v10 plus Fable's population-wide material-exposure
term, independently frozen and validated by Astra. Its exact source is in
`candidates/v12/`; the ZIP includes the unchanged Stage A v1 model.
Read the [release gate](analysis/release-v12/README.md) for the measured
improvement in material exposure and the limits of the evidence. The archive
label is not an arena version; the human performs the upload.

## Release numbering

Use the [shared version table](../fable-submissions/README.md) to identify actual arena uploads by artifact hash. Before creating a new Astra release archive, read the highest version in `../fable-submissions/` and use exactly that integer plus one; recheck before publication and never overwrite a historical artifact. The existing Astra **v10/v11 labels are provisional safety candidates**, not arena version numbers or the output of the new 24-hour campaign. v11 was packaged when Fable's highest label was v10; its manifest preserves that fact. Repository checkpoints preserve these earlier artifacts without reserving an arena version. The human performs arena uploads.

Independent analysis and implementation for IAmAVirus, established 2026-10-07 at the user's request. Shared root source files, existing uncommitted work, and `fable-submissions/` are owned by the existing workflow; edit Astra's copy here. Coordination lives in `../chatroom/`.

| Path | Purpose |
|---|---|
| [analysis/release-v12/README.md](analysis/release-v12/README.md) | Frozen source/model provenance, target-opponent replay gate, correctness checks, and timed matches for the historical v12 release. |
| `candidates/v12/`, `v12-origin.json`, `v12-manifest.json` | Pinned release source and immutable ZIP/model checksums, separate from ongoing experiments. |
| [specs/research-plan-24h.md](specs/research-plan-24h.md) | Research-based campaign, responsibilities, resource limits and fail-fast gates. |
| [specs/technical-spec.md](specs/technical-spec.md) | Belief, simulation, evaluation and later training implementation contracts. |
| [analysis/duck-bluqrpex/README.md](analysis/duck-bluqrpex/README.md) | Duck game diagnosis, 32-game snapshot and four-seed archived-belief probe. |
| [analysis/duck-chccdlu3/README.md](analysis/duck-chccdlu3/README.md) | Verified win against Duck v4 and the running public-result monitor. |
| [analysis/capture-recovery/README.md](analysis/capture-recovery/README.md) | Unpackaged A1 capture-recovery prototype, correctness evidence and neutral/negative first pilot. |
| [analysis/visibility-deductions/README.md](analysis/visibility-deductions/README.md) | Fable's pawn deductions ported behind an opt-in switch; four-arm belief probe and paired action results. |
| [analysis/grouped-prediction/README.md](analysis/grouped-prediction/README.md) | Opt-in duplicate-state expansion and uncapped weighted transitions; focused correctness evidence only. |
| `tools/analyze_duck.py`, `tools/probe_belief.cc` | Reproducible offline diagnosis; no live truth input or arena upload. |
| `implementation/` | Working experimental source: earlier Astra v11 shortlist repair plus unpackaged A1 capture recovery. `implementation/RELEASE.md` describes the historical v11 archive, not these later edits. |
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

## Historical C++/hybrid architecture

The C++ runtime enters through `bot.cc`: initialize the arena protocol, consume each observation once, update both particle belief and recurrent history, and answer clock prompts with legal UCI moves. It loads two ONNX graphs for neural/hybrid mode and falls back to cpp if inference is unavailable.

`position.*`, `bitboard.*`, and `observation.*` implement rules, attacks, visibility, and observation-derived moves. Castling needs remembered rights; en passant needs successive views. In this variant a move that leaves the mover's king capturable ends the game immediately, so orthodox check/checkmate semantics must not replace the referee rules.

`belief.*` propagates full-board particles through opponent moves, filters against observations and own-piece constraints, resamples, and recovers when the population collapses. The archive baseline uses the hand-coded opponent prior; today's root additionally has an optional learned prior in `opponent_model.*`.

`engine.*` computes king risk over the particle population, shortlists with alpha-beta search on a representative board, and evaluates candidate/hypothesis matrix cells. `regret.*` solves the resulting finite matrix game and samples a move. This is a local robust decision procedure over sampled boards, not a solved equilibrium of the full imperfect-information game.

Hybrid mode adds neural-policy and low-particle-risk candidates subject to a row budget. Neural danger breaks ties in risk ordering. Neural value is logged; per-square neural belief does not update the particle filter. The interaction between candidate coverage, belief quality, search budget, and the sampled matrix is therefore central to actual playing strength.

The Python learning pipeline uses the C++ rules via `rules_capi.cc` and `learning/rules.py`. `api_client.py` and `ingest.py` collect/cache/validate completed replays. `histories.py` builds separate actor histories and truth-dependent targets; frame t's history predicts the move at frame t+1. `features.py` and the native neural tracker must stay in parity. Public board strings always retain a1-through-h8 order; the model's internal Black rank flip is a separate transform.

`model.py` is a CNN plus GRU with candidate policy, danger, value, and belief heads. `pretrain.py` performs supervised replay learning. `env.py`, `rollouts.py`, and `train_ppo.py` train recurrent PPO on fresh simulated policy trajectories, with same-player returns and recurrent prefix reconstruction. Public replays are not inserted into the PPO likelihood ratio. `export.py` produces ONNX releases; `evaluate.py` and `harness/` cover model, tactical, simulated-match, timed-arena, and measurement checks.

## Historical v12 assessment

The older v5/v8 comparison is confounded by opponent mix. The new Astra v12
trial starts from the later arena-v10 safety fixes and adds population-wide
material exposure. On 37 historical target-opponent seats, moves exposing at
least 300 cp fell from 21 to 12; immediate king losses stayed 20/274. The small
prospective gate also improved exposure without changing king losses. This
supports a trial, not a higher-Elo claim.
The bounded 180+2 comparison against arena v10 finished 2W–2L, with all four
games won by White and no protocol failures. The [match report](analysis/release-v12/real-clock/summary.json)
records the complete result and its small-sample limit.

The separate `implementation/` research tree preserves ordinary-capture
evidence during recovery and offers optional pawn deductions and grouped
prediction. Their belief-quality improvements have not established stronger
play, so those experiments are excluded from v12. Historical Astra v10/v11
ZIPs remain immutable and are not the latest trial candidate.

Read [the detailed concerns sent to Fable](../chatroom/astra-concerns-2026-10-07.md) for verified numbers, code findings, uncertainties, and proposed checks. Several root README/handoff/version statements are historical; current API data and artifact hashes take precedence for this audit.

## Reproduce

```bash
python3 astra-submissions/tools/audit_arena.py --archives fable-submissions
cd astra-submissions/implementation
ORT_HOME=/path/to/onnxruntime-sdk bash build.sh
```

The audit is offline and read-only. The source copy is independently buildable and does not depend on root working-tree engine changes. Compiled artifacts are local; future candidate archives belong under this workspace, not `../fable-submissions/`. Do not claim a source-copy smoke test establishes playing strength.
