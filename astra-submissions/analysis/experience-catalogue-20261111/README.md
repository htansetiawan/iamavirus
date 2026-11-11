# Search tactical examples; keep hindsight separate from actor retrieval

We now have a source-bound, indexed catalogue of terminal patterns and a way to
annotate the existing actor retriever's results **after their ranking is fixed**.
It is an analyst tool. It does not select moves or run inside v38.

This connects existing work rather than inventing a strategy algorithm:
[011](../../../chatroom/011-astra-compact-experience.md) already implemented the
packed actor index; [027](../../../chatroom/027-astra-strategy-first-and-misty.md)
proposed skill contracts; [327](../../../chatroom/327-astra-terminal-pattern-refresh.md)
already labelled terminal motifs; [PR 7](https://github.com/htansetiawan/iamavirus/pull/7)
removed the actor query's candidate list. The additions here are a separate
SQLite facet index and an exact source-identity join from chosen actor matches
to hindsight labels. Actor features, SQL filters and ranking are unchanged.

## What is available

| Capability | Implementation and evidence |
| --- | --- |
| Browse examples by composable roles | Filter terminal kind, attacker piece role, hidden status and presence of true-board safe alternatives. No player-name filter. |
| Bind the label to the correct decision | Match game, seat, predecision ply and exact replay SHA-256. Stale source identity yields a mismatch status, with no label attached. |
| Keep retrieval independent of hindsight | Finish the original actor query first; retain its complete result under `actor_result`; add separate `oracle_annotations` keyed by decision ID. |
| Audit a known example | Duck's `abt27me2`, Black before ply 140: `Kg4-h4` enters the hidden Rh1 line; true-board safe set is only `Kg4xf4`. This is the already reported 411 positive control. |

The catalogue contains **368 inspected games / 736 seats / 357 terminal
examples**. The first 300 games and their 600 seat records are retained exactly
from 327. The additional 68 are the complete current window already inspected
in 411–413. Their 5,780 frames agree with the course referee; all 1,165 terminal
candidate actions agree with the existing native one-ply checker. There are 66
new king-exposure endings; the draw and opponent process-failure game acquire
no king-exposure motif. Neither cohort is a fresh model holdout.

| Terminal class | Examples across these two cohorts |
| --- | ---: |
| Existing attack left unresolved | 143 |
| King walk into attack | 133 |
| King capture into attack | 66 |
| Own move opens the king's line | 15 |

Nineteen examples match `king_bait + rook attacker + all attackers hidden +
safe alternative exists`. These are searchable terminal cases, not a measured
19-case strategy success rate: the catalogue has no denominator of all offered,
refused or successful bait opportunities. Likewise, a safe move on the true
board need not be identifiable from the player's fog information.

## What the real queries reveal

A separate private actor index over all 368 games contains 31,318 decisions:
24,247 train references, 3,203 validation and 3,868 test. Seven fixed queries
retain every original actor-result field/rank except elapsed time. Each query
excludes its whole complete trajectory and searches training references only.
One additional self-reference control proves an exact real-source join; it is
explicitly excluded from any retrieval-quality interpretation.

| Query game / predecision ply | Eligible actor candidates | Terminal labels among top references |
| --- | ---: | ---: |
| abt27me2 / 139 | 1 | 0 / 1 |
| abt27me2 / 138 | 75 | 1 / 10 |
| x0l4i8ns / 83 | 26 | 0 / 10 |
| x0l4i8ns / 82 | 12 | 0 / 10 |
| abt27me2 / 0 | 1,537 | 0 / 10 |
| qi16y1oe / 101 | 1 | 0 / 1 |
| qi16y1oe / 100 | 34 | 0 / 10 |

Only **one of 52 returned references** has a terminal label. That is label
availability on seven selected queries, not accuracy: a nonterminal reference
can still be useful, and a terminal reference can be irrelevant. The current
query filters by exact own king square and own piece count, then compares
categorical visible squares. It cannot yet recognize equivalent role geometry
across different boards or infer a multi-move plan. Even this larger window
provides just one eligible reference for the Duck king-walk query.

The missing runtime capability remains an observable trigger: infer the
relevant piece roles and uncertainty from permitted history, predict opponent
responses, and compare candidate actions through rules-exact search. Retrieving
hindsight labels does not implement that trigger. Existing negative style,
response-model, learned-ranker and playing gates are not reopened by this tool.

## Use locally

```sh
.venv/bin/python astra-submissions/tools/experience_catalogue.py browse \
  --database data/astra-spool/experience-catalogue-20261111/catalogue.sqlite \
  --kind king_bait --attacker R --all-hidden --no-forced --limit 10

.venv/bin/python astra-submissions/tools/experience_catalogue.py query \
  --actor-database data/astra-spool/experience-catalogue-20261111/actors/actors.sqlite \
  --catalogue-database data/astra-spool/experience-catalogue-20261111/catalogue.sqlite \
  --view YOUR_64_CHARACTER_OBSERVATION --side 1 --exclude-game abt27me2
```

The two databases are separate. Both query paths open read-only connections.
The builder checks exact replay identity; it does not by itself prove a supplied
label correct. The label's upstream referee/native audit remains necessary.
Source labels, actor shards, raw copies, databases and per-query rich results
remain outside Git: 25.0 MB total. Public results contain counts and hashes.

## Verification and limits

Six functional cases plus four validation subtests pass: role filtering,
predecision/source binding, label mutation without actor-rank change,
held-out/excluded reference isolation, failed-build cleanup and no overwrite.
The first test run exposed a test-fixture assumption about decision IDs; the
assertion now uses IDs returned by the existing builder. The initial failure
receipt is retained; catalogue library code was unchanged by that correction.
The CLI browse also returns the requested role-filtered examples successfully.

The original curation session **46794 exits 0**. Separate saved-record review
reconciles all 368 replay hashes, every seat key, all 357 stored labels and all
52 returned actor references. It verifies training-only whole-trajectory
exclusion, unchanged input databases and absence of oracle actor columns.
This review does not rerun every referee/native calculation.

[Frozen plan](plan.json) · [preflight](preflight.json) ·
[initial test receipt](functional-initial.xml) · [final test receipt](functional-final.xml) ·
[original result](result.json) · [execution](execution.json) ·
[record audit](record-audit.json) · [CLI check](cli-smoke.json).

[Catalogue source](../../tools/experience_catalogue.py) ·
[functional tests](../../tools/test_experience_catalogue.py) ·
[historical curation driver](../../experiments/experience-catalogue-20261111/run.py).
The driver pins local private inputs and native libraries, rather than claiming
a one-command fresh-clone reproduction. No new API reads, model fit, GPU work,
bot search/match, arena ZIP/version, production dataset export, service change
or website deployment occurred. No strength or asymptotic speed claim is made.
