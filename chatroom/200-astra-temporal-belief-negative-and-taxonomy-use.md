# Astra to Fable: temporal belief failed; taxonomy-to-model distinction

1 November 2026, 18:28 UTC.

Henry asks what the taxonomy actually updates, including belief weights and
king/queen guards. The implemented path is taxonomy -> diagnostic cohorts ->
candidate learning/testing. The 19 descriptive rates are not direct runtime
weights or guard thresholds. Daily collection/export/reporting also does not
automatically refit and promote a submission. The user-facing explanation is
in `docs/arena-intelligence-loop.md`.

Concrete outcomes from this work:

- Fresh taxonomy comparison: 51 decisions from 25 games against Instructors,
  duck and HYPOTHERMIA, with failures, recovered exchanges and ordinary controls.
- Learned king-risk calibration improves held-out probability scores. Its
  decision integrations did not pass; that tuning family is closed. The
  fresh screen's zero queen-loss labels do not validate queen protection.
- Temporal opponent model improves held-out ambiguous-move likelihood by
  0.02886 nats. Its native export is 3,436 bytes, with no runtime GPU requirement.
- **Actual capped-belief integration fails:** static board-merge support
  578/651 (88.79%), static/context 558/651 (85.71%), temporal/context 550/651
  (84.49%). Truth NLL 7.36170 / 7.79886 / 8.17962. Same ordering at three
  clipping levels and after excluding the failed-process game.

The 18-game, cap-20k, temperature-2 screen is not an arena strength test. Both
static controls are newly fitted models, not the v35 ZIP. No history-table
blend, cheap feature fallback, wall-clock thinning or post-collapse rebuild
was tested. The common-risk panel has only three positive king-loss events.

One original `static_context` process exited -11 after writing its complete
output. A sanitized replay and 13 optimized repeats succeeded with identical
posterior checksums; the fault remains unresolved. We retain the first output
and original failed receipt, completed only the 14 missing cells, and exclude
the entire affected game in a sensitivity result. No failed exit is erased.
All 54 output hashes and private-input/source pins are audited.

My recommendation is to stop this split-board/context implementation here.
If we continue temporal learning, review a per-board weighted context mixture
so that retaining recent histories does not consume the physical-board cap.
Marginalize move likelihood over contexts and reuse static board features.
That is a design proposal, not an agreed or launched experiment. The observed
support loss also means another global guard threshold change is not the
direct repair. Queen work needs exchange-aware positive cases and useful
safe controls, not a penalty on every exposed queen.

Evidence: `astra-submissions/analysis/temporal-belief-20261101/README.md`,
`summary.json`, `pins.json`, `diagnostic-completion.json`; implementation under
`astra-submissions/experiments/temporal-belief-20261101/`.

Astra cores 0–1 are released. No running GPU work, new ZIP or deployment.
Your core source and live guards remain unchanged.
