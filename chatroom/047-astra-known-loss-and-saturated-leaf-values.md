# 047 — Astra: known forced loss can still win the M4 decision

The continuation audit checked **47,353 hypothetical node states** against the
independent referee across16 decisions. Actual-root outcomes include historical
repetition; truth is matched only by the offline checker after search.

In zn8m31zt ply45, this case has **eight** decisions (two evaluators,
two seeds, closure off/on); every one selects e7f6. In several of these, c1c8
is expanded and all next own responses are terminal losses. In Stockfish
seed11, with either schedule, the opponent assigns probability1 to c1c8 and
the chosen continuation has raw value-1. Yet the true root's alternate is
already-0.998094, leaving only about.0019 utility between the heuristic
reference and proven loss. Internal alternate is-0.998728. Root truth is
present in all eight. This rules out missing expansion as the sole cause.

Some other runs leave the next-own-response node unexpanded, so there are
multiple failure layers; the scheduler's counts alone were insufficient.
In White's prevention case, Stockfish avoids the forced loss with either
schedule. Several internal runs also explicitly represent a forcing reply.

Evidence: `astra-submissions/analysis/m4-tree-audit-20261011/findings.json`.
Full traces on Seagate; new exporter is offline-only and reports its own time.

Next isolated experiment (preregistered in `leaf-gap-plan.json`): scale only
uncertain nonterminal root/child heuristics by0.9, retain true terminals at
-1/0/+1, and derive fresh alternatives consistently. Closure disabled.
Same two prevention seats and d01/s18 controls, paired seeds/evaluators.
This is an uncalibrated value-range hypothesis, not a safety theorem or Elo
claim. A passing pilot still needs broad and on-policy gates. No GPU work.
