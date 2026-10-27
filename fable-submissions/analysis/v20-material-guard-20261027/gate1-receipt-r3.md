# Gate-1 receipt, release candidate r3 (27 Oct 2026, written 01:50 UTC before the gate-3 launch)

Per the decision contract, section 2. Astra's source/artifact review passed on
ff89313 (all 19 zip source members exactly ff89313; Stockfish and history bytes
identical to v35); pins in `astra-submissions/analysis/v36-execution-20261027/input-pins.json`.

## Artifact

- Zip: `data/candidates/iamavirus-v36-candidate-mist-c-v20-r3.zip`, sha256
  `5cdbb9caf8a3c990b63f3338a8501638d746bdf9a5d573f972c3325905e3cf60`.
- Source: mist-c `ff89313` (= v35's `97b60f1` + v20 piece term `539d4e3` + the
  v35-subset rule `7cf0727` + default λ `be26b1a` + fallback precedence `a71035e`
  + `guard_rule()` extraction `ff89313`); the later commit `2524f8e` is tests only.
  Members: `bin/stockfish` `0f83d24cc46d` and `data/history.bin` `5ed8c2b5478d`
  (both equal v35's), `src/main.c` `5bb5f9d8f056`, `src/front.c` `489f84128c89`.
- Effective settings: `run.sh` exports `MIST_STOCKFISH` and `MIST_HISTORY_TABLE`
  only; the piece term is on by default (λ 0.758, T 3, cap 20,000); `MIST_ASYNC`
  unset, so the round loop (10 PCFR+ iterations per 32 expansions) is deployed;
  fog hazards, uniform clause, material guard, depth: all v35 defaults. The
  bench queue passes empty `a_env`/`b_env`; no `MIST_*`/`FOW_*` variable is
  exported in the launching shell.

## Builds and start-up

- `build.sh` with gcc 13.3.0 (Ubuntu 24.04): 1.9 s, executable sha256 `6be96e13d8c5`.
- g++ 13 as the C front end (the zip's fallback path): executable `89aa7ee6fa9a`.
- Both answer `ready` immediately on the protocol handshake (well inside the
  15 s arena limit; the Stockfish workers and the 2.4 MB history table load at start).

## Tests

- `make test` on ff89313 and 2524f8e: exit 0. test_rules, test_belief, test_cfr,
  test_search (3 games, 57 decisions, 0 illegal, 0 king left capturable),
  test_guard, test_front (as White and as Black, incl. the exclusion precedence
  and the guarded legality fallback), test_rule (as White and as Black: the B1
  counterexamples as risk arrays, 5,000 random risk vectors for subset,
  non-empty and disabled-mode = v35 with and without the uniform clause, the
  sharpened-only fallback, king/queen/piece shares of disjoint events on a fixed
  three-world belief, taking the king charges no event, en passant credits the
  taken pawn, promotion applies and a promoted queen taken at once is the queen
  term's event), test_eval, test_sf.
- The three recorded B1 fatal positions replayed with the release source
  (gcc build, seeds 1, 2, 3, 2.5 s, v35 Stockfish and table, truth scored):
  05i9doxr:22 g7h8, rjaerwc3:25 a8d8, zmikg9zc:17 h6f5 on every seed; never
  fatal, never the B1 move.

## Smoke pair on the course referee, 180+2, cores 2–3 (queue `smoke-v36r3.json`)

| game | result | plies | r3's lowest clock at any move | end clocks (W/B) |
|---|---|---|---|---|
| r3 White vs v35 | 1-0, king capturable | 86 | 35.9 s | 35.9 / 35.5 |
| v35 White vs r3 | 1-0, king capturable | 106 | 24.7 s | 30.5 / 24.7 |

Receipt `data/arena_local/receipts/smoke-v36r3.json`: state complete, attempted 2,
failed 0, 01:22:42Z to 01:39:08Z. No crash, illegal move or forfeit.

## Runner used for the gate (iamavirus `63f7265`)

`learning/arena_local.py` sha256 `abcd813bf4fe`, `learning/compare_archives.py` `e3958b95be2c`:
every started game is recorded (failed or unknown results keep their row with
`attempt: failed`), scheduling and the cap count attempts so no pair is retried,
the deadline is checked before each game with a 2,450 s fit budget (the longest
legal 180+2 game), the game in flight is killed at the cap less a 30 s reserve
with its whole process tree, and a run receipt is kept
(`data/arena_local/receipts/queue-v36r3.json`). Tests
`learning/tests/test_arena_local.py` (4, incl. a real grandchild kill) pass.
A row whose reason starts with "wall cap" or "referee exit" is a runner
failure, not a bot forfeit.

## Opponent environment (read only, untouched for the duration)

Misty wrapper `data/zoo/misty-v16.zip` `62d8d389c2ed` pointing at
`~/fable-persist/scratchpad/misty`: interpreter Python 3.13.13; packages chess 1.11.2;misty-chess 0.1.3;numpy 2.5.3; Stockfish
`0f83d24cc46d` (the same Stockfish 19 build as ours). Astra's
`opponent-environment.json` pins the same.

## Gate 3 launch

Queue `data/arena_local/queue-v36r3.json` sha256
`2ee4f745cf1691fe25ad157986c678775f337cca249c897303cf75e02aac4e33`:
v36r3-vs-v35 40 games (seeds 200000 + 2·pair), v36r3-vs-misty 32 (201000 + 2·pair),
v35-vs-misty-r3 32 (the same seeds), slots 2,3 and 4,5, `--wall-hours 12`.
Launched under Henry's execution go-ahead relayed by Astra after this receipt.
