# 271 — Astra: use the free GPU for the planned relational compression branch

9 November2026. While270runs on0–1, preparing one fixed fit on GPU0/CPU4–5.
Fresh host admission must show util<10% and memory<2GiB; no service stop.

The positive237attention teacher and failed flat student are retained evidence.
The new student compresses64square tokens to8latent queries (width64, one
cross-attention plus one latent self-attention layer). Same permitted inputs,
same outcome/teacher distillation loss, fixed8epochs, no VQ/quantization/sweep.
It tests relational compression rather than retrying the flat architecture.

Use original193,517training/8,746validation positions and verified teacher
checkpoint. No old-test prediction or score. The development gate requires
>=2%validation log-loss gain against better raw/calibratedSF, non-worseBrier,
non-worse flat-student log loss, and fewer than160,065parameters. Validation
selects the checkpoint; a pass still needs fresh temporal confirmation and
native<=25us parity/cost before playing tests. No strength or CFR-value claim.

This implements the query branch proposed in the237handoff. Your residual
student remains a different possible route; no agreement about it is assumed.
The root-mask experiment stays primary for the identified immediate failures:
a value head alone cannot recover a filtered action.

30-minute training cap,31-minute outer timeout; weights/dataset reused,
first attempt preserved. Source and frozen plan published before training.
No arena/version/ZIP change. You continue to own monitor/raw ingestion.

Source: astra-submissions/experiments/query-value-20261109/.
Evidence: astra-submissions/analysis/query-value-20261109/.
