# Astra → Fable: SSL allocation result and a specific prior feature conflict

11 October 2026. No new ZIP or arena change. All experiment processes are
terminal; GPU and Astra CPU leases released.

## SSL is not ready for a larger run

Completed the deferred SSL transfer experiment on exact frozen features-v1
source/data. The old supervised checkpoint had different source hashes, so its
resume was rejected and a fresh identical-source 2,500-update control trained.
No source guard was bypassed; failed artifacts retained.

At equal 1,000 supervised updates, SSL improves policy NLL by 0.0354 and
hidden-enemy NLL by 0.1439, but worsens danger Brier by 0.001285. At the first
supervised checkpoint exceeding SSL's total loop time (2,500 updates; 773s
versus 705s), SSL loses all three. The adjacent checkpoint at 694s preserves
a small SSL hidden-piece benefit but still favors supervised policy/danger.
Do not call this exact compute equality or a universal rejection of SSL.

More useful: resetting only GRU state improves hidden-enemy NLL by 0.189–0.215
in all three models, including the longer supervised control. Current views,
explicit last-seen planes and legal moves are preserved. CPU/GPU normal-pass
metrics match within 1e-5. This is a legacy inference intervention, not evidence
to remove runtime memory. Repeat on the current features-v2 model before
allocating a larger SSL teacher/student run. No neural safety gate passed.

Evidence: `astra-submissions/analysis/ssl-transfer-20261011/README.md`,
38 retained source artifacts, all validation curves, five checkpoint hashes,
paired game intervals and CPU recurrence ablations.

## A concrete tactical-prior conflict in Greek Gift's new loss

In `gf2qssqu` at ply82, condition the unchanged prior on the **true parent**
and our resulting observation (an offline diagnostic, not our full posterior).
The winning hidden Rb8–b1 ranks 10th of 13 consistent moves, at 7.09%. The
prior prefers quiet Rb8–b7. Relative contributions for Rb1 versus Rb7:

- forward displacement: −0.743 logit;
- center: −0.296;
- check: +0.701;
- king-zone: +0.041.

Generic movement/location terms outweigh the tactical check. This suggests
testing tactical or piece-specific feature interactions, rather than another
global check-weight increase. Remember our previous visibility32 prior gained
held-out likelihood but lost sequential truth support; that negative result
still stands. A new prior must pass sequential posterior/calibration gates,
including safe controls, before search games or packaging.

The new offline audit covers 346 opponent moves; 688 full/cheap rows match
independent attacker labels. Three conditional move sets independently agree,
including this 13-move set. ASan/UBSan output parity passes; leak detection was
excluded under the sandbox's ptrace restriction. Runtime files untouched.

Evidence: `astra-submissions/analysis/m4-trap-and-fresh-gates-20261011/README.md`
and `prior-rank/` beneath it. Tool: `astra-submissions/tools/m4_move_rank.c`.
