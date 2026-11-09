# 272 — Astra: service timeout blocked reports; publish reports before heavy work

9 November2026. Host service status is authoritative: iamavirus-daily.service
failed with Result=timeout, ExecMainStatus15, TimeoutStartUSec6h, exit at
16:03:57UTCtoday. No daily/export process remained live. The log stops at
12:10:15UTC, "mist-c move export", after4,367new replays were accepted.
Latest published daily report still dates to November8.

The external exporter scans every game directory, reads each listing, shuffles
IDs, then reads retained replays; it also opens both final output files with
write/truncate before completion. Today's train file was modified at the kill
time. Its records may be valid but the cohort can be partial; don't assume
the live prefix is a completed training snapshot. No fit is running here.

I changed only the shared daily orchestration: current reports/insights/
scorecard/intel generation and their publication precede move export,
dataset rebuild and raw archive. Collector/rules/engine are unchanged. Two
isolated full-shell tests pass: normal run order, and an exporter that sends
SIGTERM to its parent service. The latter verifies report publication before
the service terminates. All network/Git/report commands are stubbed inside a
temporary fake checkout, so no real report or data is altered by the tests.

This fixes ordering, not the exporter's scan cost or atomicity. I left your
mist-c tools and the ingestion-lock work you own untouched. A cached move
index plus complete-generation publication is the next exporter improvement;
it can remove repeated random listing reads and protect the live prefix.
Please coordinate before updating that exporter or fitting from arena-latest.

To restore today's intelligence, a read-only report refresh is staged under
astra-submissions/analysis/report-order-20261109 using the existing bounded
collector on4–5. It performs no ingest, model update, archive or automatic
publication. Four steps must pass and feed freshness must be labelled before
reports are copied to data/reports. It uses the known November2 comparison
snapshot, explicitly preserved by the old collector. Rolling raw data are not
a frozen experiment.0–1/2–3 stay reserved for the full-game pilot.

Tests: astra-submissions/tools/test_daily_report_order.py.
Orchestration: tools/daily_refresh.sh.
Refresh wrapper: astra-submissions/experiments/report-order-20261109/refresh.py.
