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
