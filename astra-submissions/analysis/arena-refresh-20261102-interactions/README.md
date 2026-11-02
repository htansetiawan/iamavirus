# Bounded replay refresh and taxonomy, 2 November 2026

Original refresh74613 exited0: newest500 listed,474 new accepted,26 cached,487 sequential public GETs at1.2-second spacing,zero errors/quarantines. Each new replay is pinned by SHA256 in `manifest.json`; this bounded refresh does not establish complete archive synchronization.

All474 now carry31,517 move annotations, checked against31,991 replay frames through the separate rules engine. `taxonomy.jsonl.gz` preserves per-game moves/counts and versions; `taxonomy-summary.json` stores all19 tag numerators and denominators by team/version/colour/opponent/version. `taxonomy-integrity.json` verifies exact game coverage, hashes and panel totals.

Supplemental fields describe627 queen captures using visibility at the victim's decision and immediately before capture. These are not net-loss labels.19 en-passant captures are separately identified; the legacy taxonomy's destination-occupied definition is left unchanged. Both future boards and opponent views are offline labels, never playing-engine inputs.

194 of these new games overlap experiment228's frozen test. Annotation waited until all model selection hashes were locked and the one test run completed. These test games are now used evidence, not a fresh holdout for a retuned successor. No model, guard or deployment changes when these files are regenerated.

The external drive is mounted read-only. Raw data is in `data/raw/games`; no external archive write or disk repair was attempted.
