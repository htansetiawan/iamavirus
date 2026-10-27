# Gate-1 receipt, mist-c a71035e (the fallback-precedence correction), 27 Oct 00:45 UTC

Not a release receipt: r3 (rule extraction and tests) is still to be frozen.

- Source: mist-c `a71035e` = `be26b1a` (default piece term) + `front_exclusions`,
  `front_best_allowed_avoiding`, the main.c call sites and `tests/test_front.c`
  (4 files, +87/−13). Candidate zip `data/candidates/iamavirus-v36-candidate-mist-c-v20-r2.zip`
  sha256 `b2a2000c48da`; the superseded `iamavirus-v36-candidate-mist-c-v20.zip`
  (`49f65e1d93e5`, `be26b1a`) is untouched.
- Build: `make build/mist` with gcc 13.3.0 (Ubuntu 24.04); local executable
  sha256 `514ec95dece8` (informational: the arena compiles the zip's source itself).
- Tests: `make test` exit 0: test_rules, test_belief, test_cfr, test_search
  (3 games, 57 decisions, 0 illegal, 0 king left capturable), test_guard,
  test_front (as White and as Black, including the new exclusion-precedence and
  guarded-fallback checks), test_eval, test_sf all passed. Full log kept in the
  session scratchpad.
- Effective settings: no `MIST_*` or `FOW_*` variable is exported in the shell
  that ran the replays and benches; the zip's `run.sh` exports only
  `MIST_STOCKFISH` and `MIST_HISTORY_TABLE`; `tools/suite_run.py` adds
  `MIST_FORCE_MOVES`, `MIST_STOCKFISH`, `MIST_MAX_SECONDS`, `FOW_SEED`,
  `MIST_TRUTH_SEQ` and the explicit `--env` pairs (`MIST_HISTORY_TABLE`, and
  `MIST_PIECE_GUARD` for the B lanes); the bench queue passes empty `a_env`.
  `MIST_ASYNC` is therefore unset everywhere: the deployed search is the round
  loop (10 PCFR+ iterations, then up to 32 expansions in waves of two).
- Bench status: no bench running (0 referee, engine or Stockfish processes at
  00:45 UTC). The superseded candidate's run (`queue-v36c.json`, launched
  00:24:22Z) was stopped at about 00:40 UTC with three completed games, kept in
  `data/arena_local/games.jsonl` as diagnostics: `v36c-vs-v35` pair 0 as White
  won (66 plies, clocks 53.8/49.3 s); `v36c-vs-misty` pair 0 as White won, as
  Black lost. Cores 2–5 idle.
- Evidence correction (Astra): the pre-fix restore-all branch wrote no log
  marker and the replay records keep only the summary line, so the earlier
  statement that neither fallback path fired in 4,828 stored records is
  withdrawn. The four replay sets are pre-fix evidence; the fresh set and the
  games run on the frozen release artifact.
