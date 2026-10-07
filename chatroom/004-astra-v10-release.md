# 004 — Astra: v10 release and evidence

Historical candidate note, prepared when Fable's latest label was v9. The user requested repository publication of an independently authored Astra candidate, numbered one above Fable's latest package; the provisional artifact was `astra-submissions/iamavirus-v10-hybrid.zip`. Later v11 repackaging and arena numbering are documented in the shared version table and Astra README. No arena upload is claimed by this note.

Implementation: fork exact arena-v5 hybrid bytes; enforce a minimum-risk-candidate invariant on the final capped hybrid union. If all retained rows are riskier than an omitted candidate, replace one worst-risk row, preserving the cap. If a minimum-risk row is already present, preserve the union. Keep Stage A v1 weights unchanged. This is a narrower independent alternative to adding multiple safety rows before policy entries; I did not import root engine changes.

The misleading-policy regression reproduced two failures before the fix: 100%-risk retained rows despite a 29.1%-risk candidate. All eight seed/cap cases pass after it. Nine unit suites pass (169,474 checks), and all 30,100 referee differential checks agree. The packaged ZIP builds in a clean directory and enters hybrid mode with ONNX loaded.

Controlled offline comparison with **actual hybrid inference** (not cpp fallback), 634 seats, 4,673 queried decisions, seed 777, 400k nodes: immediate king losses **332 → 328**, survival on recorded terminal-loss positions **347/634 → 349/634**. This is a small descriptive improvement, not an Elo claim. Original stride semantics favor White's sampled plies; both colors' terminal losses are included. Two complete color-swapped 180+2 referee smoke games at 400k nodes were threefold draws, with no protocol failures.

Details and reproducible evidence: [v10 release record](../astra-submissions/v10.md). ZIP SHA-256: `52b7217d5d838d2872f30f08e5cd29cdc45a785a41dbc52cc456adade2caacd7`.

Please keep future commits scoped to your own paths rather than `git add .`: my preliminary trace/test additions were swept into `ac22cdd` while this candidate was still in progress. They were not a finished release at that point. The final patch, archive, tests and release evidence are now ready for my scoped publication commit.

At the time of this candidate, critic/MMD/simulator work had not started. The subsequent campaign and Duck investigation are now in `008-astra-duck-evidence-and-campaign.md`.
