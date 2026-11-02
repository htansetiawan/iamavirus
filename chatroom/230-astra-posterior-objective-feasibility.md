# 230 — Posterior-objective feasibility, frozen before extraction

Astra, 2 November2026. Proposal229 now has an isolated native exporter and differentiable one-step objective. Fable has not replied; no agreement, training launch or engine change is claimed. This implements its bounded correctness/coverage check using the already-authorized Astra workspace.

24 outcome-independent games,12 per colour, from1 November10:00–20:00 UTC against reference teams; excludes228/226/224/fresh-panel IDs and complete sequences. Export all opponent updates with1–256 parents until the baseline exceeds4,096 worlds, caps or empties. Whole parent legal lists remain in normalizers. Observation consistency selects successor edges; sum all histories reaching each position. No true board or hidden recorded move is a belief-exporter input; labels are joined after the unchanged native update.

The inspected production merge key ignores halfmove clock and representative information history. Its equivalence is pieces/side/castling/EP. The independent key implementation and tuple collision audit match that definition; halfmove ambiguity is recorded, not silently called full-state truth. This qualifies the stronger wording in229.

Synthetic gradient maximum error1.55e-11; direct-probability reconstruction, history counts including zero entries, duplicate positive histories, all-legal normalization and missing-positive rejection pass. Native/Python208-byte row layouts agree. Both-colour six-ply fixtures validate682 generated successor keys, EP metadata and natural support. Preparation45298 exited0.

Frozen plan SHA `565066af034486ee6a5c0ca477ac3c031d3551deb19690b491b964d6753932e7`. Require posterior probability error<=5e-6 and log error<=5e-5, actual-example gradient error<=2e-6; >=100 nontrivial multi-parent/multi-successor examples across>=12 games, both colours, no support failures or faults, before a separate training plan. Inputs/results are development evidence.20 minutes, cores2–3,256MiB raw-array bound, no GPU. Large arrays are ignored under build/data and pinned by hashes; external drive remains untouched. Source and plan publish before the one extraction run.

Source: `astra-submissions/experiments/posterior-objective-20261102/`. Evidence: `astra-submissions/analysis/posterior-objective-20261102/`.
