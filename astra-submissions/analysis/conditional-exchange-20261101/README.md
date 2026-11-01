# Conditional exchange audit and forcing-clearance corpus

1 November 2026. **No new candidate or guard change.** The audit corrects a
short-horizon interpretation, produces a reusable tactical corpus, and checks
which of those opportunities unchanged v37 already finds.

## What the actual search saw

Exact v37 archive `41e02e280b61…`, six permitted-history runs: two previously
selected losses, three fixed seeds, 2.5-second search budget. Instrumentation
executes after the original move is fixed; it adds no truth, move filter or
extra solver iteration. All six first attempts succeed. Every exported
information-set strategy and value sum reconciles; **75,086 move transitions**
match the independent C++ rules, including board, side, castling and en passant.

| Case | Belief and search finding | Implication |
|---|---|---|
| duck `tjds234d:54`, Rxb7 | Nd6 has about 4.1% full-belief probability. Its sampled mass is 9.375%, 0%, 3.125%. Where present, search values Rxb7 worse than Rb3; other worlds reverse the preference. | Sampling variation and posterior quality remain relevant. The capture is not simply absent from search. More samples have not been tested as a same-clock improvement. |
| HYPOTHERMIA `92px495s:26`, Qxd5 | Be6 has 29.99% belief probability; sampled mass is 31.25%, 31.25%, 15.625%. Search sees ...Bxd5 and values that branch badly. Qxd5 still wins in expectation over the other worlds. | Changing a queen threshold from the single true outcome would not establish a better decision rule. |

The last-iterate queen probability is 54.8%, 66.6%, and 78.9% in these runs.
The preceding restricted-mixture full-game pilot already failed its gate; this
audit does not reopen it. Individual worlds can have other captures stronger
than the named one; its probability alone is not total capture risk.

## Correction: the tempting recapture is a trap

The old one-exchange label gives the bishop alternative no loss because
`Bxd5 Bxd5 Qxd5` appears to gain three points. It stops too early:

```
Bf3xd5 Be6xd5 Qd1xd5 Bd6xh2
                         ├─ Kg1h1 Qd8xd5
                         └─ Kg1xh2 Qd8xd5
```

The bishop move attacks the king and clears the d-file. The only immediately
surviving replies are Kh1 and Kxh2. After ...Qxd5 and the defender's best next
safe response, both branches have a net loss of **at least four points** from
the original position. The original `Qxd5 Bxd5 Bxd5` recapture line permits
the same combination. **This proves a continuation after those recaptures,
not a forced loss from either root move:** declining the recapture remains an
option. The actual search often declines it, so that behaviour was not an
exchange-accounting bug established by our earlier label.

`deflection-proof.json` records 6,560 legal-move/survival checks against the
course referee. A separate orthodox Stockfish probe also exposes the longer
combination; its centipawn scores are not Fog of War ground truth. That probe
retains its setup error and two Python UCI adapter hangs; owned processes were
stopped, and a bounded direct-pipe implementation completed. These were not
failed or retried policy tests.

## A composable pattern with executable examples

The miner scans the latest 5,000 cached games involving our reference/leading
teams, completed since 29 October. It finds 37 candidate recorded sequences.
Six pass a stronger proof: the first capture attacks the king, every surviving
reply moves that king, the nominated slider capture remains safe after each
reply, and the defender's best next safe response leaves a gain of at least two.

| Attacker | Defender | Game / ply | Clearance → capture | Proven minimum gain |
|---|---|---|---|---:|
| IAmAVirus v35 | Strongly Invisible | `2obip599:23` | Bxh2 → Rxd1 | 5 |
| Instructors v4 | RATIRL | `5ug2qtkb:61` | Bxf2 → Rxd7 | 5 |
| Instructors v4 | Crimson Fog | `svu0zmtm:33` | Bxb2 → Rxc2 | 2 |
| Cranberry Lemon v1 | duck | `rzr3p3jl:53` | Bxg4 → Rxf4 | 3 |
| duck v6 | Instructors | `q6wgifb9:38` | Bxh7 → Qxd4 | 4 |
| HYPOTHERMIA v4 | Lost Signal | `axhilosk:29` | Bxh2 → Rxd5 | 5 |

The four hidden-slider cases are recorded as such. The corpus is an offline
labelled set, not an observed input to the model or an arena frequency estimate.
Full replay validation and **16,894 further course-referee checks** validate
all six examples and every proof branch. The miner initially encountered a
null timestamp in the archive index; that pre-scan failure is retained and
missing dates are now excluded.

Unchanged v37 was then run on all six attackers' permitted histories, one
fixed seed at 2.5 seconds. **It chooses the recorded tactic in four of six**,
including our v35 tactic, both Bxh2 examples and duck's Bxh7. In `5ug2qtkb` it
chooses g4xh3 (a pawn capture); in `rzr3p3jl` it chooses Bf5e6. Neither is immediately fatal.
Those alternatives are not automatically errors: their posterior risks and
other continuations have not yet been compared. Six selected positives are
not a skill rating, a win rate, or a release gate.

## What this changes next

Use these verified forcing continuations to assess queen/rook exchange labels
and offensive opportunity tests. Do not treat "zero three-ply material loss"
as a validated safe alternative, and do not tune a global guard from this
example. Investigate the two unselected opportunities before adding a special
rule or model feature. The existing engine demonstrably has this tactical
capability in some observation histories.

Evidence: `plan.json`, first `receipts.jsonl`, `summary.json`, compressed
`*.audit.json.gz`, `deflection-proof.json`, `clearance-corpus.json`,
`clearance-corpus-validation.json`, `ability-plan.json`,
`ability-receipts.jsonl`, and `ability-summary.json`. Sources are in the
matching `astra-submissions/experiments/conditional-exchange-20261101/`.
`archive_evidence.py unpack` restores the raw audit JSON, verifying original
receipt hashes, before `run.py verify`. Rebuilding requires the pristine v37
extraction produced by the preceding stable-mix builder. No GPU or live
source/default change; no numbered ZIP is produced.
