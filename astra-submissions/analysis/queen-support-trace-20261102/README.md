# Two queen-loss belief traces

The frozen plan and runner use the unchanged v37 binary with its existing log-only truth hook. True boards are diagnostic inputs, not policy features; these runs are not eligible strength tests.

## Completed: support loss predates the queen mistake

All four first-attempt calls pass, with unchanged final choices between logging-off and logging-on in both cases. This is a diagnostic observation, not proof that instrumentation leaves every intermediate world unchanged. Run handle 98511 and summary 77029 exited 0; host-owned processes are gone and cores 2–3 are released. The four calls took about 43 seconds; no host launch-PID snapshot was captured before completion, but the original handle and every first-attempt receipt are retained.

**Lost Signal (`9ospae7x`).** The traced true placement is present at ply 27 in 54,105 worlds, ranked 37,896; its share is below the log's five-decimal display precision. The next opponent move is Qd8e7. At ply 28 the update reaches 200,000 worlds and truth is absent. No pre-update clock-thinning line occurs between those two reports. Truth remains absent through ply 52, when only 833 worlds remain and the engine chooses Qe2b5, the recorded queen mistake at ply 53. The older final-only trace had 917 worlds; these are different diagnostic runs, not evidence of exact replay equivalence.

This narrows the first-loss interval to the opponent expansion/capping update in this new run, rather than an immediately preceding clock shrink. It does not directly log the candidate before the expansion cap, so attributing the exact internal stage still requires a stage-specific probe. The truth was already underweighted before disappearance: retention and move likelihood can compound. Once discarded, reweighting the surviving worlds cannot restore it. A bounded backlog/re-expansion mechanism after the belief contracts is a concrete design to investigate if the stage probe confirms this mechanism; it is not implemented or claimed to work.

**Foggy Fischer (`ncejetlc`).** Truth remains present at all 48 logged views, with no cap or clock thinning. The final belief has 11 worlds, truth rank 4 and printed share 0.00003. The earlier full-precision posterior audit measured 0.0000344232. At plies 46 and 47 it printed 0.00009; the observed Na3c4 move at ply 48 reduced the share further without changing the board count or rank. Extra world samples cannot fix a case where every world is already searched. This motivates comparing move-likelihood models on fixed worlds and representative held-out games, not fitting a correction to this one loss.

These two loss-selected cases cannot establish population miscalibration. Small probability on one realized event is not by itself proof that a probability model is wrong. Future fitting must include outcome-independent games and controls. No model, threshold, candidate or 219 match setting changed.

Evidence: `summary.json` contains all 100 post-update reports; raw stdout/stderr and hashes are retained in `receipts.jsonl`. `terminal.json` records process completion.
