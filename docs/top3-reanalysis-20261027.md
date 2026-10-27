# Getting to the top three: a re-analysis, 27 October 2026

Question from Henry: how do we get to rank 2 or 3? Evidence: the 167k arena games held
locally (all teams, both views), the daily taxonomy, and what we have measured on mist-c.

## Where we stand

Leaderboard at 10:18 UTC: Greek Gift 2379, Knight Vision 2142, Strongly Invisible 2102,
Decent Chess Bot 2089, Crimson Fog 2058, duck 1987, Instructors 1962, Mist Opportunities
1951, HYPOTHERMIA 1919, IAmAVirus 1887 (rank 10). Rank 3 is 215 to 255 Elo away. The arena is
Elo with K = 8, so the rating tracks strength within about 30 points. v35 gained about 30 over
v34; each guard rule since has been worth 10 to 20; the v36 piece term failed its gate today.

## Who beats whom

Score of the row team against the column team, all games since 13 October (current versions).

| | GG | KV | SI | Dec | CF | Mist | Inst | duck | us |
|---|---|---|---|---|---|---|---|---|---|
| Greek Gift | | .73 | .82 | .83 | .86 | .95 | .86 | .89 | .93 |
| Knight Vision | .27 | | .58 | .63 | .60 | .78 | .71 | .65 | .76 |
| Strongly Invisible | .18 | .42 | | .51 | .59 | .72 | .70 | .64 | .78 |
| Decent Chess Bot | .17 | .37 | .49 | | .48 | .68 | .68 | .62 | .72 |
| Crimson Fog | .14 | .40 | .41 | .52 | | .68 | .55 | .57 | .71 |
| Mist Opportunities | .05 | .22 | .28 | .32 | .32 | | .48 | .47 | .51 |
| Instructors | .14 | .29 | .30 | .32 | .45 | .52 | | .44 | .59 |
| duck | .11 | .35 | .36 | .38 | .43 | .53 | .56 | | .68 |
| IAmAVirus | .07 | .24 | .22 | .28 | .29 | .49 | .41 | .32 | |

Cells hold 94 to 849 games each. Three tiers: Greek Gift alone; Knight Vision, Strongly
Invisible, Decent and Crimson Fog, who score 0.4 to 0.6 among themselves; and Mist,
Instructors, duck and us, who score 0.44 to 0.59 among ourselves, 0.22 to 0.38 against tier
two and at most 0.14 against Greek Gift.

Rank 3 therefore means becoming a tier-two engine: about 0.5 against Knight Vision, Strongly
Invisible, Decent and Crimson Fog, 0.2 against Greek Gift, 0.7 against tier three. Today we
score 0.22 to 0.29, 0.07 and 0.32 to 0.49.

Mist Opportunities matters as a control. It is the other Obscuro-style engine in the arena, better
tuned than ours, and it sits in tier three with us: 0.22 to 0.32 against tier two, 0.05 against
Greek Gift. Two implementations of the same design at the same budget (two cores, 180+2) landed
in the same tier. Both implement a fraction of the paper's agent: 32 root worlds, depth-1
leaves, no 2-KLUSS, no safety gadgets, no tree carried between moves.

## How the games are lost

- **A bleed, not a trap.** Median material on our side at ply 40 and 60: Greek Gift −1 and −3,
  Knight Vision −2 and −6, Decent −1.5 and −3, Strongly Invisible 0 and −2. Our losses to these
  four last 75 to 85 plies (median). Every one ends by king capture.
- **The queen asymmetry.** Share of games in which a queen is lost outright (the other queen
  still on the board three plies later), ours against theirs: Greek Gift 0.57 vs 0.37, Decent
  0.52 vs 0.37, duck 0.57 vs 0.41, Knight Vision 0.44 vs 0.48, Strongly Invisible 0.43 vs 0.53.
  Greek Gift against tier two loses its queen outright in 0.28 to 0.43 of games while its
  opponents lose theirs in 0.52 to 0.63. The same asymmetry runs down the whole matrix.
- **Taxonomy against the teams above us** (three days, per 100 moves, us vs them): sacrifices
  3.0 vs 1.6, king moves 17.9 vs 12.6, king threats 3.1 vs 4.3, hidden king threats 1.4 vs 2.2.
  We give material and shuffle the king; they attack the king under fog.
- **Time is not the story.** Greek Gift thinks 3.7 s a move (median) to our 2.9 and ends with
  27 s; we end with 35 s unused. About three quarters of all final king captures, ours and
  theirs, come from a piece the loser had not seen the ply before.

## What the levers are worth

| lever | evidence | verdict |
|---|---|---|
| Guard rules (king, queen, piece) | +10 to 20 each; the piece term lost 15.5/40 to v35 today | diminishing; not a route to +200 |
| More search at the current belief | 1 s to 6 s: fixed 12, broke 5 of 487 suite decisions; 2.65x expansions marginal | null as things stand |
| Belief quality | the truth is in the belief in 68 of 71 blunders but at median share 0.06%; the temperature sweep was the largest suite gain so far | the lever we have never sized |
| M4: 2-KLUSS, safety gadgets, tree carry-over | the part of Obscuro neither we nor Misty implement; Astra's `kluss.c` exists on a branch, unplayed | unknown, structural |
| In-process leaf evaluation | 20 to 50x per leaf (note 161); pays only if search converts | depends on the belief result |
| Learning | PPO trainer exists, not integrated; Astra's teacher-student loop (note 140) not run; a supervised risk head was worse than the C guard (note 143) | nothing measured in play yet |
| Imitation of tier one and two | on disk with the mover's own view: Greek Gift 590k decisions, Knight Vision 935k, Strongly Invisible 1.8M, Decent 646k | unmeasured; the only route that copies what tier two does |
| Opening and exploit lines (note 032) | the protocol does not name the opponent; generic motifs only | bounded |

## The measurement we have not made

The engine is belief × search × evaluation × guard. We know what the guard and more search time
are worth. We do not know what a correct belief is worth, and that decides the route. The
experiment: play v35 with the true board substituted for its belief (an oracle; `MIST_TRUTH_SEQ`
already carries the true boards into the engine, so this is a small change in `main.c`) against
v35, 40 games both colours on cores 2 to 5. If the oracle scores 0.85 or more, the belief is the
bottleneck and the program is belief work: M4 and a learned opponent model. If it scores 0.65
or less, the search and the evaluation are the bottleneck and the program is in-process
evaluation, more worlds and deeper leaves. Half a day of code, one evening of games. Run it
first, after the 20:00 UTC checkpoint, on the cores the gate-2 replays release.

A second cheap measurement: train the view-conditioned imitation model on Greek Gift's decisions
and report top-1 agreement on held-out games, by phase. The pipeline exists in `learning/`.
If agreement is low, imitation is off the table; if high, the integration is a root prior in
mist-c, which the move model already supports for the opponent's side.

## The five weeks to 1 December

1. **This week.** Decide v36 (corrected candidate or stay on v35). Oracle decomposition.
   Imitation ceiling. Gym calibration by Astra (the local Misty is the arena's Mist v1; v35
   scores 0.72 against it and 0.49 against Mist v2), with a ladder of our own past versions whose
   local results must reproduce the arena ordering.
2. **By 7 November.** Choose the route from the oracle result and commit the remaining three
   weeks to it: belief (M4 plus opponent model) or search (in-process evaluation plus capacity),
   with the imitation prior added to either if its agreement justifies it.
3. **By 21 November.** One candidate through the gates on the calibrated gym, uploaded, and
   confirmed in the arena (200 games is a day).

What to expect. Tier two needs +200 Elo and nothing measured so far delivers more than 30. The
oracle result is the honest test of whether this architecture can reach tier two at all: if v35
with perfect information is not far stronger than v35, no belief work gets there and the route
is a learned policy from tier-two play. Either way, the next two weeks must be spent on the
measurement, not on another guard rule.
