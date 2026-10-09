# SunTzu codebook v1: 29105 windows, 3 levels x 16 codes

Each code: share of windows, the side's mean game score, the features it over-represents (z-score vs all windows), and the teams that use it most (share of that team's windows).

## Level 1 (chief: grand strategy)

| code | share | score | over-represented features | used most by |
| --- | --- | --- | --- | --- |
| 1.0 | 1.7% | 0.28 | queen_exposed_unseen +7.2, sacrifice +1.2, long_strike +0.8, queen_raid +0.7 | TA Baseline P 4%, TA Baseline A 3%, TA Baseline S 2% |
| 1.1 | 8.1% | 0.78 | own_shelter:one-gone +1.6, enemy_shelter:one-gone +0.9, enemy_shelter:advanced +0.6, material_diff +0.6 | Knight Vision 12%, Decent Chess Bot 9%, Greek Gift 9% |
| 1.2 | 3.6% | 0.27 | enemy_shelter:walked-out +3.8, king_move +2.2, k +2.2, phase +1.9 | Strongly Invisible 6%, duck 5%, Instructors 4% |
| 1.3 | 2.0% | 0.94 | king_threat_unseen +4.1, king_threat +3.3, queen_raid +3.2, q +1.9 | Decent Chess Bot 4%, Greek Gift 3%, Knight Vision 2% |
| 1.4 | 23.5% | 0.48 | enemy_shelter:center +1.0, own_shelter:center +1.0, pawn_storm +1.0, p +0.8 | TA Baseline P 35%, TA Baseline A 32%, Decent Chess Bot 26% |
| 1.5 | 2.6% | 0.54 | own_shelter:luft +5.9, q +0.5, enemy_shelter:luft +0.4, back_rank_bare +0.4 | Strongly Invisible 4%, Instructors 4%, Greek Gift 4% |
| 1.6 | 10.3% | 0.57 | castle +1.1, own_shelter:center +1.0, enemy_shelter:center +0.9, capture +0.5 | Knight Vision 12%, Decent Chess Bot 12%, TA Baseline A 11% |
| 1.7 | 3.3% | 0.19 | king_leaves_home +2.5, king_move +2.4, k +2.4, own_shelter:walked-out +2.0 | Decent Chess Bot 4%, TA Baseline S 4%, Strongly Invisible 4% |
| 1.8 | 4.3% | 0.11 | own_shelter:advanced +2.9, sacrifice +0.6, phase +0.5, enemy_shelter:advanced +0.4 | TA Baseline P 7%, IAmAVirus 7%, TA Baseline A 7% |
| 1.9 | 11.1% | 0.49 | enemy_shelter:intact +1.4, own_shelter:fianchetto +1.4, enemy_shelter:fianchetto +0.9, capture +0.4 | Knight Vision 17%, Greek Gift 11%, Instructors 11% |
| 1.10 | 2.7% | 0.14 | own_shelter:open +3.3, enemy_shelter:open +2.5, phase +1.0, back_rank_bare +0.7 | IAmAVirus 7%, TA Baseline P 4%, TA Baseline S 4% |
| 1.11 | 11.2% | 0.50 | own_shelter:intact +2.7, enemy_shelter:intact +0.6, capture +0.4, fog_route +0.3 | duck 18%, IAmAVirus 15%, Strongly Invisible 15% |
| 1.12 | 4.4% | 0.77 | own_shelter:advanced +3.0, enemy_shelter:advanced +0.8, material_diff +0.5, material_trend +0.4 | Decent Chess Bot 6%, Greek Gift 6%, Knight Vision 6% |
| 1.13 | 1.7% | 0.98 | own_shelter:open +4.1, king_hunt_sacrifice +3.4, material_diff +1.2, phase +0.9 | Knight Vision 2%, Instructors 2%, TA Baseline A 2% |
| 1.14 | 3.9% | 0.91 | own_shelter:walked-out +2.6, phase +1.5, enemy_shelter:walked-out +1.1, material_diff +1.0 | Greek Gift 6%, Knight Vision 6%, Strongly Invisible 6% |
| 1.15 | 5.7% | 0.07 | own_shelter:one-gone +1.4, back_rank_bare +0.8, sacrifice +0.8, enemy_shelter:one-gone +0.6 | TA Baseline S 11%, IAmAVirus 11%, TA Baseline P 8% |

## Level 2 (general: plan)

| code | share | score | over-represented features | used most by |
| --- | --- | --- | --- | --- |
| 2.0 | 5.9% | 0.49 | walk_into_unseen +0.8, enemy_shelter:advanced +0.5, n +0.4, enemy_shelter:intact +0.3 | IAmAVirus 10%, duck 7%, Strongly Invisible 7% |
| 2.1 | 13.2% | 0.53 | p +0.5, pawn_storm +0.4, victim_walked_in +0.3 | TA Baseline P 19%, Knight Vision 18%, TA Baseline A 17% |
| 2.2 | 8.0% | 0.33 | p +0.4 | TA Baseline P 14%, TA Baseline A 14%, IAmAVirus 11% |
| 2.3 | 5.4% | 0.34 | vision_loss +0.8, r +0.7, q +0.5, own_shelter:fianchetto +0.5 | Instructors 7%, TA Baseline S 6%, duck 6% |
| 2.4 | 5.1% | 0.50 | king_leaves_home +1.1, king_move +1.0, k +1.0, enemy_shelter:one-gone +0.8 | Knight Vision 7%, Decent Chess Bot 6%, TA Baseline S 6% |
| 2.5 | 1.9% | 0.41 | back_rank_bare +3.0, enemy_shelter:fianchetto +1.2, enemy_shelter:luft +1.2, r +0.5 | Knight Vision 3%, Decent Chess Bot 2%, Instructors 2% |
| 2.6 | 3.9% | 0.53 | king_threat_unseen +2.4, king_threat +2.0, long_strike +0.8, r +0.5 | duck 5%, Greek Gift 5%, TA Baseline S 4% |
| 2.7 | 6.0% | 0.79 | material_diff +0.8, phase +0.6, r +0.4, enemy_shelter:advanced +0.4 | Greek Gift 8%, Strongly Invisible 8%, Knight Vision 7% |
| 2.8 | 5.3% | 0.75 | king_hunt_sacrifice +1.1, material_trend +0.7, vision_gain +0.6, pawn_storm +0.5 | Greek Gift 7%, Decent Chess Bot 7%, Knight Vision 7% |
| 2.9 | 4.2% | 0.09 | sacrifice +2.4, walk_into_unseen +0.8, k +0.3, king_move +0.3 | TA Baseline P 9%, TA Baseline A 7%, IAmAVirus 7% |
| 2.10 | 5.9% | 0.28 | forcing_chain +1.2, capture +1.2, fog_route +1.1, capture_unseen +1.0 | TA Baseline S 11%, TA Baseline P 10%, TA Baseline A 9% |
| 2.11 | 13.8% | 0.53 | castle +1.3, enemy_shelter:intact +0.6, own_shelter:center +0.5 | IAmAVirus 15%, Strongly Invisible 15%, TA Baseline S 15% |
| 2.12 | 9.6% | 0.48 | enemy_shelter:center +0.7, pawn_storm +0.3, p +0.3 | duck 12%, Strongly Invisible 11%, Instructors 11% |
| 2.13 | 4.2% | 0.37 | king_move +1.0, k +1.0, own_shelter:open +0.9, phase +0.6 | IAmAVirus 6%, Decent Chess Bot 5%, duck 5% |
| 2.14 | 3.5% | 0.70 | q +1.6, queen_raid +1.6, own_shelter:fianchetto +0.6, vision_loss +0.6 | Strongly Invisible 5%, Greek Gift 5%, Decent Chess Bot 4% |
| 2.15 | 4.2% | 0.81 | forcing_chain +1.5, fog_route +1.5, capture +1.5, capture_unseen +1.3 | Knight Vision 6%, Decent Chess Bot 5%, Greek Gift 5% |

## Level 3 (officer: tactic)

| code | share | score | over-represented features | used most by |
| --- | --- | --- | --- | --- |
| 3.0 | 3.4% | 0.58 | enemy_shelter:open +3.0, phase +1.1, own_shelter:open +0.8, king_move +0.7 | Instructors 4%, Greek Gift 4%, TA Baseline A 4% |
| 3.1 | 4.0% | 0.40 | walk_into_unseen +1.0, enemy_shelter:one-gone +0.7, sacrifice +0.6, enemy_shelter:open +0.4 | TA Baseline A 5%, TA Baseline S 5%, Greek Gift 4% |
| 3.2 | 5.1% | 0.51 | walk_into_unseen +1.1, enemy_shelter:advanced +0.6, enemy_shelter:one-gone +0.4, n +0.4 | Strongly Invisible 6%, Decent Chess Bot 6%, Knight Vision 6% |
| 3.3 | 3.8% | 0.47 | enemy_shelter:luft +1.9, own_shelter:one-gone +1.3, enemy_shelter:intact +0.3 | IAmAVirus 5%, Knight Vision 4%, Decent Chess Bot 4% |
| 3.4 | 2.8% | 0.53 | enemy_shelter:fianchetto +3.3, back_rank_bare +1.1, own_shelter:intact +0.3 | Instructors 3%, Decent Chess Bot 3%, Strongly Invisible 3% |
| 3.5 | 5.5% | 0.49 | b +0.6 | IAmAVirus 7%, Greek Gift 7%, Strongly Invisible 6% |
| 3.6 | 8.9% | 0.51 | — | Strongly Invisible 10%, Instructors 9%, TA Baseline A 9% |
| 3.7 | 10.1% | 0.47 | p +0.5, pawn_storm +0.4, enemy_shelter:center +0.3 | TA Baseline P 12%, Decent Chess Bot 11%, TA Baseline A 11% |
| 3.8 | 7.3% | 0.47 | forcing_chain +0.8, capture +0.7, victim_walked_in +0.7, fog_route +0.6 | TA Baseline P 12%, TA Baseline A 10%, Decent Chess Bot 9% |
| 3.9 | 10.1% | 0.52 | enemy_shelter:center +0.5, pawn_storm +0.4, p +0.4 | Strongly Invisible 11%, duck 11%, Knight Vision 11% |
| 3.10 | 5.3% | 0.50 | enemy_shelter:advanced +0.8, castle +0.4, own_shelter:center +0.3 | IAmAVirus 6%, duck 6%, Decent Chess Bot 6% |
| 3.11 | 5.0% | 0.54 | queen_raid +1.0, long_strike +0.7, q +0.7, capture_unseen +0.6 | TA Baseline S 7%, Greek Gift 6%, Instructors 6% |
| 3.12 | 7.1% | 0.50 | capture +0.6, enemy_shelter:one-gone +0.5, fog_route +0.5, long_strike +0.5 | TA Baseline P 9%, TA Baseline S 9%, IAmAVirus 8% |
| 3.13 | 2.9% | 0.49 | enemy_shelter:walked-out +1.8, king_leaves_home +1.6, phase +1.3, k +1.2 | Decent Chess Bot 4%, duck 4%, Greek Gift 3% |
| 3.14 | 8.5% | 0.33 | — | TA Baseline S 13%, IAmAVirus 12%, TA Baseline A 11% |
| 3.15 | 10.2% | 0.62 | — | Decent Chess Bot 13%, Greek Gift 12%, Knight Vision 11% |

## Ours vs the top six (level 1)

Share of IAmAVirus windows (555) vs top-six windows (22,019) per level-1 code, with the code's score:

| code | what it is | ours | top six | ratio | score |
| --- | --- | --- | --- | --- | --- |
| 1.15 | own shelter one pawn gone, back rank bare, giving material | 11.2% | 4.6% | 2.4x | 0.07 |
| 1.10 | open shelters, back rank bare | 6.8% | 2.3% | 2.9x | 0.14 |
| 1.8 | own shield pushed two or more, giving material | 7.4% | 3.5% | 2.1x | 0.11 |
| 1.3 | hidden king hunt (unseen king threats, queen raids) | 0.7% | 2.4% | 0.3x | 0.94 |
| 1.14 | chasing a king that walked out | 0.9% | 4.8% | 0.2x | 0.91 |
| 1.1 | material edge with weakened shelters on both sides | 5.6% | 8.9% | 0.6x | 0.78 |

Caution: v1 codes mix situation (shelters, material) with action (move kinds), so a losing code can describe a bad position as much as a bad choice. v2 separates them: the situation conditions the chief, the code quantizes only what the side does.
