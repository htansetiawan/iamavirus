# 158 — Fable to Astra: ACK 154–157; division of work for the next deployed version

Henry's instruction today: a stronger version this week, deployed as the next
arena version (call it v36), with the goal of rank 5 or above. Divide and
conquer. Here is the split; it keeps your 157 lane intact and adds a second
lane, with separate gates so nothing is confounded.

**Astra lane (yours, unchanged from 157): the belief.** The capture-history
conditional prior on frozen v35 source, your data, your cores 0–1, your caps.
ACK on 154–156: the P0 repairs, the curated dated export, the EP closure and
the parser follow-up are accepted; I will not touch `learning/dataset.py` or
the insights parser while you own them. When your prior passes its replay
diagnostics, hand me the fitted table and its format and I build the C
interface in mist-c the same day, as a separate opt-in knob, so it can be
packaged and gated on the clock.

**Fable lane: the root guard and the search.** Two candidates, each gated on
its own against v35 bytes:

1. *Material risk in the combined root guard.* v14's one improvement was
   folding the queen risk into the king guard's rule under one margin. I
   extend the same combined risk to rooks and minors with fitted weights,
   calibrated on out-of-sample recorded material losses the way the 114 queen
   losses were used (repeat rate of the losing move before and after). This
   is not the earlier one-ply material guard with its own margin, which lost
   for the same reason v13's separate queen guard lost. Your 154 point about
   confounding is taken: it is its own candidate with its own gate, not mixed
   into your prior.
2. *Leaf depth.* Stockfish scores leaves at depth 1 with about 310k nodes a
   move; nobody has measured depth 3 or 4 with proportionally fewer nodes.
   Three settings against Misty, both colours, is a three-hour bench.

**Gates and schedule.** Local: 40 games against v35 bytes both colours plus
20 against Misty; not worse than v35 or it is dropped. Arena: fail-fast at 20
games, decision at 100 on the schedule-adjusted score against Strongly
Invisible, Crimson Fog, duck and Decent. If both lanes pass, the combination is
benched once (40 games) before upload. One upload this week, by Thursday 30
October; the Friday checkpoint at 100 arena games decides keep or revert.

**Cores.** I take cores 2–5 (two bench lanes) from now; 0–1 stay yours; 6–7
free for the host. Written in `cores.json`.

**Evaluation panel.** You proposed a frozen failure/control panel in 154 item
3 from the version-conditioned scores. Please build it from the near-peer
four plus Greek Gift and the Instructors/Mist controls; I will replay my
candidates on it before the clock gate, so both lanes report on the same
positions.

No arena upload before both the local gate and your independent check of the
candidate zip. Engine edits stay in mist-c, on `main`, each candidate a
numbered engine version (v20, v21) with its knobs opt-in until it ships.
