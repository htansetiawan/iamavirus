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

## Fixed fit complete: negative, no continuation of this configuration

Host admission passed; original87395 exited0 in24.34s, all8epochs, epoch8
selected on validation.73,345parameters/293,380FP32bytes. Query student
LL0.47051/Brier0.14701 versus flat0.47254/0.14706, but calibratedSF
0.46767/0.14224 is better on both. Gate fails. No test opened, sweep,
native-cost work or deployment follows. The teacher itself only gains0.86%
LLon thisvalidationfold; our2%bar is demanding, but even a zero-gain bar
would reject this query model againstSF. Don't turn the raw-SF win into a
quality claim by omitting the calibrated control.

Independent CPU reviewer62668 exits0, all8746validation predictions and
game-aggregated metrics checked; maxCPU/GPUprobability difference7.73e-5,
metricshift<1e-6; gate unchanged. Checkpoint and evidence retained. GPU/4–5
reservation released. The broader latent-relational direction remains open;
the concrete root-mask candidate passed270 and proceeds to actual games.
