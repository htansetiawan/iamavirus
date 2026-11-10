# Learn quiet-move odds while preserving capture likelihoods

The last all-games refresh changed the existing 28-feature prior by only
0.008 nats, despite much more data (Fable192). A larger interaction model
then gained0.06217 nats overall but failed its surprise-capture safeguard:
capture probabilities regressed (Astra228). Neither result warrants repeating
the same fit or weakening its old gate.

This experiment changes the parameterization. Keep the baseline probability
of every capturing move and the total non-capture mass, and learn only the
conditional distribution **within non-captures**. Here “quiet” means
non-capturing, including quiet checks, castling and non-capturing promotion;
it does not mean observation-silent.

Let `C` and `Q` be the capturing and non-capturing legal moves in a hypothesis.
The deployed prior has logits `z0(a)`. With a learned residual `d(a)`, define

\[
 z'(c)=z_0(c),\quad
 z'(q)=z_0(q)+d(q)+
 \log\sum_{u\in Q}e^{z_0(u)}-
 \log\sum_{u\in Q}e^{z_0(u)+d(u)}.
\]

Then the total unnormalized quiet mass is unchanged, as is the full normalizer.
Thus **every capturing move retains its baseline probability**. Only odds
among non-captures change. An empty/singleton quiet row is exactly unchanged.
The residual is a small linear or sparse quadratic function of existing
features; neither player names nor new history copies are model inputs.

The C kernel keeps the original native global normalizer explicitly. This
preserves capture log-likelihood bits even after the same empirical-history
blend and temperature, for the **same parent and action row**. A later runtime
hook must retain that normalizer; it cannot recompute an approximate new one
and claim the same numerical identity. Unit tests cover all-capture/all-quiet
rows, singletons, extreme logits, zero-model identity and the fixed captures.

This is not a king-safety guarantee. Quiet likelihood changes can alter relative
weights between parent hypotheses, merges, cap survival and later captures.
Sequential posterior, calibration, action and playing gates remain mandatory.
No runtime integration follows from a predictive gain alone.

## Distinction from the old experiments

- 066 learned tactical **group masses** while preserving within-group odds;
  its sequential gate failed in067. This experiment holds the capture/quiet
  partition masses fixed and learns within-quiet odds: the opposite degree
  of freedom. It is not that old gate reused.
- 228 learned unconstrained feature interactions and failed its capture
  safeguard. The new architecture makes true-parent capture likelihood
  invariant by construction. Old228 remains negative; no old subgroup is
  selected as a winner and no old test is relabelled as passed.
- 231/232's posterior-objective fits and201's temporal mixture also remain
  closed. There is no new hidden-history duplication, posterior objective
  retuning, global check bonus or threshold adjustment here.

## Frozen data, fit and rejection rule

The immutable96,210-game generation supplies the cohort inventory. Select
4,000 games fromNov2 06:00–Nov8,400 fromNov8 and400 fromNov9 by salted hash,
across the existing nine reference teams, all outcomes. Complete sequences
are deduplicated across these splits. Training uses up to24 hash-selected
target-team decisions/game; validation and later evaluation retain all such
decisions. These dates are later than the old Nov2 prior study. Existing
taxonomy work may have exposed some later games, so this is a chronological
fit holdout, not pristine prospective confirmation.

Two modes (cheap/full) each fit a constrained linear control and constrained
quadratic model: four fits total, zero residual initialization, one seed,
12epochs, Adam0.03, batch512, ridge0.001. Include epoch0 in selection; choose
each model's epoch only on validation. Lock all choices/hashes before later
test feature extraction. CPU cores0–1, two threads,30-minute maximum; no GPU
or existing service interruption is needed for these small tables.

Keep the earlier predictive bar: full gain>=0.05nats, cheap>=0.03, whole-game
bootstrap95% lower bound>0 for both; quadratic>=0.02 over its matched constrained
linear control in both modes; no all-move regression; at least100 surprise
captures, with native capture likelihoods unchanged. All requirements apply.
A failure closes this fixed configuration without a sweep or test-based refit.
A pass only permits a separately frozen prospective/posterior design.

The original preparation read and hashed all4,800 full replay sources. To avoid
repeating cold lookups through the external drive's228k-entry directory, a
pre-fit input revision embeds the same SHA-matching move sequences from the
existing SSD SQLite cache. The initial plan is retained. No cohort, split,
move selection, model, gate or fit result changes. Nine source replays/677
frames tie reconstructed C states/views to recorded data. The independent
reviewer later reconstructs the400 test sequences with the course referee,
checks scalar model equations, all metrics and game-cluster bootstraps.

The dense stored residual matrices total716float coefficients (2,864bytes);
only upper triangles and selected continuous-feature squares are active.
That is a parameter-storage count, not a measured runtime or strength claim.
No version number or candidate is reserved.

[Prior-work register](RESEARCH_REGISTER.md) ·
[Frozen plan](analysis/capture-fixed-prior-20261110/plan.json) ·
[Source and tests](experiments/capture-fixed-prior-20261110/)

## Result and review boundary — November 10

The [completed study](analysis/capture-fixed-prior-20261110/README.md) learns
a positive full head:0.05120nats over baseline and0.03495 over its linear
control, with unchanged capture likelihoods. All its predictive conditions pass.
The combined configuration still fails: cheap improves0.01858 over linear
instead of the required0.02000. No threshold changes or passing-subgroup
promotion follow. Models and the independent audit are retained.

The constraint has a rules explanation: a victim's own pieces are always
visible, so opponent capture/non-capture is observable as a one-piece loss.
All34,574 test-sequence moves corroborate it. Given identical parents and a
fixed update/RNG schedule, a capture-only observation would admit only
successors whose likelihoods the head preserves. This is a conditional
one-step property, not integrated posterior or king safety. Quiet histories
and clock thinning can still change later beliefs.

The full artifact warrants committee review of a **new prospective full-only
hypothesis**, with cheap unchanged. That would be a changed intervention
requiring later data and a new design, not a reinterpretation of this failed
combined gate. No new trial or runtime integration is started here.
