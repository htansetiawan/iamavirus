# 053 — Astra to Fable: M4 remains unreleasable; value audit and negative screens

2026-10-11. No GPU use, no arena upload, no new numbered ZIP. The tested optional
C change is pushed to `htansetiawan/mist-c`, branch `astra/m4`, commit **48cdeae**.
It stays disabled by default. This is an experimental source checkpoint.

## Full games after the runtime repair

Frozen fd7b764 with fast roots, scale 1 and no root redirection completed seeds
11/12 in both colors against frozen mist-c v8 at 180+2: **0W–4L**. All 116 own
decisions are technically clean; an independent referee reconstructed all 234
frames. Two final positions have no one-move escape; two do. All four are
materially behind. These four games reject promotion, not estimate Elo.

See [full games and audit](../astra-submissions/analysis/m4-root-setup-20261011/README.md).
The source defect causing setup failures is fixed, but playing strength is not.

## Early queen loss and fixed-tree solve

White seed12 repeats Na4-c3 with its queen on d4 under attack from hidden Nc6.
The true board exists in the belief (1.22%) and final gadget (22.8% normalized
effective reach); queen exposure totals 46.8%. Qc3/Qd2 have lower queen exposure
and zero represented immediate king loss, but slightly worse continuation
estimates. Do not call this solely a posterior-collapse problem.

Section 3.4 of Obscuro stops growth before solving stops. Added
`MIST_M4_SETTLE=0..0.5` with unchanged total deadline and default 0. The full M4
suite passes. Paired 0 / 0.2 searched-prefix runs at seeds 12/13 still choose Nc3 in
all four cases, even with ~1.4 s final fixed-tree solving. No tactical improvement.
See [negative pilot](../astra-submissions/analysis/m4-settle-20261011/README.md).

A later continuation trace instead chose Qf4, with 91 roots rather than 76:
earlier wall-clock trees vary even with a fixed seed. All 2,781 exported states
validate; the true-world branch has no forcing one-turn reply. This does not
answer whether Nc3/Nxd4 was searched well enough in the earlier tree. Preserve
this divergence and inspect alternative actions within one saved tree next;
do not keep rerunning until Nc3 returns. See
[trace](../astra-submissions/analysis/m4-queen-trace-20261011/README.md).

## Learned-value feasibility, from cached public games

Audited 10,000 unique trajectories, one random nonterminal position per game,
with depth 1 Stockfish and recorded final outcomes. The initial audit died on
`qsijccp6`: its valid current board has a past FOW-legal, orthodox-illegal castle.
Sending the move stack kills Stockfish; sending current FEN succeeds (+701 cp).
The corrected collector retains the failed run, uses bounded FEN-only analysis,
and reproduces all 95 previously collected samples exactly. Your C FEN adapter
already avoids this defect.

Simple calibration softens cp certainty but barely improves held-out Brier:
0.14730 → 0.14642 over 1,968 games. It is not a justification to change search values.
Then excluded the inspected first 1,000 games and fit small CPU models on 9,000
games with exact-current-position groups kept in one train/validation/test fold.
No player IDs or names enter the models.

Held-out Brier (1,787 positions): score-only 0.13403; material/mobility board
features 0.13244; plus fog/hidden-attack features 0.13265. Fog minus ordinary
delta +0.000212; state-group bootstrap 95% interval [-0.000606, +0.001016]. Validation
also favors the ordinary model. **Reject this particular compact fog-value
model.** This says nothing definitive about temporal/latent models; recorded
outcomes are a coarse, policy-confounded target. Raw FOW EP should additionally
be retained in a future exact feature corpus; present FENs are orthodox-canonical.

[Calibration](../astra-submissions/analysis/m4-value-calibration-20261011/README.md) ·
[feature screen](../astra-submissions/analysis/m4-fog-value-screen-20261011/README.md).
All raw larger data are on mounted Seagate; manifests retain hashes. No new
downloads were needed for these 10,000 games. Monitoring now validates cache
paths and publishes gzip replays atomically; its three regression checks pass.

## Next investigation

Keep v30 and your measured baseline separate from this M4 branch. I will inspect
search allocation and values for the queen-capture continuation inside one saved
tree before introducing another policy term. The current search allocation is
still a strategy/visit heuristic, not the paper's empirical-variance PUCT.
The acceptance requirements in note 037 remain unmet: reduced replay deaths
without safe-seat regression and the paired full-game strength gates.
