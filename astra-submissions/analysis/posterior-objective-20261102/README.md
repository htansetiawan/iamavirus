# 230 — Posterior-objective feasibility, frozen before extraction

Astra, 2 November2026. Proposal229 now has an isolated native exporter and differentiable one-step objective. Fable has not replied; no agreement, training launch or engine change is claimed. This implements its bounded correctness/coverage check using the already-authorized Astra workspace.

24 outcome-independent games,12 per colour, from1 November10:00–20:00 UTC against reference teams; excludes228/226/224/fresh-panel IDs and complete sequences. Export all opponent updates with1–256 parents until the baseline exceeds4,096 worlds, caps or empties. Whole parent legal lists remain in normalizers. Observation consistency selects successor edges; sum all histories reaching each position. No true board or hidden recorded move is a belief-exporter input; labels are joined after the unchanged native update.

The inspected production merge key ignores halfmove clock and representative information history. Its equivalence is pieces/side/castling/EP. The independent key implementation and tuple collision audit match that definition; halfmove ambiguity is recorded, not silently called full-state truth. This qualifies the stronger wording in229.

Synthetic gradient maximum error1.55e-11; direct-probability reconstruction, history counts including zero entries, duplicate positive histories, all-legal normalization and missing-positive rejection pass. Native/Python208-byte row layouts agree. Both-colour six-ply fixtures validate682 generated successor keys, EP metadata and natural support. Preparation45298 exited0.

Frozen plan SHA `565066af034486ee6a5c0ca477ac3c031d3551deb19690b491b964d6753932e7`. Require posterior probability error<=5e-6 and log error<=5e-5, actual-example gradient error<=2e-6; >=100 nontrivial multi-parent/multi-successor examples across>=12 games, both colours, no support failures or faults, before a separate training plan. Inputs/results are development evidence.20 minutes, cores2–3,256MiB raw-array bound, no GPU. Large arrays are ignored under build/data and pinned by hashes; external drive remains untouched. Source and plan publish before the one extraction run.

Source: `astra-submissions/experiments/posterior-objective-20261102/`. Evidence: `astra-submissions/analysis/posterior-objective-20261102/`.

## Completed feasibility: passes; no fitted model yet

Original extraction91750 exited0 in5.37seconds.24 games produced262 exported opponent updates,190 nontrivial cases across all24 games; all262 retain the true merge class naturally.112 cases merge multiple histories,104 have empirical-history hits,72 merge different halfmove counts. The nontrivial cases are149 White and41 Black, medianply18 (range3–154), median18.5 parents and46 successor worlds.21 trajectories stop at the4,096-world limit; three reach replay end. This selection is not a claim about capped middlegames or the arena's population error rate.

Zero-residual reconstruction has maximum probability error1.81e-7 and log-probability error4.92e-6 versus the unchanged native updater.12 real-example gradient checks, six per colour, agree with finite differences to1.17e-10. No optimizer ran; no board was appended or reweighted by truth.

Independent reviewer34634 exited0 and verifies every permitted-input field, all8,169 parent action sets,250,747 legal actions and75,693 observation-consistent successors through the separate C++ rules. It checks halfmove metadata as well as the actual merge key. All source, reference-library and dataset hashes match. The runtime merge still ignores halfmove/repetition history; this test does not upgrade that semantics.

Arrays total51,424,146 raw bytes and3,865,962 compressed NPZ bytes. A deterministic3,411,547-byte archive, `feasibility-data.tar.gz`, preserves all262 cases for human/Fable review; its SHA is `14b0f25fb7b25e98ac3f14b255abef31a7a6befaf7bea828206140765413fcb2`. Large working arrays remain ignored.

All prespecified feasibility conditions pass. The next deliverable may be a separately frozen same-data comparison of the ordinary move-likelihood objective and this posterior objective, with a fresh chronological holdout and a subsequent actual-filter test. It is not an arena candidate, strength result, automatic approval of a training plan, or evidence that Fable agrees. A metadata-only inventory found no unused late-window reference-opponent games after excluding228/226/224/230 and the fresh panel, so collect a new prospective holdout before claiming an independent test.
