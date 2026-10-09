# 020 — Why we lose to the top six, and the plan to beat duck and Instructors

*Fable, 2026-10-09 15:10 UTC. Data: v20 + v21 (the same bytes), 54 games against the top six (6–3–45), 136 games in all; every replay validated. A full report regenerates every 30 minutes: `data/reports/top6-report.md` (ladder, record by version, skill gaps, loss anatomy, what worked).*

## Where we stand

Rating 1622, 8th of 12. duck is +311 above us, Instructors +267. Against them v20 went **4–1–11 (duck)** and **2–0–6 (Instructors)**; against the other four 0–2–28. v15 went 2–0–44 and 4–0–40 against duck and Instructors, so we are moving, from almost nothing.

## The missing skills, ranked by what they cost us

**1. Seeing danger in the fog, for our king.** All 45 of our king losses to the top six were to a piece we could not see when we moved; 34 of them came from our own king move. The engine's particle belief rates those moves safe, and the replays show it is badly miscalibrated:

| open lines from the king's destination into unseen squares | king moves | king captured on the next ply |
| --- | --- | --- |
| 0 | 227 | **0%** |
| 1 | 87 | 6% |
| 2 | 108 | 15% |
| 3 or more | 226 | 14% (22% against the top six) |

**2. Resisting bait.** Capturing with the king lost the king on the very next ply in **18 of 57** cases. Against duck and Instructors, 7 of our 13 king losses came right after our king took a piece they had put next to it (example: Instructors played Qxf7 sacrificing the queen; Kxf7 walked onto the open f-file in front of a hidden rook on f1).

**3. Seeing danger in the fog, for our queen.** In 19 of the 42 losses where we fell 3 points behind and stayed there, the piece lost was our queen, almost always to a capturer we could not see when we moved. Instructors took our queen between plies 31 and 42 in 4 of our 6 losses to them. Queen moves onto squares with 3+ open lines into the fog are captured on the next ply **21–26%** of the time; with no such lines, 0 of 22 against the top six.

**4. Stealth (attacking from the fog).** 43–45% of their captures come from squares we cannot see; ours, 27–33%.

**5. Information.** In these games they see 34–36 squares on average to our 31.

**6. King pressure.** Against the top four they attack our king 6.1 times per 100 moves; we attack theirs 1.3 times.

The first three are defensive and cost us games directly; 4–6 are why we rarely win when we survive.

## Plan (v22)

1. **Calibrated fog risk (now).** An engine term that prices king moves, king captures and queen moves by the open lines from their destination into unseen squares, using the rates above as a floor under the particle estimate. Gates: replay our losing decisions (does it now refuse them?), games against the v20 bytes (what does the caution cost?), and the TA Baseline P replica (no regression where we already win).
2. **A belief that keeps hidden sliders alive.** The particles lose track of where unseen rooks, bishops and queens can be; note 017 already showed sliders are the discipline ceiling.
3. **RL against opponents that ambush.** The RL league has only networks without search; it needs search-based and ambushing opponents (this needs the RL trainer, which the session cannot currently read).

Predictions will be made per opponent class: TA baselines, top six, everyone else.
