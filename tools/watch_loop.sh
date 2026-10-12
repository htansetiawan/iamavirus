#!/usr/bin/env bash
# Arena watch loop: every INTERVAL minutes ingest our newest games, rewrite the
# version watch report and the top-six report, commit only those two files and
# push. Measurement only. Usage: tools/watch_loop.sh <arena version> [minutes]
# Run with nohup/setsid so it outlives the session that started it.
set -u
cd "$(dirname "$0")/.."
VERSION=${1:?arena version}
INTERVAL=${2:-20}
PY=.venv/bin/python
OUT=data/reports/v${VERSION}-watch.md
TOP=data/reports/top6-report.md
LOG=data/logs/watch-v${VERSION}.log
mkdir -p data/logs
while true; do
  {
    echo "== $(date -u +%FT%TZ)"
    nice -n 10 $PY -m learning.ingest --team IAmAVirus --output data/raw --limit 200
    $PY -m learning.arena_watch "$VERSION" --output "$OUT"
    $PY -m learning.top6_report --output "$TOP"
    rec=$(grep -m1 '^\*\*Record' "$OUT")
    git add -f "$OUT" "$TOP"
    git commit -q -m "v${VERSION} watch and top-six report: $(date -u +%H:%M) ${rec}

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -- "$OUT" "$TOP" && tools/push_safe.sh
  } >>"$LOG" 2>&1
  sleep $((INTERVAL * 60))
done
