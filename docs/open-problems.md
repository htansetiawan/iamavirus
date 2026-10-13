# Open problems and directions

*What the current engine still gets wrong, with the evidence, and the directions we are considering. Status as of 13 October 2026, v34 at 440 arena games.*

[TOC]

## Hidden checks the belief talks itself out of

The king guard works when the belief holds the threat: on the suite the true board is present in 68 of 71 residual hidden-check blunders, but at a median share of 0.06%, far below the 2% margin. The chosen move is the belief's least-risk move; the belief is wrong, not the guard.

The clearest case is the **a5 queen after 1.d4**. In a 19-ply arena loss to Instructors (game `cmyf2h7z`): 1.d4 Nc6 2.c4 d5 3.cxd5 Qxd5 4.e3 Qa5+ with a5 never visible. The belief had the check at a 14% share, the guard fired, and we blocked with Nc3. After 7.a3 Bxc3+ 8.bxc3 the opponent twice declined the free Qxc3+ (8...e5, 9...Nf6). Under the move model, squared by the 2.0 temperature, those two non-captures are near impossible for a queen on a5, so every a5 world fell to a 0.016% share and the engine moved the blocking pawn, 10.c4, into Qxe1. A three-decision mini-suite of this game lives in the persistent suite directory.

Levers under discussion, in the order we would try them:

1. **Threat memory in the guard.** A square the guard has already acted on keeps a floor weight until it is observed. Cheap and targeted; the risk is never moving a blocker again.
2. **A third guard weighting, uniform over the consistent worlds.** Asks whether the move is fatal in a non-trivial fraction of consistent worlds regardless of the model. The risk is passivity, which the suite's material kind measures.
3. **An epsilon floor on the move model.** Opponents do decline free captures; probably too weak alone after two declines at temperature 2.0.

## Two-ply hidden mates

A visible gain in every sampled world can hide a forced king capture in the few worlds that hold both attackers. Example from a bench game: Nf3-e5 wins material on every board the search saw, but with a bishop on c6 and a queen on the long diagonal it allows Qxg2 and the king falls. Both v12 and v9 play into it on every seed. This is not a suite kind yet; the candidate kind is "allowed a forced king capture within two of their moves on the true board", and the candidate lever is a two-ply guard that scores the risk of a forced capture after the opponent's best reply.

## Greek Gift

v34 is 0 for 32 against Greek Gift, the leaderboard's number one, where v33 scored 0.11. Nothing in the suite isolates it yet. The first step is a per-opponent loss classification from the replays: how long the games last, when the material swings, and whether the losses are hidden checks or positional.

## Repetition draws

Ten of 440 games ended by threefold repetition, all in games of 97 plies or more, several against opponents we normally beat. The repetition rule only applies when we are two points ahead; the draws suggest the engine stops pressing when ahead but blind. Logging the material balance at the draw would tell us whether to lower the threshold or add a progress term.

## Measured nulls

Things that were tried and measured as no gain, kept so they are not tried again: compiler flags (-O3, LTO, -march); history-prior pseudo-counts from 1 to 16; a flatter move model (temperature 0.5 and 0.7) and the model turned off; the time divisor 20 on its own; more search time from 1 s to 6 s on the hidden-check kind (it helps only the material kind); the temperature gain without the two-weighting guard (withdrawn as v11 after two 7-to-9-ply losses to our own v10).

## Research directions

- **Search distillation.** Distil mist-c's CFR root policies into a small local network and use it as a root prior or amortised policy, compared on the same suite. This is the arena-compatible way to bring a learned decision model into the engine, since the arena is offline.
- **Learned belief weighting.** Replace or complement the conditional-logit move model with a learned plausibility scorer for hidden boards, scored on the 59 remaining hidden-check decisions and in paired games. A hosted decision model (TypeSafe's Jev) was looked at for this role; it cannot play arena games itself, so the experiment is about whether it beats our fitted model as an opponent-move likelihood.
- **Deep RL methods for the policy.** The Python era's PPO bot with a near-chance value head motivated a literature study of methods for two-player zero-sum imperfect-information games (R-NaD, magnetic mirror descent, NFSP, PSRO, ReBeL, asymmetric critics); the write-up is in the repository's `reports/`.
