# IAmAVirus replay analysis

369 arena games of IAmAVirus (all versions), 11893 of our decisions, labelled from the true board offline (`learning/curate.py`; rows in `gold/`).

## Record by version

| version | W | D | L |
|---|---|---|---|
| 2 | 4 | 0 | 0 |
| 3 | 10 | 0 | 0 |
| 4 | 103 | 6 | 153 |
| 5 | 26 | 2 | 8 |
| 6 | 2 | 0 | 6 |
| 7 | 2 | 0 | 10 |
| 8 | 9 | 0 | 15 |
| 9 | 7 | 0 | 3 |
| 10 | 3 | 0 | 0 |

## How the losses end (terminal class, by version)

| version | already-lost-no-safe-move | exposed-king-to-hidden-attack | exposed-king-to-visible-attack | king-moved-into-hidden-attack | technical:Illegal move |
|---|---|---|---|---|---|
| 4 | 35 | 50 | 0 | 66 | 2 |
| 5 | 2 | 2 | 0 | 4 | 0 |
| 6 | 2 | 2 | 0 | 2 | 0 |
| 7 | 1 | 2 | 1 | 5 | 1 |
| 8 | 6 | 0 | 0 | 9 | 0 |
| 9 | 1 | 0 | 0 | 2 | 0 |

## Decision-level hazards, by version

| version | decisions | fatal moves | fatal with a safe alternative | exposed ≥3 to a capture | …capturer hidden | …and punished next ply |
|---|---|---|---|---|---|---|
| 2 | 58 | 0 | 0 | 7 | 5 | 2 |
| 3 | 256 | 0 | 0 | 20 | 19 | 4 |
| 4 | 8630 | 151 | 116 | 818 | 714 | 293 |
| 5 | 1073 | 8 | 6 | 66 | 64 | 13 |
| 6 | 199 | 6 | 4 | 30 | 25 | 13 |
| 7 | 446 | 9 | 8 | 46 | 42 | 19 |
| 8 | 886 | 15 | 9 | 80 | 76 | 33 |
| 9 | 314 | 3 | 2 | 25 | 23 | 11 |
| 10 | 31 | 0 | 0 | 1 | 1 | 0 |

## Record by opponent (all versions)

| opponent | W | D | L |
|---|---|---|---|
| TA Baseline S | 13 | 3 | 51 |
| TA Baseline P | 35 | 3 | 23 |
| Apricot Squad | 56 | 1 | 3 |
| TA Baseline A | 15 | 1 | 34 |
| baseline.py | 46 | 0 | 0 |
| duck | 1 | 0 | 25 |
| Greek Gift | 0 | 0 | 14 |
| Instructors | 0 | 0 | 14 |
| Decent Chess Bot | 0 | 0 | 13 |
| Knight Vision | 0 | 0 | 10 |
| Strongly Invisible | 0 | 0 | 8 |

## Decisions that handed over 5+ points and were punished (197)

| game | ver | ply | move | exposure | capturer hidden | opponent reply | result |
|---|---|---|---|---|---|---|---|
| krs4thaf | 4 | 35 | Qe7h4 | 9 | True | h1h4 | W |
| eisyf537 | 4 | 74 | Qe3g5 | 9 | True | g8g5 | L |
| 01rlkam1 | 4 | 37 | Qa5b4 | 9 | True | e4b4 | L |
| dgb115t7 | 3 | 23 | Qd8d4 | 9 | True | e3d4 | W |
| upp14gpy | 2 | 30 | Rd1d8 | 9 | False | f6g7 | W |
| kd78fva1 | 7 | 67 | Qh4d4 | 9 | True | g1d4 | L |
| 7vrfj37u | 7 | 18 | Qd2c2 | 9 | True | d4c2 | L |
| 9tivk1gi | 4 | 47 | Qd7b5 | 9 | True | b1b5 | W |
| dyqy8bkm | 4 | 18 | Qd1d5 | 9 | True | a5d5 | L |
| sphpx0pm | 4 | 86 | Qc6f3 | 9 | True | f8f3 | D |
| j8zn0ugw | 6 | 34 | Pc4c5 | 9 | True | c3e2 | L |
| 6blt5n5j | 6 | 52 | Qd1e2 | 9 | True | e4e2 | L |
| 7tkm78ho | 6 | 35 | Qd8c7 | 9 | True | g3c7 | L |
| 9d1ds9jk | 4 | 26 | Qd6c5 | 9 | True | d8d1 | L |
| lv3458qt | 4 | 7 | Qd8d5 | 9 | True | c3d5 | L |
| 5gpca5ax | 8 | 56 | Ph4h5 | 9 | False | c1d1 | L |
| igofgvq3 | 8 | 29 | Kg8h8 | 9 | False | g5h4 | L |
| d8u3rvlf | 8 | 28 | Qd1d6 | 9 | True | d8d6 | L |
| sojhp80k | 8 | 39 | Be6d7 | 9 | True | e1e7 | L |
| i3do06tu | 8 | 63 | Qh7d3 | 9 | True | e3d3 | L |
| zsrjlxfm | 8 | 20 | Ke1c1 | 9 | False | e7e4 | L |
| 4f8tk3w6 | 5 | 48 | Qd4g7 | 9 | True | f7g7 | D |
| vltis7fc | 5 | 17 | Qd6e5 | 9 | True | f4e5 | L |
| o7xu51yc | 5 | 69 | Ra8a1 | 9 | False | e2g4 | W |
| edeqz93s | 9 | 31 | Qd7b5 | 9 | True | c3b5 | L |
| q3bi743n | 4 | 44 | Qe5e7 | 9 | True | d8e7 | W |
| r2q1onlw | 4 | 57 | Qd6h2 | 9 | True | g1h2 | L |
| f95k1os4 | 4 | 40 | Qa8b7 | 9 | True | d7b7 | L |
| i25lmwiu | 4 | 54 | Qe5b8 | 9 | True | f8b8 | W |
| x8wy2wap | 4 | 7 | Qd8d4 | 9 | True | f3d4 | L |
| un73u8b3 | 4 | 32 | Qd2e3 | 9 | True | b6e3 | W |
| bq28qwag | 4 | 24 | Bc1g5 | 9 | False | d8g8 | W |
| 00u9e1x9 | 4 | 31 | Qd8g5 | 9 | True | e3g5 | L |
| 77ltptjq | 4 | 37 | Qd8g5 | 9 | True | e3g5 | W |
| l2rw7eyz | 4 | 36 | Ne4f6 | 9 | False | d4e3 | L |
| so8hw2nz | 4 | 35 | Qc7c3 | 9 | True | e2c3 | L |
| ua84dgzo | 4 | 40 | Rf4f5 | 9 | False | a1d1 | L |
| 91xkr6ej | 4 | 22 | Qc3e5 | 9 | True | e8e5 | L |
| rdvmouxm | 4 | 86 | Qd3d4 | 9 | True | h8d4 | W |
| 9tjl5qe4 | 4 | 29 | Ra8d8 | 9 | True | c4a3 | W |

## Reading

- `fatal moves` are moves that left our king capturable on the true board; `fatal with a safe alternative` is the subset where the position still had a safe move, i.e. a decision failure rather than a lost position.
- `exposed ≥3` counts moves after which the opponent had an immediate capture netting at least three points (one-ply exchange arithmetic); `capturer hidden` means that piece's square was unseen in our view at the decision, i.e. a belief failure rather than a search failure.
- Rows carry the full view and true board, so any of these decisions can be replayed through any bot mode with `python -m learning.replay_bot <game> --plies <ply>`.
