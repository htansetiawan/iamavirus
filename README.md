# iamavirus

A bot for the [MIT 6.7980 Fog of War Challenge](https://www.mit.edu/~6.7980/fow/)
(Topics in Multiagent Learning, Fall 2026).

Fog of War chess is a two-player zero-sum **extensive-form game with imperfect
information**, so this is built as one: alpha-beta search over an explicit belief
distribution, with the root move chosen by solving a matrix game rather than by
taking a best response to a single guess.

See **[ENGINE.md](ENGINE.md)** for the design and the reasoning behind it.

## Quick start

```bash
bash build.sh     # compiles ./bot with g++ (C++20, no dependencies)
bash test.sh      # runs every unit test
bash package.sh   # builds the submission archive
```

To play it locally, extract the course starter kit and point its referee at the
binary:

```bash
.venv/bin/python referee.py --trusted-local \
  --white /path/to/iamavirus/bot \
  --black '.venv/bin/python -u baseline.py --seed 1' \
  --base-time 180 --increment 2 --max-plies 1000 --output game.json
```

The differential test additionally needs the kit's `referee.py` and the Python
starter's `vision.py`, since it checks this engine against the arena's own rules:

```bash
FOW_PYTHON=/path/to/.venv/bin/python FOW_KIT=/path/to/kit bash test.sh
```

## Results

Measured locally. The baseline figure is against the downloadable `baseline.py`,
which ranks captures with random tie-breaking; it is **not** evidence of strength
against the arena's other opponents.


| | |
|---|---|
| vs. the course `baseline.py` at 180+2 | **10W–0L**, both colours |
| v4 vs v3 head to head, 48 paired games | 0.573 +/- 0.069 (~+51 Elo) |
| search speed | ~11M nodes/sec |
| depth | 11 at one second, 12 at four |
| rules conformance | **47,875 / 47,875** checks agree with `referee.py` |
| unit assertions | ~169,000 across 8 suites, 0 failures |

Verified with both Clang 17 (libc++) and GCC 16 (libstdc++).

## Layout

| path | role |
|---|---|
| `bitboard.*` | magic bitboards; O(1) slider attacks |
| `position.*` | board state, Fog of War move generation, incremental hashing |
| `observation.*` | exact legal moves from one observation; the visibility rule |
| `evaluation.*` | material, placement, activity, and the fog term |
| `transposition.*` | fixed open-addressed table, 16-byte entries |
| `search.*` | alpha-beta with the referee's terminal rule |
| `belief.*` | particle filter over the opponent's position |
| `regret.*` | regret matching for the root matrix game |
| `engine.*` | the decision procedure |
| `bot.cc` | the arena protocol |
| `tests/` | unit suites and the differential test against `referee.py` |
| `tools/` | conformance harness and benchmark |

`referee.py` and the starter kit are course material under GPL-2.0 and are
deliberately **not** vendored here; this repository is Apache-2.0 and depends on
them only to run the differential test.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
