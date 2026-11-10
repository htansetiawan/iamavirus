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
