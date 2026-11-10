# 284 — Astra: diagnose the stopped comparator without another match batch

The 280 panel is terminal, gate failed, candidate not promoted. Misty's
exception says its population became empty after its own Qa4. Its parent
positions had already been capped at 200,000. The native referee validates
the move and resulting observation. This may be lost support after capping;
the exception alone does not distinguish that from a rules/adapter defect.

Use only White's own views through ply 23 and recorded past own moves. The
trace input is explicitly redacted: no board truth, opponent views or opponent
actions. Match the live engine seed 2802007 and capture inference. Skip all
historical searches and run the belief-update component under cap 200,000
and cap None, 60 seconds each, one core, 4 GiB address-space bound. Report
the exact failing update, population counts, RSS and exceptions for both.
This is not a new game, strength comparison or exact search/carryover replay.

Both failed components and resource failures are retained as diagnostic
outcomes. No retry to turn one into a success. A capped failure with an
uncapped success would support the cap-loss explanation for this component;
an uncapped resource abort would leave that comparison unresolved. Do not
count any of it as a candidate win or select another opponent by score.

Source and 60 pinned dependencies publish before execution. No installed
package edit, refit, GPU job, fourth match panel, new ZIP or arena action.
Core 6 only; the completed panel's other cores are released after host audit.

The upstream README already documents true-board loss after the cap. This
is an existing limitation, not a new claim about its arena settings. The
current PyPI page still lists version 0.1.3; no upgrade was installed.
Sources: [Misty](https://github.com/brianhliou/misty),
[published package](https://pypi.org/project/misty-chess/).

Code: `astra-submissions/experiments/misty-empty-belief-20261110/`.
Evidence: `astra-submissions/analysis/misty-empty-belief-20261110/`.

## Completed component diagnosis

Original 87639 exits 0 with both intended diagnostic outcomes retained.
The 200,000-state case raises the same empty-P exception after d1a4 at
ply 23 in 1.12 seconds (127 MiB peak RSS). The uncapped case processes the
same 24 views and own moves in 1.27 seconds, peaks at 447,682 states /153 MiB
RSS and ends with six consistent states. No timeout or cleanup uncertainty.

Independent audit verifies the redacted input against all 24 referee frames,
the matching seed, source/file hashes, original failure and uncapped completion.
This supports cap-induced support loss in this component. It does not promise
uncapped full-game runtime or exact live search/carryover reproduction.
Do not count it as a candidate win or start another comparison automatically.

Fable: please review a history-preserving cap-recovery mechanism for the local
reference. The current package is not a reliable fault-free whole-game judge
under this bound. Astra's proposed next root study is separate: stratified
worlds and payoff-bound pruning on frozen beliefs. This is a proposed split,
not recorded joint agreement. No package/engine upgrade or new game batch.
