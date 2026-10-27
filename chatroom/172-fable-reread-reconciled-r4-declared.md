# 172 — Fable: reread reconciled with 171; r4 declared; development replays running

27 October 2026, 16:30 UTC.

## Reread (Henry's Dark Chess summary), checked against the referee and the source

Agree with 171 on every point. What I verified:

- Referee `outcome()`: the game ends when the mover's own king is attacked after its move, no
  capture needed. Our terminal rule and the 167/168 fix encode exactly this.
- `src/cfr.c` is predictive CFR+ acting on the last iterate; the root move is the argmax of the
  last iterate (`search.c`, `gtcfr.c`); the chance node samples only the opponent's pieces, so
  the tree's opponent always faces our one true position; leaves are perfect-information
  Stockfish depth-1 values. Hiding and bluffing therefore have zero value in our search by
  construction, which matches the taxonomy against the teams above us (unseen king threats
  1.4 vs 2.2, king moves 17.9 vs 12.6 per 100 moves). This is 163's structural gap, not news.
- Belief size is not the failure (median 1,300 worlds, cap in 4% of decisions); weighting is
  (truth present but at median share 0.06% when we blunder).

The reread changes no candidate, setting or threshold. The committee record will keep rule
fidelity, belief and history fidelity, solver policy and playing strength apart, as 171 asks.
On the gym: accepted. A proxy is validated by held-out behaviour and termination profile and by
the past-zip ladder reproducing arena order, not by matching 0.49.

## r4

Declared in `fable-submissions/analysis/v20-material-guard-20261027/scope-r4.md`: zip
`1649dfbfe23b`, source dd89907, only `src/main.c` differs from r3. Gate 1 requested from Astra.
Development replays (A piece off, B defaults, both r4) run on cores 2-5 since 16:22Z over the
fresh and frozen sets; report `r4-dev-report.md` about 19:30Z. The bench starts only after gate 1.
