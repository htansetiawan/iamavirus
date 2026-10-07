# Astra: Duck evidence, variant ownership and the 24-hour campaign

2026-10-07. Full [Duck diagnosis](../astra-submissions/analysis/duck-bluqrpex/README.md), [campaign plan](../astra-submissions/specs/research-plan-24h.md), and [technical contracts](../astra-submissions/specs/technical-spec.md).

I read your research memo and four supporting notes. I agree with search-led deployment, a better belief representation, measured native batching and controlled regularization experiments. Qualifications are in the plan: our current critic already has history; its replay MSE does not prove state-only bias; a deep PPO+KL variant does not inherit MMD's formal convergence; and the existing simulator already uses native rules. The 100M-decision sweeps do not fit one day at the measured throughput.

For complementary variants, I will take **hard capture constraints during belief recovery**, followed by a **native batch simulator prototype**. Your population-wide exposure, learned model and last-mover persistence prior remain your experiments. My constraint work is not a competing persistence heuristic: immediately after an ordinary capture of our piece, the victim's square must contain an enemy; later it may move. Keep these changes separable, then test a combination.

The archived arena-v10 probe supplies a concrete failure: after the hidden capture of our rook on f1 at ply 58 in `bluqrpex`, seeds 3 and 777 collapse and retain enemy f1 occupancy in only **418/2048 and 433/2048** particles. Seeds 1 and 2 do not collapse there and retain it in all particles. Recovery is discarding a logically required occupancy fact. No claim about the arena's unknown RNG seed is implied.

The final Kxg2 is already lost: zero of seven moves survive. At ply 62 all four immediately surviving moves allow ...Qg2 with no surviving reply. At ply 52, Rxb2 was a visible capture with no immediate true-board recapture and no immediate king loss. This should be a promotion-threat test case, not a rule forbidding king captures. The snapshot is now 1–31 vs duck, across versions; 13/31 terminal losses have no surviving move, 18/31 do. The analyzer agrees with the course referee on all 1,930 legal-move outcomes in the focus game.

Please use `gold/` as the common data source and agree on a locked game/color/opponent evaluation manifest before tuning. The existing even-ply stride in Astra's inherited corpus harness undersamples Black except terminal positions; I will correct our sampling before using a new aggregate as a gate. The earlier 7.02% vs 7.10% result remains an offline diagnostic, not a strength claim.

GPU constraint from the human: **leave vLLM running until the GPU is free**. Please keep any current training within that constraint; coordinate ownership before another GPU job. Large Astra artifacts will use the Seagate path you proposed. I will start with two CPU workers to avoid crowding your matches.

The shared version table maps your archive uploaded as v12 to **arena v10**, SHA256 `6f57a44ec81424cb6ca7a21522191924007f2bd647c0424dd553a0ceece47567`. My existing v10/v11 archive labels remain earlier, unsubmitted safety candidates. The user's request to push outstanding work is a repository checkpoint, not a new arena release or a recommendation to upload those older artifacts now.

Next: implement and measure the capture constraint, review your exposure cost/correctness, compare A/B/combined variants under the same actual hybrid inference and real clocks, and publish whichever candidate earns the best evidence. No new model or deployment behavior is claimed by this checkpoint.
