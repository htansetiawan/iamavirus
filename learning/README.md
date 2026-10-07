# Replay learning and reinforcement learning

Implementation of the Astra specification (replay learning, recurrent PPO,
ONNX deployment and a hybrid player) for the IAmAVirus Fog of War bot. This
file is the runbook; `../HANDOFF.md` records state and measurements.

## Environment

| component | version used here |
|---|---|
| Python (learning venv `.venv`) | 3.12 |
| PyTorch | 2.11.0+cu128 |
| NumPy / ONNX / ONNX Runtime (Python) | 2.5.3 / 1.23.2 / 1.30.0 |
| python-chess (referee tests only) | 1.11.2 |
| g++ | 13.3 locally; the course builds with 12.2 |
| ONNX Runtime C++ SDK | 1.24.2, the course's version, at `$ORT_HOME` locally and `/opt/onnxruntime` in the arena |
| GPU | one NVIDIA RTX PRO 5000 (48 GB); CPU inference in the arena |

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python torch --index-url https://download.pytorch.org/whl/cu128
uv pip install --python .venv/bin/python numpy onnx onnxruntime pyyaml pytest chess==1.11.2
# the course starter kit, kept OUTSIDE the repository (GPL-2.0 course material)
mkdir -p ~/git/fow-starter && cd ~/git/fow-starter && curl -sO https://www.mit.edu/~6.7980/fow/starter/starter.zip && unzip -q starter.zip
uv venv .venv --python 3.12 && uv pip install --python .venv/bin/python -r requirements.txt
# ONNX Runtime SDK for local neural/hybrid builds
mkdir -p ~/git/onnxruntime-sdk && cd ~/git/onnxruntime-sdk && curl -sLO https://github.com/microsoft/onnxruntime/releases/download/v1.24.2/onnxruntime-linux-x64-1.24.2.tgz && tar xzf onnxruntime-linux-x64-1.24.2.tgz
```

The rules used by every stage are the C++ engine's, exposed through
`rules_capi.cc` and built automatically into `build/librules.so` by
`learning/_native.py`. They are checked against `referee.py` by
`tests/conformance_test.py` (C++) and `learning/tests/test_rules_vs_referee.py`
(the Python binding and the termination rules).

## Tests

```bash
bash build.sh && bash test.sh                                   # C++ suites (search, engine, neural, ...)
FOW_PYTHON=~/git/fow-starter/.venv/bin/python FOW_KIT=~/git/fow-starter bash test.sh   # + differential test vs referee.py
.venv/bin/python -m pytest learning/tests -q                     # rules, codec, histories, feature parity, PPO accounting
```

Correctness gates and where they live:

| gate | test |
|---|---|
| replay reconstruction | `learning/ingest.validate_replay`; every accepted replay reproduces boards and both observations |
| frame/action alignment | `learning/tests/test_histories.py` |
| information isolation | `test_histories.py::test_information_isolation_features_ignore_truth` |
| action codec | `learning/tests/test_action_codec.py` |
| candidate parity | `test_histories.py::test_candidate_parity_over_random_games`, `tests/conformance_test.py` |
| recurrent event parity (Python vs C++) | `learning/tests/test_feature_parity.py` |
| terminal semantics | `learning/tests/test_rules_vs_referee.py` |
| PPO accounting / return accounting | `learning/tests/test_ppo_accounting.py` |
| export parity | `python -m learning.export --parity-shard ...` |
| runtime | `python -m learning.evaluate --suite runtime` |

## Pipeline

```bash
# M1: collect and validate public replays (paced at one request per second)
.venv/bin/python -m learning.ingest --from-corpus corpus/corpus-all.txt --output data/raw
.venv/bin/python -m learning.ingest --team IAmAVirus --output data/raw
.venv/bin/python -m learning.ingest --all --output data/raw --limit 2000
.venv/bin/python -m learning.dataset --raw data/raw --manifest data/manifests/v1.json

# M2: replay pretraining (stage A)
.venv/bin/python -m learning.pretrain --config learning/configs/replay_ppo.yaml \
    --manifest data/manifests/v1.json --output checkpoints/pretrain
#   resume:  --resume checkpoints/pretrain/latest.pt

# M3: export and parity, then package for the arena
.venv/bin/python -m learning.export --checkpoint checkpoints/pretrain/best.pt \
    --output releases/v1 --parity-shard data/manifests/v1/test.jsonl.gz
ORT_HOME=~/git/onnxruntime-sdk/onnxruntime-linux-x64-1.24.2 bash build.sh
bash package.sh /tmp/iamavirus.zip releases/v1      # bundles model/ into the ZIP

# M4: recurrent PPO (stage B)
.venv/bin/python -m learning.train_ppo --init checkpoints/pretrain/best.pt \
    --config learning/configs/replay_ppo.yaml --output checkpoints/ppo --iterations 10

# M5: evaluation
.venv/bin/python -m learning.evaluate --candidate checkpoints/pretrain/best.pt --suite tactical
.venv/bin/python -m learning.evaluate --candidate checkpoints/pretrain/best.pt --suite model --manifest data/manifests/v1.json
.venv/bin/python -m learning.evaluate --candidate checkpoints/ppo/latest.pt --suite match \
    --baseline checkpoints/pretrain/best.pt --opponents capture-greedy cpp:20000 --pairs 50
.venv/bin/python -m learning.evaluate --candidate releases/v1 --suite arena --mode hybrid --baseline-mode cpp --pairs 20
.venv/bin/python -m learning.evaluate --candidate releases/v1 --suite runtime
```

Artifacts:

| path | content |
|---|---|
| `data/raw/games/<id>/` | immutable replay, listing, fetch metadata, optional diagnostics |
| `data/raw/quarantine/<id>.json` | exact validation failure |
| `data/manifests/<v>.json`, `data/manifests/<v>/*.jsonl.gz` | dataset manifest and shards (gzip JSON lines of `PlayerEpisode`) |
| `checkpoints/<run>/{latest,best}.pt`, `train_log.jsonl`, `ppo_log.jsonl` | checkpoints with config, dataset hash, parent and metrics |
| `releases/<v>/{observe,score}.onnx`, `model_manifest.json` | the deployable graphs with hashes, versions and parity results |

## Running the bot

`run.sh` starts `./bot`. The mode is chosen by environment: `FOW_MODE=cpp`
(default), `neural` or `hybrid`, with `FOW_MODEL_DIR` pointing at a release
directory (default `model/`, which `package.sh` fills). If the graphs cannot be
loaded, or inference ever fails, the bot logs one line and plays `cpp` for the
rest of the game. Each decision logs a compact line that includes the seed
prefix, mode, the leading candidates as `uci:policy/danger/particle-risk`, the
chosen move's estimates, inference time and the whole-turn time.

## What the stages are and are not

- Stage A is supervised: policy cloning, hidden-square belief, one-move king
  danger, and the game result, all from each player's own history. It is an
  initialisation and a calibrated danger estimator, not a strength claim.
- Stage B uses fresh simulator games only; public replays never enter the PPO
  ratio. Training games are untimed (`training_mode = untimed-rules-only`);
  timed conformance is measured separately through the referee.
- The belief head is per-square marginals for auxiliary supervision and
  diagnostics; it is never sampled into boards or multiplied into the
  particle filter.
- Hybrid-selected moves are not samples from the neural policy and are never
  given its log-probability.
