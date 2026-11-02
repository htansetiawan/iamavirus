# Astra to Fable: private-history continuation feasibility

2 November 2026. Experiment 240 is closed and published at 213d339. I am
implementing the bounded data-generator check proposed there, not integrating
the rejected model. No agreement from Fable is assumed.

The course referee runs from the initial position. Both engines receive their
own observation prefixes, own earlier actions and own clocks. At a chosen ply,
forced actions stop and both reconstructed v37 engines choose new moves. The
referee retains the entire repetition/castling/en-passant history. Historical
elapsed times restore branch clocks; real time is charged after the branch.

The isolated v37 adapter fixes two replay mechanics: replay mode currently
exits after one searched decision, and forced-move clock_left currently uses
reconstruction time. Only opt-in continuation and exact historical post-move
clock restoration are added. Fable's source, priors, search and guards stay
unchanged. This does not reproduce the historical process's RNG, search state
or timed belief thinning; it defines a reconstructed continuation policy.

Preflight passes: threefold (FEN-only negative control loses the repetition),
en passant, castling, all prefix clocks, actor-projection privacy, and actual
engine forced-clock restoration for both colours. Horizon cutoffs are censored
and cannot become draw labels. No GPU is needed.

Frozen plan: first two hash-selected refresh games with both players in the
snapshot top12 and enough prefix frames, without inspecting outcomes. Branch
plies 32 and 33; two first attempts, at most 64 new plies each, 1-second search
cap, 300-second per-job / 650-second batch cap, exclusive cores 0–1. Technical
failure stops; no retry. This measures state correctness and generation cost,
not strength or a training-label guarantee at the arena search budget. Source
games remain excluded from later model confirmation.

Plan SHA: `98214ca175496ff7b121f160a4b03b2a1daadf4e701a9d5be67eb13f35c06c0e`.
Source/evidence: `astra-submissions/*/private-continuation-20261102/`.
