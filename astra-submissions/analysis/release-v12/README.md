# Astra v12 release gate

The candidate is [iamavirus-v12-hybrid.zip](../../iamavirus-v12-hybrid.zip),
SHA-256 `a5f806d0039f514006f3af902767557ad35137d9d02e2779181d438eb5b47cf3`.
Its runtime and Stage A v1 model are identical to Fable's earlier exposure-only
archive `d549f8b5379d`, recovered from Git `9614f6f`. Relative to **arena v10**,
the change prices the opponent's best immediate net capture anywhere on the
board after our move, rather than only the moved piece's destination. Astra
owns the independent validation and release; Fable authored this engine change.

This is an arena-trial candidate. It has not established an Elo improvement or
consistent wins against Duck or TA A/S. Their private executables are not
available locally. The live monitor continues to collect their completed arena
games.

## Frozen comparison

[candidate-freeze.json](candidate-freeze.json) records every original source
and model hash before prospective gate replays were opened. The staging label
was initially 13. Fable then removed superseded v12 archives, so the user's
`max(Fable archive major) + 1` rule required release label **12**. The freeze
is preserved unchanged; [label-change.json](label-change.json) maps the paths.
Archive labels are separate from arena upload numbers.

Both arms use hybrid mode, identical Stage A v1 model bytes, seed 777,
400,000 search nodes per queried decision, and each colour's own-decision
stride of six. Actual losing final decisions are included separately.
The engine receives only its observations and own moves; true boards label
the resulting choices offline. The recorded game then continues with its
actual move, not the engine's counterfactual choice.

[gate-manifest.json](gate-manifest.json) fixes all game IDs, replay hashes,
opponents, colours, versions, and selection rules. Historical data consists of
up to twelve most recent pre-cutoff seats per target opponent and colour in
the monitor snapshot, including wins. Prospective data is every eligible
target game in that snapshot under the previously declared post-19:15 UTC,
SHA-256-odd split. Five prospective games were available; their all-loss
outcomes were incidental to that selection, not an outcome filter.

## Replay results

| Instrument | Arena v10 | Astra v12 |
|---|---:|---:|
| Historical immediate king losses / 274 decisions | 20 | 20 |
| Historical avoidable king losses / 262 survivable decisions | 8 | 8 |
| Historical moves exposing at least 300 cp / 254 nonfatal decisions | 21 | 12 |
| Historical mean exposure on nonfatal decisions, cp | 63.88 | 41.36 |
| Prospective immediate king losses / 40 decisions | 6 | 6 |
| Prospective avoidable king losses / 39 survivable decisions | 5 | 5 |
| Prospective moves exposing at least 300 cp / 34 nonfatal decisions | 4 | 2 |

Historical exposure counts by opponent: Duck **7 → 4**, TA A **3 → 1**,
TA S **11 → 7**. No queried choice flipped from immediately safe to fatal,
or the reverse, in either dataset. Forty-seven historical choices and five
prospective choices changed.

Exposure is an approximate one-ply net-capture label, not a full exchange
search. Decisions within a game are dependent. These are offline diagnostic
results, not 314 independent matches or a claim about Elo. The prospective
set is particularly small. Full per-decision records, binary/model hashes,
and the common measurement source are retained here.

## Correctness and packaging

A clean ONNX-enabled GCC build passed all nine C++ unit suites and
**18,625 / 18,625** course-referee differential checks. See [tests.log](tests.log).
The final ZIP was extracted into another clean directory and rebuilt with
ONNX support. Its runtime/model hashes exactly match the frozen candidate;
its allowlist contains source, models, and provenance, with no host executable.

Real-clock, colour-swapped comparisons against the archived arena-v10 engine
finished **2 wins, 0 draws, 2 losses** across two independent seed pairs at
180+2. White won every game; each candidate's pair score is 0.5. All four ended
by the normal king-capturable rule, with no protocol failure or warning and
more than 97 seconds left on each final clock. Diagnostic tails confirm hybrid
operation for both bots. See [the complete match report](real-clock/summary.json).
Four games are a release check, not a resolved playing-strength comparison;
even identical pair scores do not justify a zero-width confidence interval.

The final decision is to publish this as the conservative **arena-trial**
variant: the material-exposure diagnostic improves, immediate king-loss labels
do not regress in the queried histories, and the build/protocol checks pass.
Consistent wins against Duck and TA A/S remain an unachieved campaign goal.
