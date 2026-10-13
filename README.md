# iamavirus

A bot for the [MIT 6.7980 Fog of War Challenge](https://www.mit.edu/~6.7980/fow/)
(Topics in Multiagent Learning, Fall 2026).

**Documentation:** the methods, architecture and algorithms over time are written up
at **[htansetiawan.github.io/iamavirus/docs/](https://htansetiawan.github.io/iamavirus/docs/)**
(sources in [docs/](docs/)); the interactive system notebook of the neural-era bot is at
[htansetiawan.github.io/iamavirus/](https://htansetiawan.github.io/iamavirus/). The version-by-version
record with outcomes is [MUTATIONS.md](MUTATIONS.md); the submission log is
[fable-submissions/README.md](fable-submissions/README.md).

The engine playing in the arena since version 33 is **[mist-c](https://github.com/htansetiawan/mist-c)**,
a clean-room C implementation of Obscuro-style imperfect-information search with Stockfish
leaf evaluation. The description below is of the earlier C++ engine in this repository,
which remains the rules reference and the local harness.

Fog of War chess is a two-player zero-sum **extensive-form game with imperfect
information**, so this is built as one: alpha-beta search over an explicit belief
distribution, with the root move chosen by solving a matrix game rather than by
taking a best response to a single guess.

See **[ENGINE.md](ENGINE.md)** for the design, **[versions/](versions/)** for what
each version changed and what the measurements actually said, and
**[harness/](harness/)** for how anything here is evaluated.

Negative results are recorded deliberately. Most of what was tried did not work,
and at Elo 1468 against leaders near 2100 the honest state is that the C++
rewrite and the rules conformance are proven while the strategic heuristics are
not.

## Quick start

```bash
bash build.sh     # compiles ./bot with g++ (C++20); picks up ONNX Runtime from /opt/onnxruntime or $ORT_HOME
bash test.sh      # runs every unit test
bash package.sh   # builds the submission archive; `bash package.sh out.zip releases/v1` bundles a model
```

The bot plays in one of three modes, chosen by `FOW_MODE` (`cpp`, the default;
`neural`; `hybrid`) with a release directory in `FOW_MODEL_DIR`. The learning
pipeline that produces releases lives in [learning/](learning/README.md).

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
| `bot.cc` | the arena protocol; feeds the neural adapter and selects the mode |
| `neural_observation.*` | observation-history features, in parity with `learning/features.py` |
| `neural_inference.*` | ONNX Runtime adapter for the two exported graphs |
| `rules_capi.cc` | C interface over the rules and the engine for `learning/rules.py` |
| `learning/` | replay collection, datasets, the recurrent model, pretraining, PPO, export, evaluation |
| `tests/` | unit suites and the differential test against `referee.py` |
| `tools/` | conformance harness, feature-parity harness and benchmark |

`referee.py` and the starter kit are course material under GPL-2.0 and are
deliberately **not** vendored here; this repository is Apache-2.0 and depends on
them only to run the differential test.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
