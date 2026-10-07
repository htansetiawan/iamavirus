# Representation experiments

This package is independent of the deployed engine. It reuses the unchanged
feature boundary and task heads to measure architecture, pretraining and
precision choices separately. None of these commands uploads an arena bot.

Run from the repository root with `PYTHONPATH=astra-submissions:.` and the
repository's `.venv/bin/python`. Pin CPU work to cores agreed in
`chatroom/cores.json`; CUDA additionally requires the coordinated Astra lease.

```sh
PYTHONPATH=astra-submissions:. taskset -c 2,3 .venv/bin/python -m unittest \
  learning_experiments.test_models learning_experiments.test_ssl \
  learning_experiments.test_evaluate -v

PYTHONPATH=astra-submissions:. taskset -c 2,3 .venv/bin/python \
  -m learning_experiments.profile_models --output build/astra-model-profile

PYTHONPATH=astra-submissions:. taskset -c 2,3 .venv/bin/python \
  -m learning_experiments.run --manifest data/manifests/v3.json \
  --variant attention --phase supervised --device cuda --steps 1000 \
  --output /media/henrytan/seagate/iamavirus/astra/representations/attention-pilot
```

`--variant cnn` is the unchanged CNN control. `compressed_attention` inserts a
512-value intermediate bottleneck with no spatial bypass. All three models
export the existing observation/scoring tensor interface. Graph compatibility
does not by itself prove that a packaged C++ submission is correct.

`--phase ssl` uses the actor-only EMA teacher/student and masked-observation
objectives. A subsequent `--phase supervised --initialize SSL_CHECKPOINT` starts
a separate fine-tuning experiment. It is not a continuation of the SSL optimizer.
The source hashes and initialization checkpoint hash are recorded.

The runner freezes native C++ feature-rule sources into each output directory;
it does not rebuild Fable's shared `build/librules.so`. It hashes both used
shards, never reads the test shard, keeps full prefixes at training cuts, and
evaluates complete validation histories exactly once per decision. Output
contains `run.json`, `status.json`, append-only training metrics, checkpoints,
and validation reports with per-game sums for paired analysis. `--resume`
requires the original source/data/configuration identity. Use a new output
directory for changed experiments. Check process state as well as `status.json`
after an external interruption; a killed process cannot update its status.

```sh
PYTHONPATH=astra-submissions:. .venv/bin/python -m learning_experiments.compare_pilots \
  --control /path/to/cnn-pilot --candidate /path/to/attention-pilot \
  --step 1000 --output /path/to/comparison.json

PYTHONPATH=astra-submissions:. taskset -c 4,5 .venv/bin/python \
  -m learning_experiments.quantize_audit --graphs releases/v3 \
  --shard data/manifests/v3/validation.jsonl.gz --games 16 \
  --output build/astra-int8-audit
```

Add `--keep-recurrent-fp32` for the selective-precision arm. The audit asserts
the GRU matrices actually remain float; ONNX Runtime's Gemm renaming otherwise
makes a naive node exclusion silently ineffective. Each arm feeds back its own
recurrent state. Immediate-fatality labels in this audit describe policy-only
proposals, not the hybrid engine's final move.

Designs:

- [Attention and useful compression](../specs/attention-representation-experiment.md)
- [Self-supervised history learning](../specs/self-supervised-history-learning.md)
- [Larger teachers and inference precision](../specs/teacher-student-precision.md)

Evidence lives in `../analysis/representation-pilots/`. Large weights, ONNX
files, and full GPU-run logs remain in ignored build directories or on Seagate.
