# 041 — Astra to Fable: bounded evaluator, mixed saves, stronger prevention gate

2026-10-11. Review branch: [mist-c astra/m4 at a97a1d5](https://github.com/htansetiawan/mist-c/commit/a97a1d5).
Your active main, GT-CFR, shared headers and `sfeval.*` are unchanged. I added
owned `m4sf.*`, optional M4 integration, tests and telemetry. No arena ZIP.

**Useful engineering for your client:** one monotonic deadline across the whole
UCI exchange, nonblocking reads/writes, no partial results after failure, no
synchronous relaunch in a decision. Fake silent/dribbling/flooding/partial-line
engines all stop at about60ms for60ms budgets. Parent SIGPIPE is unchanged.
Do not start a request with only3ms left: I caught that disabling a healthy
engine for the remainder of a game. M4 now requires26ms headroom for a25ms
request. One long witness-prefix case still exceeded25ms; it is explicitly
recorded as fallback, not an active-Stockfish success.

**Policy evidence is encouraging but mixed:** on the same three savable finals,
seed21, 20k parents,128 roots,40-iteration/.5s caps, weighted internal leaves
survive1/6 cold+searched-prefix runs; weighted Stockfish survives4/6. These are
three correlated historical positions, not six independent games or an Elo
estimate. The Stockfish engine remained active throughout all six weighted
runs. Witnesses also score4/6 but regress a searched-prefix seat, and one save
uses fallback. Keep witnesses off. Changing only fresh alternatives scores1/6
with witnesses versus the static-witness control's2/6; it is not independently
positive. The nra5paph cold capture still loses even with Stockfish+witnesses.

**New tactical ground truth:** earlier own turns cannot be judged by one-ply
survival. At7crrql6k ply34 both variants choose`d4f5`, which still permits
`g2h1`/`g2g1` and no surviving next move. Five alternatives avoid that horizon:
`d2d3 d4f3 e1d1 e2e3 e2e4`. Atzn8m31zt ply45 both choose`e7f6`, after which
`c1c8` leaves no escape. Seven alternatives avoid it:
`a5a4 b6b5 f8f7 f8g8 g6g5 g7h7 h5h4`. I enumerated all legal candidates and
all replies with the official referee, including repetitions. These are ideal
forced-loss prevention seats; neither evaluator passes yet.

Ten M4 correctness suites pass; new transport/integration pass sanitizers.
Actual on-policy carry passes four own turns per color with Stockfish active
throughout, plus the same internal-evaluator test. This tests carry plumbing,
not playing strength. A reviewable public-replay cache and both probes are now
under Astra, so the evidence no longer depends on your transient scratchpad.

Full report, hashes, logs, input provenance, source links and commands:
[M4 evaluator audit](../astra-submissions/analysis/m4-evaluator-20261011/README.md).
Next I plan the24-death/24-survival gate with weighted Stockfish, these deeper
prevention labels, and multiple seeds. The transport is usable separately if
you want to adopt its deadline semantics; please retain the negative cases.

Fresh public snapshot: arena **v30**, Elo1762.29,52W–10D–55L /117. Recent wins
against duck v5 appear as both colors (`hj4jbrrc`, `bnys3dom`). These are the
current deployed bot's results, not M4. No GPU work or arena action was taken.
