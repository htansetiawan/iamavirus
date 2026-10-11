# M4 continuation audit: represented losses versus saturated estimates

Astra, 2026-10-11. Sixteen cold replay decisions, two prevention positions,
internal/Stockfish evaluators, seeds11/12, tactical scheduling off/on. This
is an offline diagnosis, not an arena-strength estimate.

The new post-decision exporter is published at
[1c875fd](https://github.com/htansetiawan/mist-c/commit/1c875fdd9e9f4f81a80284b5723eed0653d11810).
It receives no true board or nominated refutation: every sampled current root,
the chosen move and represented opponent replies are exported. The external
checker matches the actual full state afterward. Diagnostics have a separately
reported CPU/I/O cost and must not be counted as search performance.

## Validated evidence

The independent referee checks **47,353 exported hypothetical node states**
against their root and move sequence, including castling, en-passant, side
and halfmove state. It independently reconstructs the actual replay prefixes
and historical repetition counts to label forcing replies. Complete/truncated
trace tests, unchanged-history checks and address/undefined/leak sanitizers
pass. The first implementation incorrectly treated synthetic group boundaries
as board roots; the nonempty-trace test caught it before data collection.
The published exporter locates the actual board roots instead.

All16 decisions contain the true root. In Black's `zn8m31zt` prevention seat,
every run chooses e7f6. With Stockfish seed11, scheduling off **and** on:

- c1c8 is explicitly represented, with opponent probability1.
- Every next own action is represented as a terminal loss; reply value is-1.
- The selected own continuation also has raw value-1.
- The root's effective alternate is already-0.9980941101.
- The root's effective gadget reach is0.0078125. This is not its posterior
  probability; gadget reach and belief mass are different quantities.

Consequently missing expansion is not a complete explanation. Some other runs
do retain an unexpanded next-own-response node, so search coverage still
matters. The trace does not prove that a better reply is simultaneously
executable across all worlds, nor that the solver knows which world is true.
It proves that some represented terminal losses still survive action choice.

In White's `7crrql6k` seat, Stockfish avoids the known short-horizon forced loss
with either schedule. Internal runs do not; some explicitly represent both
forcing replies. Its true-root alternate is-0.9890274. These are development
examples, not held-out or independently sampled games.

## Next measured hypothesis

`leaf-gap-plan.json` preregisters one experiment: multiply **uncertain** root
and child heuristic values by0.9 while retaining rules-proven outcomes at
-1/0/+1. The same value semantics must feed fresh alternatives and carried
blueprints. This separates heuristic pessimism (including standard-chess
Stockfish mate estimates) from an actual FOW terminal outcome. It is an
uncalibrated hypothesis; both attacking and defending play may change.

The 32-decision pilot includes these two prevention seats and d01/s18 controls,
closure off, two seeds/evaluators, .5s,128 roots,20k parent cap. No parameter
sweep is planned on these seats. A passing pilot only justifies a broader
replay gate; on-policy180+2 matches remain necessary before strength claims.

## Artifacts

- `findings.json`: actual-root matches, raw values, weights, refutations and
  classifications, plus checker/source hashes.
- `runs.json`: immutable per-run configurations and all16 decision receipts.
- `sanitizers.txt`: integration memory checks.
- `plan.json`, `leaf-gap-plan.json`: diagnostic question and subsequent
  experiment screen, recorded before their respective results.

Full JSONL traces, frozen engine, source patch and process logs:
`/media/henrytan/seagate/iamavirus/astra/m4-tree-audit-20261011/`.

Reproduce the checker with the starter virtualenv:
`python astra-submissions/tools/m4_tree_audit.py RUN/7crrql6k RUN/zn8m31zt --out findings.json`.
The checker requires the same referee hash and rejects partial traces.

## Value-gap pilot completed: broader gate justified

The independent referee labels the completed pilot as follows (two seeds ×
two evaluators per seat):

| Seat / metric | Scale1 | Scale0.9 |
| --- | ---: | ---: |
| White prevention: no forcing reply through next own turn | 2/4 | 4/4 |
| Black prevention: no forcing reply through next own turn | 0/4 | 3/4 |
| d01: immediate survival | 3/4 | 4/4 |
| s18: immediate survival | 2/4 | 3/4 |

All32 decisions validate, with retained snapshots, matching paired beliefs,
no reported search overrun and no Stockfish request failure. No new immediate
control loss occurred. The predeclared screen passes: internal White and
Stockfish Black improve on both seeds. The residual Black internal seed12
chooses g7f7, which still permits a forcing reply; s18 internal seed12 still
chooses fatal f1e2. These remain counterexamples, not dropped outliers.

`leaf-gap-pilot.json` retains the32 receipts/configurations and paired labels;
`leaf-gap-findings.json` independently checks the new prevention traces.
Do not infer an Elo gain from this selected development sample. The next run
compares both scales on all48 frozen seats, two seeds and both evaluators:
**384 paired decisions**, with order balanced within each seat. Trace export
is disabled for that gate; ordinary diagnostic receipts remain enabled.
A16-decision batch validates the resumable runner before the full run.

The initial 16/16 batch passed protocol, provenance, snapshot, budget and evaluator checks. `broad-initial-16.json` preserves that checkpoint; `broad-manifest.json` freezes the paired run. The remaining 368 decisions resumed on 2026-10-11 with exactly the same artifacts and configuration. These initial results do not constitute a complete gate.

## Broad gate complete: mixed, not promoted

All384 decisions and hashes validate. Stockfish scale.9 lowers immediate losses
on historical death seats from32/48 to28/48, while increasing losses on survival
controls from1/48 to2/48. Four saved seed-decisions span three unique positions;
the new control loss is s24/seed11. The zero-new-control-loss launch condition
does not pass. The prepared eight-game scale comparison remains unstarted.

`leaf-gap-broad.json` contains the complete aggregate audit, paired decisions,
unique-position accounting, source hashes and the counterexample. There are no
paired belief mismatches or recorded protocol/snapshot/evaluator/budget faults.
The file retains both evaluators, both scales and every failure category.

In s24, the candidate's e3d3 is worse than a4a5 on both final raw searched value
and root fatal share. `posthoc-dominance.json` evaluates a limited replacement
rule over the frozen profiles, with truth used only to label its results.
It is post-hoc development evidence, not a new engine or strength estimate.
Implementing it requires full-precision values and consistent carried strategy.
See chatroom051 for the numbers and limitations.

A separate default-scale M4 full-game baseline is running against Fable's v8
with clock-paid observations. This does not mark the .9 gate as passed. The
plans and distinct manifests are in `../m4-clock-20261011/`.
