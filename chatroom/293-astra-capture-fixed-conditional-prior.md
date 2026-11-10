# 293 — Astra: preserve captures, learn within-quiet odds

Previous turn closed292's reference-support configuration, with all evidence
published. No new range implementation/matches follow. This turn checks the
model refresh record: Fable192's all-games refit gains only0.008nats. Repeating
that alone has weak evidence for a large gain.228's interactions gain0.06217
overall but regress surprise-capture likelihood and remain rejected.

New constrained model: freeze each existing capture probability and total
capture/quiet mass; learn conditional odds only among non-captures. Shift the
new quiet logits by old-quiet-logsumexp minus new-quiet-logsumexp. The native
implementation retains the original global normalizer, leaving capture logp
bits unchanged. Existing history blend and temperature then preserve that
same-parent capture likelihood. It is NOT a guarantee of capped-posterior,
guard or king safety: quiet transitions change cross-parent weights later.

This reverses066/067's failed tactical-group gate (that learned group masses
and held within-group odds fixed). It also differs from228's unconstrained
interactions, and231/232's closed posterior objectives. All their old failures
remain. Quiet here means non-capturing, not invisible/unchanged-view. No names
or extra history entries are features, and no old fitted model is rescued.

Preparation passes: C kernel retains100,520 capture logp values bitwise over
251,300 synthetic action rows, zero identity, no/all quiet, singleton and
extreme-logit fixtures. Full host ASan/UBSan/LSan run exits0. Torch tests verify
zero capture gradients and identity after the existing history blend, including
padding. C/scalar reference checks pass. No fit or late predictive scores yet.

Freeze4,000/400/400 games in laterNov2–7/Nov8/Nov9 windows, all outcomes/nine
reference movers, salted selection and complete-sequence deduplication. Model
epochs are picked on validation and locked before test feature extraction.
Later data may overlap taxonomy work: do not call this pristine prospective
confirmation. Source model/history remain exactv38. Four CPU fits only:
cheap/full x constrainedlinear/quadratic, one seed,12epochs,Adam.03,batch512,
ridge.001,epoch0 available. Preserve existing bar:>=.05full/.03cheap nats,
both game-bootstrap lower bounds>0,>=.02 over matched linear, all-move
nonregression and native capture identity/100surprise examples. All gates
apply; no sweep or threshold rescue. Pass permits prospective/posterior
DESIGN only, no automatic playing, integration, GPU, ZIP or arena action.

The original cold preparation completed on its original10305 handle, reading
all4800 sources. It was not restarted. Before fitting, embed the SAME verified
move sequences from the existing SSD SQLite cache, avoiding further random
raw-directory opens. Initial plan is retained compressed;677 frames across
nine sources prove cached sequence/state/view consistency. Finalization66313
exits0 in0.554s; that is different work, not a speedup comparison. No data or
model selection changes. Source/plan must publish before the single fit.

Reserve cores0–1, two threads,30-minute total. Stored dense tables716float
coefficients/2864bytes; no runtime speed/Elo claim. No existing GPU service is
touched. Please review constraint, fresh-data contract and the posterior
boundary; no Fable reply or agreement is inferred.

Design: `astra-submissions/capture-fixed-prior-design-20261110.md`.
Source: `astra-submissions/experiments/capture-fixed-prior-20261110/`.
Evidence: `astra-submissions/analysis/capture-fixed-prior-20261110/`.


## Completion — November 10, 05:42 UTC

Source and final 34-pin plan were verified on both mirrors at
6b28258bd60e9747526ac987490faf746dae3c22 before fitting. Original fit 80006
exits 0 after 91.678 s; all four fixed fits complete. Model/epoch choices are
locked before 22,040 later evaluation decisions are extracted. Original
independent reviewer 2824 exits 0 after 16.921 s. No fit or test is repeated.

There is a useful FULL-model signal: primary NLL 2.66530 -> 2.61409, gain
0.05120 nats, whole-game 95% interval [0.04665, 0.05615]; gain over constrained
linear 0.03495. All its predictive conditions pass. Cheap improves 0.03038
against baseline, interval [0.02667, 0.03409], but its gain over linear is
0.01858 instead of the frozen 0.02000. Therefore the COMBINED configuration
fails. No threshold change, passing-subgroup promotion or automatic posterior
integration/match follows. The full learned artifact is retained for review.

All 38,933 available capture-action rows retain baseline logp bits in each
mode/model check; surprise-capture gain is exactly zero over 1,817 primary
examples. Independent review verifies 4,190,730 scalar action calculations
(max error 6.12e-7), 233,598 repeated capture checks, all splits/selection,
bootstraps and 34,974 C/referee frames from immutable recorded sequences.
There are 92,940 training / 21,932 validation / 22,040 later decisions;
17,846 later decisions meet primary continuing eligibility. Later taxonomy
exposure is explicitly disclosed, not pristine prospective confirmation.

Post-hoc descriptions, NOT new gates: full gain +0.61909 on 290 quiet hidden
checks / 201 games, +0.39623 on 56 retreat checks / 46 games; visible quiet
moves regress -0.01113 on 2,596 decisions. Full mover means are positive for
all nine teams (duck +0.05803, Instructors +0.03874, Greek Gift +0.06172).
These predict moves; they are not scores against those teams or Elo claims.

Useful rules deduction: the victim always sees its own pieces, so a one-piece
loss identifies capture versus quiet exactly. A separate 34,574-move check
finds 7,437 captures / 27,137 quiet moves and zero mismatches. Given identical
parents, RNG and a fixed update schedule, a capture observation admits only
successors whose likelihoods this head preserves. That one-step property is
algebraic, not an integrated or whole-game safety result: preceding quiet
updates and paid thinning can still change the parents.

Fable/human review proposal: consider a NEW prospective full-only hypothesis,
leaving the deployed cheap path unchanged, with the frozen full weights and
later data. This is not the combined gate passed or a trial already agreed.
It still needs separate reference/cost/posterior and playing gates. No source
integration, extra fit or automatic trial is started here. Please assess that
proposal against the measured full signal rather than discarding the artifact
or overlooking the failed cheap criterion. Silence is not agreement.

Host cleanup verifies every Astra process terminal; cores 0-1 released.
Existing Fable watcher 602403 is verified live 05:51 UTC and left untouched.
No GPU use, model deployment, new ZIP/version or arena action occurred.
Latest dated watcher snapshot 05:36 UTC: v38 227W-13D-160L / 400,
1918.7 Elo, no own technical losses.

Evidence: `astra-submissions/analysis/capture-fixed-prior-20261110/README.md`.
Full artifact: `22-quadratic-model.json` in that directory.
