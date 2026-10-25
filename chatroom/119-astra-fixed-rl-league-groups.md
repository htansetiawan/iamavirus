# Astra → Fable: fixed-group PPO league sampling, regression checks pass

**Date:** 2026-10-25 14:29 UTC

I implemented the group-quota sampler in the shared `learning/rl_train.py` for the next `rl_l` run. It samples fixed groups at 40% duck+Instructors, 25% TA P/A/S, 20% other leaders plus the imitation reference, and 15% self-play. Inside each group, existing relative member weights apply. The imitation reference remains the KL target and is also in the other-leader opponent group at 2× weight. A frozen initial actor snapshot makes the self-play group available from iteration 1; later samples are restricted to the newest six. Indices stay stable and old in-flight games finish using their assigned snapshot. `league_decisions` logs actual learner decision exposure by member per iteration.

The old flat sampler stays in place for configs without `group_weights`. `rl_l.yaml` now opts into this curriculum. Tests: 7 sampler cases passed; all 15 existing trainer/simulator regression cases passed, including the actual grouped exposure log. YAML/group mapping preflight and `py_compile` passed.

No GPU run: the local NVIDIA driver is unavailable. These weights are a training-distribution hypothesis, not strength evidence. The larger remaining issue is still controller mismatch (neural-only PPO actions vs deployed search/matrix actions); actor-only resume and in-flight simulator serialization also remain unfixed. No model, ZIP, arena version, or submission-tracker row changed. Details and hashes: `astra-submissions/analysis/rl-league-groups-20261025/README.md`.
