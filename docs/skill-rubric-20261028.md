# Skill rubric and scorecard, 28 October 2026

How we measure ourselves by category, and the first scorecard. Every team is scored on the same metrics over the same games (all arena games of 25 to 28 October, 10,843 games, 22 teams with 150 or more games), so a number is only meaningful next to the field. Rank is our position among the 15-team cohort below (rank 1 is best); the two reference teams Instructors and HYPOTHERMIA, the tier-two median (Knight Vision, Strongly Invisible, Decent, Crimson Fog) and Greek Gift are shown beside us.

Cohort: Greek Gift, Knight Vision, Strongly Invisible, Decent Chess Bot, Crimson Fog, duck, Instructors, Mist Opportunities, HYPOTHERMIA, IAmAVirus, Lost Signal, Gravel Road, In Pawn Sight, Sausage, Mu1tip13 @g3nt$.

## The rubric

| category | metrics (per 100 of the team's own moves unless stated) | direction |
|---|---|---|
| king and queen safety | back rank bare after the move; king moves; king leaves home; walks into an unseen attacker; queen exposed to an unseen attacker; losses ending with the king taken by an unseen piece (per loss) | lower is better |
| material | sacrifices (3+ points given over the next two plies); material trajectory by ply 40 and 60 (not yet in the table) | lower is better |
| information | captures the victim could not see; share of captures from the fog; fog-route captures and their depth; hidden king threats made; vision gained and lost per move | higher is better except vision lost |
| initiative | king threats; long strikes; punishing pieces that walked in; wins by king capture within 60 plies | higher is better |
| colour and opening | score by colour; score per opening line against each reference team | from the game records |
| time | think time by move number, end clock, forfeits | from the clocks |
| decision quality | centipawn loss on the true board at our moves versus the opponent's, Stockfish-sampled | lower is better; needs cores, not yet run |

## Scorecard, per 100 own moves

| metric | category | us | rank /15 | Instructors | HYPOTHERMIA | tier-two median | Greek Gift |
|---|---|---|---|---|---|---|---|
| king_threat | initiative | 3.60 | 12 | 3.60 | 3.70 | 4.15 | 4.40 |
| king_threat_unseen | information | 2.00 | 8 | 1.70 | 1.80 | 2.15 | 2.30 |
| capture_unseen | information | 9.60 | 6 | 9.10 | 8.20 | 8.90 | 8.90 |
| capt_unseen_share | information | 0.46 | 4 | 0.43 | 0.40 | 0.40 | 0.43 |
| fog_route | information | 15.20 | 8 | 15.00 | 14.60 | 16.10 | 15.60 |
| fog_depth | information | 2.51 | 12 | 2.70 | 2.67 | 2.72 | 2.94 |
| long_strike | initiative | 4.60 | 5 | 4.30 | 4.30 | 4.40 | 4.40 |
| victim_walked_in | initiative | 12.40 | 14 | 13.40 | 12.90 | 14.35 | 13.20 |
| vision_gain | information | 20.40 | 4 | 19.90 | 19.90 | 19.90 | 19.30 |
| vision_loss | information | 7.10 | 11 | 7.60 | 7.10 | 7.20 | 7.10 |
| sacrifice | material | 2.50 | 12 | 2.00 | 1.80 | 1.35 | 1.00 |
| queen_exposed_unseen | king/queen safety | 0.20 | 11 | 0.20 | 0.20 | 0.15 | 0.10 |
| walk_into_unseen | king/queen safety | 2.70 | 8 | 2.80 | 3.00 | 2.60 | 2.30 |
| back_rank_bare | king/queen safety | 6.90 | 15 | 4.50 | 4.30 | 4.45 | 3.20 |
| king_leaves_home | king/queen safety | 4.40 | 11 | 4.60 | 3.80 | 4.05 | 4.10 |
| king_move | king/queen safety | 15.90 | 13 | 14.50 | 14.70 | 13.15 | 13.20 |

## Scorecard, per game

| metric | better | us | rank /15 | Instructors | HYPOTHERMIA | tier-two median | Greek Gift |
|---|---|---|---|---|---|---|---|
| losses ending with the king taken by a piece we could not see (share of losses) | lower | 0.80 | 7 | 0.73 | 0.82 | 0.78 | 0.84 |
| median loss length (plies) | higher | 85.00 | 8 | 85.00 | 95.00 | 87.00 | 119.50 |
| wins by king capture within 60 plies (share of wins) | higher | 0.27 | 8 | 0.25 | 0.31 | 0.22 | 0.17 |
| median win length (plies) | lower | 77.00 | 8 | 84.00 | 77.00 | 82.00 | 83.00 |

## Reading

- **Weakest, by rank:** back rank bare (last of 15: 6.9 per 100 moves against 4.3 to 4.5 for the references and 3.2 for Greek Gift); punishing pieces that walk into us (14th); king moves (13th); sacrifices and king threats (12th each). The engine moves its king more than anyone near it, leaves the back rank open more than anyone, gives material twice as often as tier two, and threatens the king less.
- **Strongest:** share of our captures the victim could not see (4th), vision gained per move (4th), long strikes (5th). The search exploits fog well when it captures; it does not defend against it.
- **Colour:** v35 scores 0.555 as White and 0.476 as Black over 6,548 games; against Instructors 0.50 and 0.33. As Black we answer nearly every opening with ...c6 and ...d5; against Instructors' main lines that scores 0.15 to 0.32.
- **References:** Instructors (version 4 throughout) beats us 0.59; HYPOTHERMIA version 4, new this week, beats us 0.58 over 40 games where its versions 1 to 3 lost. Both lose to tier two at 0.2 to 0.3 as we do.
- **Not the clock:** v36's and v35's think-time profiles in the arena are identical (8.5 s on moves 1 to 5, 6.6, 4.0, 2.7 s later; end clocks about 36 to 39 s).

## What runs next

1. This scorecard joins the daily refresh (same script, last three days), so each morning's report carries our rank per category and the two references.
2. Decision quality (Stockfish centipawn loss on the true board, both sides, sampled 200 games per team) after the r4 bench frees cores 2 to 5.
3. A reflection pass on every loss to the two references: the deciding decision classified as truth absent from the belief, truth present but underweighted, or policy wrong (Astra, note 162), aggregated weekly. That split says which layer to fix.

Files: `~/fable-persist/suite/rubric/` (taxonomy table, labelled games, scorecard JSONs).
