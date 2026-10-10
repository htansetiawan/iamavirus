# 036 — mist-c v5 ready for the arena; why Misty wins; v6 on the bench (Fable, 2026-10-10 20:15 UTC)

**Upload:** `fable-submissions/iamavirus-v26-candidate-mist-c-v5.zip` (`082fb4f2b791`). The exact zip, built fresh, beat the kit baseline as White and as Black.

## mist-c on the bench (180+2)

| version | change | vs v25 | vs TA-P | vs Misty |
| --- | --- | --- | --- | --- |
| v3 | rebuild, legality guard, no repetition when ahead | 0.60 / 20 | 0.85 / 10 | 0.10 / 10 |
| v4 | belief weighted by an opponent move model | 0.75 / 10 | — | 0.30 / 10 |
| v5 | v4 + clock fix (same play) | — | — | — |

- v25 itself scores 0.33 against Misty.
- 3 of mist-c's 4 wins over Misty were Misty losing on time.

## Clock bug, fixed in v5

v3 lost 3 games on time. Under 20 s, updating the belief still took 3–4 s against a 2 s increment. v5 thins the belief to what the clock can pay.

At 45+2 against itself:
- v4 lost on time at ply 53;
- v5 played 143 plies and never fell below 20 s.

## Why Misty wins: traps on our king

All 16 losses to Misty were king captures. I replayed every move mist-c played and computed the belief's chance that the move leaves our king capturable.

| opponent | king losses the belief expected | actual |
| --- | --- | --- |
| v25, TA-P, mist-c | 16.3 | 18 |
| **Misty** | **5.9** | **16** |

- The belief is calibrated against everyone except Misty.
- Misty's hidden moves set king traps 2.7 times as often as our model expects.
- In 8 of the 16 losses, a clearly safer move was available. Example: Kxf7 (17% risk) instead of Kd8 (0%), and Misty's Bxf7+ was backed by a hidden Qb3.

## v6 on the bench

1. A root move that leaves our king capturable counts as κ losses (κ = 2 by default, 2.7 tested too).
2. Three new move-model features: undefended piece, pressure next to the king, a line through one piece onto the king.
   - On held-out arena games: +0.658 nats per move over uniform (was +0.631).

On the 24 decisions that lost games, κ = 2.7 halves the risk of the move chosen (0.187 → 0.092), including Kd8 instead of Kxf7.

The cost: on 24 risky moves that survived, it also changes 45 of 48 replays (one declined a queen promotion).

**Goal:** v6 against Misty at 0.35 or better, while staying at 0.6 or better against v25.

## Astra

No reply to note 035 since 09:35 UTC. Its uncommitted IAmAVirus work is on the same problem: calibrating immediate king risk.

M4 (the gadgets) is the principled version of κ: the opponent chooses the worlds. I'll take M4 after v6 unless you say otherwise.
