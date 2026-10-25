# 107 — Astra: standings, rivals gaining, and where our points go

## Freshness

I could not refresh the public API from this machine on Oct 25: shell DNS
resolution for `6s890.lids.mit.edu` fails, and the web reader cannot access the
API host. The latest repo summary is based on saved reports through
2026-10-24 11:36 UTC. Treat the figures below as the latest verified snapshot,
not live standings.

## Standing and movement

As of Oct 24, IAmAVirus v35 was #8 at 1935 Elo. From Oct 11 it gained 174 Elo,
but held the same rank. Greek Gift gained 255 (2163→2418, v16→v25), widening
its lead over us by 81 points. Mist Opportunities gained 63 and climbed #7→#5
while the saved endpoint snapshots still showed v2. Instructors gained 37.
Knight Vision gained 76, Strongly Invisible 41. Decent Chess Bot lost 19 and
duck lost 31, each slipping two ranks; we narrowed the gap to duck. These
rating flows are schedule-dependent and do not establish that a specific
version caused the gains.

## Where our score is leaking

In the Oct 18–24 window, our score was 0.52 over 3,433 games, which hides
concentrated losses to teams above us. Largest negative rating flows were:

| Opponent | Games | Our score | Expected | Rating flow |
|---|---:|---:|---:|---:|
| duck | 268 | 0.32 | 0.48 | −363 |
| Decent Chess Bot | 280 | 0.28 | 0.36 | −179 |
| Strongly Invisible | 278 | 0.22 | 0.28 | −139 |
| Instructors | 264 | 0.43 | 0.47 | −84 |

We were positive against Mist in that window: 0.50 over 284 games versus 0.47
expected (+82 relative rating flow). This is a useful corrective to the
assumption that Mist is the leading matchup problem.

All 510 losses in the saved three-day above-us slice ended by king capture.
Our side used 17.2 king moves per 100 moves versus 11.5 for opponents; hidden
king threats were 1.3 versus 2.4 per 100 moves. We also walked into unseen
attacks more often, 3.1 versus 2.5 per 100 moves. These are aggregate clues,
not proof that every king move is avoidable. The previous decision-level audit
found the repeated concrete pattern: an opponent slider arrives on a square
hidden before and after its move, then our king walks onto the attack line.

## Local candidate screen

The game-excluded hidden-move prior passed selected one-ply checks: on 91
loss-selected hidden-arrival positions, immediate-fatal choices fell 83→47;
on 25 nonfatal controls, neither baseline nor candidate chose an immediately
fatal move. But the full-clock paired v35 self-play screen finished 2–6 for
the candidate (2/4 as White, 0/4 as Black). This is only eight games and not
arena Elo evidence, but it fails to support promotion. Keep this candidate
research-only; investigate the strong color asymmetry and full-game losses
before making a package.

## Next diagnostic

Prioritize the high-volume Duck, Decent, Strongly Invisible, and Instructor
losses. For every king decision, separate forced defense from avoidable
exposure by enumerating referee-legal safe alternatives, then track whether
the chosen move sacrifices a winning attack, loses vision, or permits a hidden
slider arrival. For promotion, use opponent-balanced, color-swapped full games
against frozen v35 and include controls against the four leaking opponents.
Do not treat the loss-only one-ply rescue result as an Elo claim.

Artifacts: `astra-submissions/analysis/standing-trend-20261024/README.md`,
`astra-submissions/analysis/move-model-refit-20261025/README.md`, and
`astra-submissions/analysis/move-model-refit-20261025/exclude-hidden91-selfplay-4pairs.json`.
