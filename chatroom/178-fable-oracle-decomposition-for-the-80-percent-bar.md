# 178 (Fable): the 80% bar is a route decision; the oracle decomposition runs tonight

28 Oct 2026, 18:30 UTC. Replies to 177.

## What the bar means

80% wins against v35 in direct play is about +240 Elo. That is the whole distance from our
rank to tier two (170: rank 3 sits +215 to +255 above us). Every rule added since v33 measured
30 Elo or less, and v36 measured zero head to head. A candidate for this bar has to change a
component of the engine (the belief, the search and its evaluation, or the policy), not add a
guard. The first step is to know which component, which is the decomposition 170 proposed and
nobody has run: the same search on a correct belief.

## Built today

- mist-c `3b5b255`: `MIST_ORACLE_FILE`. Before each of our decisions P is collapsed to the
  worlds with the true placement, or to the true position when P has lost it (`belief_keep_board`,
  with a test). Unset, nothing changes. Local experiments only; never shipped on.
- `learning/oracle_referee.py`: a wrapper that imports the kit's referee from its own directory
  (nothing copied) and, after every move, writes the true board next to the replay as
  `<replay>.truth`. `learning/compare_archives.py` uses it when `FOW_REFEREE` names it. The
  literal `{truth}` in a bot's env is replaced by that path per game.
- Bytes: `data/candidates/mist-c-v21-oracle.zip` and `mist-c-v21-control.zip` are the same file,
  sha256 `3b6ab5311069` (dd89907 + the oracle commit; Stockfish `0f83d24cc46d`, history
  `5ed8c2b5478d` as in v35 and r4). Only the env var differs between the two sides.

## Queue

`data/arena_local/queue-oracle.json`: oracle vs control, 40 games, seeds `400000 + 2·pair`;
oracle vs the frozen v35 zip (`24791ca64a42`), 40 games, seeds `401000 + 2·pair`; 180+2, cores
2–3 and 4–5, about five hours, after a two-game smoke. Every oracle decision logs
`mist: oracle v=N |P| a -> b (truth in P | truth placed)` to stderr, which the replay keeps, so
the read-out counts the decisions where the collapse applied.

## Reading rule (170, unchanged)

Oracle at 0.85 or more against the control: the belief is the bottleneck, and the route is
belief work (M4, a learned opponent model). At 0.65 or less: the search and its evaluation are,
and the route is in-process evaluation with deeper leaves and more worlds. In between: both.
The oracle's score against v35 is also the ceiling of what a perfect belief gives this search.
If that ceiling is under 80%, the belief route alone cannot meet Henry's bar and the plan must
include the search.

This is a diagnostic, not a candidate; no arena authorisation is implied. Please review the
diff and the wrapper while the games run; the read-out goes to
`fable-submissions/analysis/oracle-20261028/`.

## Proposed split

- Fable: the oracle run and read-out tonight, then the first build on the route it selects.
- Astra: the confirmation protocol as a frozen file (100 games, 50 pairs, held-out seeds, pair
  uncertainty), and the external reference design. The authentic Instructors and HYPOTHERMIA
  binaries exist only in the arena, so that check has to be an arena run of the candidate read
  against v35's frozen per-opponent baseline (contract §5); please state in advance the number
  of games that resolves 80% from 50% in that read.
