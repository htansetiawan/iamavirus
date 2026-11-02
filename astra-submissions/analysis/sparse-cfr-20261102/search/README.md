# Equal-clock search: selective CFR

Declared gate: **FAIL**. Median node ratio 1.021x at the same 2.5-second search budget.

| Metric | Original v37 | Exact solver optimization |
|---|---:|---:|
| Immediate king loss | 12 | 12 |
| Two-point material loss in limited exchange probe | 5 | 5 |
| Four-point queen loss in probe | 0 | 0 |

| Opponent cohort | Decisions | Median nodes ratio | Fatal baseline / candidate |
|---|---:|---:|---:|
| HYPOTHERMIA | 17 | 1.023x | 4 / 4 |
| Instructors | 17 | 1.014x | 4 / 4 |
| duck | 17 | 1.049x | 4 / 4 |

All 51 protocol histories independently reconstructed from own observations, own moves and clocks. World samples, root actions and guard exclusions match between arms. Course-referee review agrees with every tactical label.

The cases are the same development supplement used by earlier experiments, not fresh held-out games. No posterior, guard, expansion rule, root selector or leaf model changes. Different search trees and moves can arise from timing, extra work and asynchronous Stockfish responses. Shared Stockfish state introduces order effects; first arm alternates by case. This result is not an Elo estimate.

Median node ratios by first arm: {"0": 1.0787607785183722, "1": 0.9555768520459604} (0 = baseline first; 1 = candidate first).

Full games are conditional on the frozen diagnostic gate; this report does not authorize promotion.
