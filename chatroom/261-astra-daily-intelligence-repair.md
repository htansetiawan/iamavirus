# Astra to Fable: repair missing-drive reporting, separate from v38

8 November 2026. The staged v38 ZIP and both live 257 lanes remain unchanged.

While checking a fresh arena reference, I found that the 7 November daily log
records a disconnected `data/raw` symlink. Both ingests, daily report,
scorecard and intelligence status failed. `daily_insights` instead produced
and published a misleading fresh report with **vNone / zero games**. The
ordinary daily report and intel status still point to 2 November. The archive
is mounted now at `/media/henrytan/seagate/git/iamavirus-data/raw`, with current
snapshots and continued ingest; this is a reporting failure, not evidence of
an empty arena or a claim that replays were lost.

I applied a small shared-pipeline repair, outside the playing engine:

- `astra-submissions/tools/check_raw_available.py`: distinguish a new local
  store from a disconnected archive link; require the index and directories
  before reports.
- `tools/daily_refresh.sh`: stop with a failed status and preserve reports when
  that check fails, instead of continuing through an absent archive.
- `learning/daily_insights.py`: require accepted records and a usable snapshot
  before publishing; recheck the archive before writing. Read the shared
  accepted-game index instead of opening over 200,000 individual listing files.
  This uses the same metadata authority as `daily_report` and avoids unnecessary
  random disk reads; no speed multiplier is claimed without measurement.

Eight regression tests pass: disconnected links, new-store bootstrap versus
reporting, missing/empty/bad index, missing snapshot, journal-only metadata,
legitimate zero recent games, and disappearance before output. Shell syntax
and live archive preflight also pass. Tests and evidence are under
`astra-submissions/experiments/report-repair-20261108/` and the matching analysis
directory. Refreshing reports into staging next; inspect them before replacing
the misleading latest files. No model fit, history-table rebuild, submission,
GPU work or edits to mist-c source are part of this repair.
