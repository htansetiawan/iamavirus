# 043 — Astra: completed M4 gate; the iteration ceiling matters

2026-10-11, 08:25 UTC. Your active source files and GPU service remain untouched.

The fixed 24-death/24-survival gate finished **192/192 valid decisions**. With
two seeds per seat, internal M4 saves 14/46 potentially savable death decisions,
Stockfish/child-alternate M4 saves 15/46. Paired contrast: six SF saves, five
SF regressions, nine both safe, 28 both lose (including two unsavable d17
decisions). Both retain 48/48 immediate survivals. They change 37/48 and 36/48
historical safe moves, respectively. This does **not** meet your promotion
gate, and the controls are historical v3/v4 moves, not a freshly replayed v6.

The 40-iteration limit bound every solve: internal used .00969 s on average,
Stockfish .09967 s. We cannot interpret that as a fair use of the .5 s clock.
I preserved the full result and started the preregistered time-budget pilot.
With cap 1,000,000, it runs 691–794 internal iterations or 212–340 SF iterations,
using .377–.383 s including snapshots. All eight pilot decisions are valid,
all snapshots retained, all SF evaluators remain ready, no reported overrun.

**d01 changes materially with more search:** all four short solves died;
both SF seeds and one internal seed now find the sole surviving move `b8a7`.
Internal seed12 still chooses fatal `d5e4`. All four s01 decisions survive.
That is one diagnostic case, not a strength claim. The same time-budget run
is now continuing for all 192 decisions on the reserved cores6–7, nice19,
with no overlapping Astra experiment.

The report now verifies engine stderr hashes and extracts actual iteration,
node and sample counts. Missing root telemetry is explicitly unavailable,
not interpreted as missing truth. It also records each chosen action's gap
to the best raw action and the best zero-risk action under the final profile.
Seven short internal losses already have a truly safe zero-risk alternative
with greater raw value; none of the short SF losses do. These are final-profile
diagnostics, not theoretical convergence bounds.

The post-hoc minimum-root-risk selector removes many immediate deaths, but
changes most safe actions and has no on-policy evidence. I have not shipped it
or adjusted a penalty to fit this selected gate. Next decisions should use
the budget-filling results, then searched prefixes and the prevention cases.

- [Results and frozen inputs](../astra-submissions/analysis/m4-gate-20261011/README.md)
- [Complete fixed-iteration result](../astra-submissions/analysis/m4-gate-20261011/cold-05-final.json)
- [Eight-decision time pilot](../astra-submissions/analysis/m4-gate-20261011/cold-time05-pilot.json)

Separately, the existing public cache contains two identical new v30 losses
to duck v5 (`9pl31sez`, `burzt1so`): `1.e4 d5 2.exd5 Qxd5 3.d4 Qa5
4.Be3??`, with the queen hidden on the a5–e1 diagonal. I am checking this as
an observation-history regression family, without opponent-name routing.
