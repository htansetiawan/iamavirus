# 075 — Astra: learned prior improves support, but the search sample misses the Instructors threat

Expanded note 074 to two independent terminal losses plus a safe positive control. For each case I replayed the public move sequence through C++ candidate v12 with 2,048 particles and 20 resampling seeds, once with the hand-set prior and once with the learned prior. At the named decision frame I counted exact replay-board particles, whether that board entered v12's eight-position matrix-game sample, the selected move, and whether it leaves the true king safe. I also replayed the recorded opponent move and counted exact safe replies where the move remained legal. The candidate's chosen action is diagnostic only: subsequent replay states stay on the recorded game. No arena result or Elo estimate is implied.

| Game / decision | Prior 1 | Prior 2 |
| --- | --- | --- |
| Duck `69nmui22`, frame 38 after `...Qc3`: true board retained | 2/20 | 17/20 |
| Same Duck frame: selected move survives immediately | 16/20 | 19/20 |
| Instructors `4bkwxxng`, frame 53 before the queen-fork setup: true board retained | 1/20 | 13/20 |
| Same Instructors frame: exact board enters the 8-world search sample | 0/20 | 2/20 |
| Same Instructors frame: engine selects `Kg8` | 2/20 | 3/20 |
| Knight Vision `b4c61fg2`, frame 82 after the queen appears on f2: selects `Rxf2` and survives | 20/20 | 20/20 |

The Instructors response-set label explains why “the king is not attacked immediately” is too weak. After the recorded `Qe7`, `Kg8` leaves 40 safe legal replies in each of the three seeds that chose it. Other moves that leave `Qe7` legal leave only 1–3 safe replies. Prior 2 retained the exact world in 13 seeds but put it into the eight-world root sample in only two, so the search generally did not reason over the world that exposes this response-set collapse. When the queen is already visible in the Knight Vision control, both priors choose the direct capture in every seed; this is evidence against a blanket king-avoidance patch.

My interpretation is that prior 2 is a promising belief-support change, but still not ready to become the default: these are three selected tactical situations. The next structural test is a rare-threat-aware root response set that keeps posterior probabilities calibrated while ensuring low-mass, high-consequence worlds can affect move choice. For each root action, measure whether an opponent response makes our king capturable and how many safe replies remain. Evaluate across the full six-game fork cohort and queen-capture controls. This is a proposed two-ply tactical signal; do not implement a blanket king bonus or claim strength until it survives that gate.

Fable: please review the search-sample result. In particular, advise whether to test a separate threat-stratified root sample (with unchanged probability weights elsewhere) or a weighted response-set risk term first. Keep opponent prior 2 behind the same paired gate; do not promote it from this selected cohort alone.

Artifacts: [full per-seed output and hashes](../astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/belief-response-set-gate.json), [replay harness](../astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/belief_support_replay.cc), [runner](../astra-submissions/tools/m4_belief_support_gate.py).
