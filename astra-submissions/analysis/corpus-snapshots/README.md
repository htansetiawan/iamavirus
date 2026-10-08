# Public replay refresh — 2026-10-08 00:25 UTC snapshot

The bounded, paginated snapshot contains **500 completed games across all teams
and outcomes**. All 39,191 true board frames and both players' observations pass
the pinned native referee validation. There are 438 new downloads and 62 cache
hits, zero quarantined games, and 500 distinct complete move sequences. Outcome
counts are 262 White wins, 218 Black wins, and 20 draws. This is a recent sample,
not a uniform opponent distribution.

Raw data and immutable fetch receipts:
`/media/henrytan/seagate/iamavirus/astra/corpus/recent-20261008T0023/`

Curated artifacts:
`/media/henrytan/seagate/iamavirus/astra/corpus/recent-20261008T0023-curated/`

| Artifact | Contents |
| --- | --- |
| `episodes.jsonl.gz` | 1,000 player histories; actor inputs separate from privileged offline labels |
| `actor-observations.jsonl.gz` | Whitelisted observation histories and own actions, with no truth boards, outcomes, or danger labels; directly accepted by the SSL loader |
| `new-games.jsonl.gz` | Histories absent by game ID and complete move hash from all listed v1–v4 splits |
| `index.jsonl` | Per-game hashes and overlap memberships, retained when assigning future splits |
| `curation.json` | Native/source/artifact hashes, counts, and split-audit receipts |

There are **38,691 decisions and 77,390 observation events**. The overlap audit
finds **477 new games with 37,073 decisions**. The other 23 games match the v3/v4
datasets: 20 training, two validation, and one test. The audit reads only shard
membership metadata; test actor/target records are not deserialized or scored.
Shared openings and partial histories can still overlap between distinct games.

No existing training split is changed. These are unassigned development pools,
including the actor-only file. Keep both colors and duplicate full histories
together when constructing the next split; using validation observations for
SSL would also contaminate that validation set.

The [compact repository receipt](recent-20261008T0023.json) pins the full outputs.
`tools/collect_recent.py` collects sequentially with API backoff and validates
each replay. `tools/curate_snapshot.py` reuses its isolated native library and
checks every generated actor candidate list against the true legal list.
