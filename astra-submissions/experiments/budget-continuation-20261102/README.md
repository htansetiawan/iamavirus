# Continuation budget and target sensitivity

Experiment 242 compares the reconstructed v37 policy at a one-second search
cap and its normal ten-second maximum, retaining its clock-dependent budget.
The same engine/model/table and private prefix are used. A planned normal-budget
repeat with the same seed measures wall-clock variability. It is an experimental
replicate, never a retry of a failed job.

Four prefixes: two hash-selected unused refresh games at ply 32/33, and the
two inspected residual-failure cases updro1eg:94 and g9nruayl:78. The latter
are post-hoc development diagnostics, not an unbiased sample or confirmation.
Each prefix gets cheap, normal and normal-repeat policies, 12 first attempts
total. Arm order rotates by prefix. Each continuation has a 64-new-ply cap;
unfinished games are censored rather than labelled draws. Two exclusive CPU
pairs run separate cases; each job has 1,000 wall seconds, batch cap 7,200.
Any technical failure stops new jobs, while other live jobs finish and retain
their first results. No training or ZIP follows this pilot automatically.

Budget changes can affect both search and timed belief thinning during prefix
reconstruction. This is an end-to-end policy-budget comparison, not isolated
search-depth causality. Recorded clocks and increment remain unchanged.
Normal play uses the v37 production maximum of ten seconds, but restoration
does not recreate a historical process's exact internal search/RNG state.

Report costs, natural outcomes/censoring, first-action agreement, and outcome
differences cheap-vs-normal and normal-vs-repeat. Never discard the repeat,
select a favourable outcome, or turn these few games into an Elo estimate.
Similarity on four prefixes cannot validate cheap labels at population scale.
The result determines data-generation budgeting and exposes target sensitivity;
it is not a model-promotion gate. All source trajectories remain development
data and are excluded from later model confirmation.
