# RL trainer repair validation

See [the Fable handoff](../../../chatroom/022-astra-rl-trainer-repair-20261009.md).

- `validation.json`: exact source and checkpoint hashes, smoke configuration,
  two actual large-model CPU update logs, model widths and test result.
- `gae-audit.json`: six corrected target cases and source identity.

Run the focused tests:

```sh
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python -m pytest -q astra-submissions/tools/test_rl_trainer.py learning/tests/test_ppo_accounting.py
```

These are correctness checks. The two-iteration smoke checkpoints are temporary
and are not submission candidates or playing-strength evidence.
