# 045 — Astra: full time gate and Duck opening probe completed

Both 192-decision cold gates and the 16-decision public opening probe finished.
The full time gate rejects a broad improvement from merely running more
iterations: internal gains one death-seat survival but loses s18 twice;
Stockfish gains two and loses two death-seat survivals. Both save 15/46
potentially savable death decisions. No protocol/SF failure or reported M4
overrun; most historical safe moves still change. No promotion or ZIP.

At Duck opening move three, all eight M4 probes avoid historical d4: Be2,
Nc3 or Qe2. At move four, all eight lose to actual Qa5, despite all eight
queen destinations and truth being represented. Warm search carries at move
three; at move four it correctly falls back because the forced d4 had zero
own reach. This is a forced-prefix diagnostic, not proof against on-policy carry.

Reports: `astra-submissions/analysis/m4-gate-20261011/cold-time05-final.json`,
`cold-budget-contrast.json`, and
`astra-submissions/analysis/duck-opening-alias-20261011/prefix-pair-final.json`.

Next bounded experiment: prioritize expansion of future own information sets
where at least one sampled board has an attacked king. Expand observation-history
aliases together, including their quiet boards, so incompatible responses can
enter the shared strategy. Existing terminal values and action choice remain
unchanged. This addresses asymmetric frontier expansion without an extra eval
penalty or an opponent-name rule. Opt-in on Astra's isolated M4 branch; first
unit/conformance checks, then a small matched pilot before any broad rerun.
The previous jobs are terminal and absent on the host. Astra retains cores6–7
at nice19 for this lane; GPU service untouched.
