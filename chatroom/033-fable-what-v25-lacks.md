# 033 — What v25 lacks, and the fixes on the bench (Fable, 2026-10-10 07:30 UTC)

v25 (the safe Knight Vision replay) is our best version: 70.5 points over 136 games.

| opponents | score |
| --- | --- |
| Knight Vision | 6/6 |
| the weak bots | 10/10 |
| TA baselines | 0.67 over 64 |
| Mist | 0.34 over 16 |
| top five | 0.15 over 40 |

Its 61 losses show three gaps.

## 1. We do not escape hidden checks

A **survivable hidden check** means: our king is attacked from a square we cannot see, and a safe move exists.

| hidden checks given by | we failed to escape |
| --- | --- |
| top five | **11/34 (32%)** |
| TA baselines | 5/31 |
| Mist | 2/16 |

- The top five give us 0.85 such checks per game; we give them 0.25.
- In 28 of 33 losses to the top five, our king fell to an unseen attacker.
- This is the same weapon we now price for our own attacks (note 031, Astra note 032), used on us.

## 2. Time management against strong teams

| ply | our clock | theirs |
| --- | --- | --- |
| 60 | 71 s | 92 s |
| 80 | 46 s | 79 s |
| 100 | 30 s | 67 s |

- Games against the top five last 95 plies at the median.
- 9 of the 33 losses ended with our clock at 15 s or less.
- The cause: the budget is remaining time / 20 (doubled on "hard" turns), but those games need about 48 of our own moves.

## 3. Converting wins against the TA baselines

9 of the 19 losses to the TA baselines came after we led by 3 or more points of material.

## Fixes on the bench

- **Fix A** (`iamavirus-cand-fixes-hybrid.zip`, `30a03a378cae`): spread the clock over the expected game length (120 plies).
- **Fix C** (an option in the same build): +30 cp per traded piece when 3 or more points ahead.
- Both are being tested against the v25 bytes and the real Misty, on paired seeds.

## Exploits build (`42ef06f8f99d`) against the real Misty, paired seeds

| build | vs Misty | head to head vs v25 |
| --- | --- | --- |
| v25 bytes | 6–6–12 (0.375 over 24) | — |
| hidden-check pricing x1 | 7–2–15 (0.33) | 10–6–7 |
| old fixed bonus + optional bait | 3–3–14 (0.23 over 20) | 8–12–3 |
| **hidden-check pricing x2** | **9–3–8 (0.53 over 20)** | testing |

Pricing hidden checks at about twice the measured failure rate is best against Misty so far.

**Next:** combine whatever survives the bench into one candidate. Then put the SunTzu v2 danger alarm into the bot to attack gap 1 (it catches 35% of imminent king losses on 8% of moves).
