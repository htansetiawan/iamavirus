# 170 (Fable): re-analysis for the top three, and the gym request

Henry asked two things: improve the local gym (ledger 13:47Z, for Astra) and re-analyse how we
get to rank 2 or 3. The analysis is `docs/top3-reanalysis-20261027.md`. Its core:

- Three tiers since 13 October: Greek Gift; KV/SI/Dec/CF (0.4 to 0.6 among themselves); Mist,
  Instructors, duck and us (0.22 to 0.38 against tier two, at most 0.14 against GG). Rank 3 means
  becoming a tier-two engine, +215 to +255 Elo. Mist Opportunities, the other Obscuro-style
  engine, is in tier three with us.
- Losses are a material bleed over 75 to 85 plies with a queen asymmetry (ours lost outright
  0.52 to 0.57 against GG, Dec, duck; theirs 0.37 to 0.41); we sacrifice twice as often and make
  fewer hidden king threats than the teams above us.
- Levers: guards and search time are measured and small; belief quality has never been sized.
  Proposed first experiment after the 20:00Z checkpoint: v35 with the true board as its belief
  (oracle) against v35, 40 games, to decide between a belief route (M4 + opponent model) and a
  search route (in-process evaluation + capacity). Second: imitation ceiling on Greek Gift's
  590k recorded decisions with its own view.

Astra: please challenge the tiers and the queen numbers (my scripts are inline in this session;
the matrix is reproducible from `data/raw/accepted.jsonl`), and say whether the oracle change
belongs in `main.c` behind `MIST_TRUTH_SEQ` or as a separate harness. The gym ladder is the
prerequisite for measuring any of it.
