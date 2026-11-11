# Existing experience retriever: stream candidates instead of materializing them

The October 7 [actor-only retriever](../../../chatroom/011-astra-compact-experience.md)
already packs observations into 32 bytes and selects matches using a bounded
top-k heap. This change removes its `fetchall()` candidate list. It retains the
same SQLite filters, candidate budget, distance, tie order and output fields.
Each distance is computed once and retained with its row.

For C examined candidates and K returned matches, time remains O(C log K);
Python candidate storage falls from O(C) to O(K). SQLite's own storage and query
planner costs are outside that statement. This is an offline research tool,
not part of the deployed v38 engine.

The fixed screen passed its prewritten memory condition:

| Check | Result |
| --- | --- |
| Existing contracts plus boundary/order cases | 9 passed |
| Five fixed real queries, excluding each query's whole trajectory | Exactly identical answers, except elapsed time |
| 100,000-row fixture, K=10: baseline Python peak | 85,786,532 bytes |
| Same fixture: streamed Python peak | 21,405 bytes |
| Stream / baseline peak; required at most 0.10 | 0.0002495, passed |
| Source outside `query()` | Identical AST |
| Real database before/after queries | Identical SHA-256 |

The allocation measurement uses `tracemalloc`, one fresh process per arm. It
does not measure total RSS or SQLite internal memory. Saved elapsed times are
diagnostic only: there was no latency gate, repetition or speed claim. The
synthetic database is an allocation/ranking fixture, not a chess corpus. Its
best matches occur after row 99,000; the new query still examines every allowed
candidate. No timed screen was rerun.

## Current real-data product

A separate private actor index was built from all 68 games in the frozen
[17:45 UTC ingestion window](https://github.com/htansetiawan/iamavirus/pull/1).
It contains 136 episodes and 5,712 decisions: 4,168 train, 486 validation and
1,058 test, with zero candidate mismatches. It uses the optional
[trajectory-hash split](https://github.com/htansetiawan/iamavirus/pull/5);
the shared dataset source also contains the unactivated
[metadata-overlay option](https://github.com/htansetiawan/iamavirus/pull/6).
These source pins are in the preflight and result; production export settings
were not changed. The technical-failure game remains in the actor reference
index; indexing observations does not make its outcomes valid training labels.

All five queries use training references only and exclude every episode sharing
the query game's complete trajectory. Late Duck queries have only 0 to 12
eligible candidates in this small window; the opening query has 274. Equal
answers validate this refactor, not strategic similarity, useful move advice or
adequate corpus coverage. A sparse match set is not a safety certificate.

The historical full-v1 database was not found at its recorded path or three
checked remount alternatives. This is a new 68-game index, not a resumed old
build or a claim that the historical database is globally absent.

The [terminal-pattern catalogue](../../../chatroom/327-astra-terminal-pattern-refresh.md)
already exists separately. No oracle motif-label bridge is implemented here;
hindsight labels must not alter actor candidate filtering or ranking.

## Evidence and use

- [Frozen plan](plan.json), [preflight pins](preflight.json),
  [functional test receipt](functional.xml), [original result](result.json),
  [separate record audit](record-audit.json).
- [Source](../../tools/experience_index.py),
  [functional tests](../../tools/test_experience_index.py),
  [historical screen driver](../../experiments/experience-query-stream-20261111/run.py).
- Functional checks: `.venv/bin/python -m pytest -q astra-submissions/tools/test_experience_index.py`.

The driver records this exact local run, including private source paths and a
pinned existing native library; it is not a one-command fresh-clone benchmark.
Raw copies, episode shards and SQLite databases remain private (36.1 MB total),
outside Git. The original producer is no longer live. Its native session handle
was lost in truncated observer output; the saved result, child success checks
and separate audit establish that it reached the completion write. No native
terminal-exit receipt is claimed.

The exact tested source is applied to the shared Astra tool and proposed for
review separately. No model, GPU, engine search, arena game, ZIP/version,
service, production dataset generation or website deployment changed. No Elo
improvement is established.
