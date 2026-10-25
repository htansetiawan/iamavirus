# 095 — Astra: replay feature corpus and held-out prior refit pilot

2026-10-25. I added a C feature oracle tied to the archived v35 `board.c` and
`movemodel.c`, plus Python replay export and conditional-logit evaluation
tools. The oracle compiled cleanly and passed an initial-position smoke case:
20 legal candidates, with the observed `e2e4` move present.

The exporter reconstructed castling rights and en-passant state from true
replay frames and checked every labeled move against the archived engine's
legal-move generator. On the cached archive, filtered to the named top teams
and excluding IAmAVirus decisions, it yielded 100 usable games, 3,746
positions, and 118,721 legal candidate moves. The two appended features fired
on 656 candidates (`MM_CHECK_UNSEEN`) and 6,104 candidates
(`MM_THREAT_UNSEEN`). Cached replay dates stop at 2026-10-11, and only 100
games were available after filtering, so this cannot represent the current
field or establish strength.

The chronological, game-disjoint split fit is currently running on CPU. It
compares the frozen v35 prior, a fit of only the two omitted hidden-threat
coefficients, and a regularized full refit. GPU access remains unavailable
(`nvidia-smi` cannot reach the driver); this small conditional-logit fit does
not need a GPU. The eight-game paired strict-king-guard self-play comparison
is also still running. No coefficients, runtime defaults, or ZIP were changed.

Next gate: judge held-out per-position NLL, top-1 and hidden-threat slices;
then replay any learned candidate through the exact sequential belief update
and referee continuations. Do not promote a model from this 100-game pilot.

Artifacts: `astra-submissions/tools/move_model_features_probe.c`,
`astra-submissions/tools/extract_move_model_dataset.py`,
`astra-submissions/tools/fit_conditional_prior.py`; extracted candidate corpus
is stored on the user-authorized Seagate volume at
`/media/henrytan/seagate1/iamavirus/move-model-20261024/`.
