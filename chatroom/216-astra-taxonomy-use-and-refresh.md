# Taxonomy use and bounded replay refresh

Astra, 1 November 2026. The human asks whether taxonomy improves belief weights and tests king/queen guards.

Current answer: it selects diagnostic cohorts and measures behaviour. Runtime successor weights still come from the separately fitted opponent move model and empirical history table. Tag rates do not directly multiply belief weights or update guard thresholds. Changed belief weights can change guard risk without changing thresholds.

The fresh taxonomy comparison contains 51 decisions from 25 games against Instructors, duck and HYPOTHERMIA. It reconstructs permitted observations and earlier own moves; true-board labels are joined afterward. It records guard risk and exclusions. It diagnoses king and material failures, but its zero qualifying queen-loss outcomes do not validate queen-guard quality. A queen being attacked is not necessarily a losing exchange. Retain both actual losses and sound trades/ordinary controls in any future queen-specific supplement; keep the existing suite fixed.

The separate fitted king-risk curve improves held-out probability scores, but its search integrations failed their decision gates. This is evidence of learning and testing, not a deployed improvement. The current data-to-candidate-to-promotion distinction must remain explicit.

Evidence: `docs/arena-intelligence-loop.md`, `astra-submissions/tools/fresh_taxonomy_gate.py`, `astra-submissions/analysis/fresh-taxonomy-20261101/README.md`, `astra-submissions/analysis/king-event-calibration-20261101/README.md`, and `astra-submissions/analysis/calibrated-root-20261101/README.md`.

The bounded newest-600 public refresh is still running on original handle 8879, on cores 4–5. Its source and receipt are under `astra-submissions/tools/refresh_evening_intel.py` and `astra-submissions/analysis/arena-intel-20261101-evening/`. No model fitting, history-table replacement, guard change or deployment is performed. A new helper, `astra-submissions/tools/pilot_taxonomy.py`, annotates every completed valid planned match by policy and colour; these descriptions do not alter experiment 214's frozen gate.

Correction to an earlier status inference: an empty refresh log was not evidence of waiting for the first API response. The redirected file is buffered. The refresh snapshot was successfully saved at 23:33:07 UTC; at a subsequent check the accepted index held 191,659 unique IDs, versus 191,335 before this run. This index delta may include concurrent writers and is not yet an attributed completion count. Wait for the original handle and final receipt; do not restart the refresh.

Experiment 214's original handles 11227 and 10536 remain live. The last checked completed record is 2 wins and 1 loss, with both wins as White. No promotion claim, candidate change, new ZIP or additional game launch follows this interim report.

## Completed data and new queen-case evidence

Refresh handle 8879 exited 0: 600 listed, 455 accepted new replays, 145 cached, zero errors/quarantines. Corpus 191,790. The new 455 are opponent-only games because our recent games were already cached. All have traceable taxonomy; 33,334 move annotations are compressed with verified hashes. Latest saved snapshot has arena v37 active, 1896.73 Elo, rank 12 among rated visible teams, at 23:33:07 UTC.

New queen curation uses the complete cached 20:00–23:33:07 window, not only new downloads: 63 of our v37 games, 103 decisions, 40 actual queen captures and 63 ordinary controls. Referee agrees on 5,553 frames / 10,638 transitions. Four recorded net >=4 losses; three remain losses under best safe one-response analysis, one has equal-material recaptures.

Important selection issue: queen_exposed_unseen uses the **post-move** view. Of 40 capturers, 37 were hidden before our choice, 33 of those became visible afterward. All four recorded large losses are in that revealed-after-move group and missed by the existing tag. Keep the existing tag's definition; add decision-time visibility to curation rather than treating an aggregate exposure rate as a risk estimate. Most queen captures here were trades, so a blanket penalty for hidden defenders would be unjustified.

Please review `astra-submissions/analysis/queen-cases-20261101-evening/README.md` and its inputs for the next guard/predictor diagnosis. This is additional evidence, not agreement on a model change or an altered 214 acceptance rule. The curation-only path failure is preserved; no match was repeated.
