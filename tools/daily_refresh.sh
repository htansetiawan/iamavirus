#!/usr/bin/env bash
# Daily arena refresh: pull new replays, rebuild the training data, update the
# taxonomy report, commit the report.
#
#   bash tools/daily_refresh.sh [--no-dataset] [--no-push]
#
# Storage: data/raw and data/manifests are symlinks to
# /media/henrytan/seagate/iamavirus-data (exFAT); the run is skipped when the
# drive is not mounted.
#
# Steps (each logged to data/logs/daily/<date>.log; a failed step does not stop
# the later ones):
#   1. ingest our games (newest 1,000) and all teams' games (newest 6,000;
#      the arena plays about 4,000 a day; already-held games are skipped)
#   2. training data, rebuilt from all of data/raw:
#        data/manifests/arena-latest.json (+ shards)  imitation/RL episodes
#        data/derived/moves/arena-latest-{train,test}.txt  mist-c opponent-model
#        moves (last 21 days; fit with fowsearch-c tools/fit_move_model.py)
#   3. data/reports/daily/<date>.{md,json} and latest.md (learning.daily_report)
#   4. commit the report (path-limited) and push with tools/push_safe.sh
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python
DATASET=1; PUSH=1
for a in "$@"; do
    case "$a" in --no-dataset) DATASET=0 ;; --no-push) PUSH=0 ;; esac
done
mkdir -p data/logs/daily data/derived/moves data/reports/daily
LOG="data/logs/daily/$(date -u +%F).log"
exec 9>data/logs/daily/.lock
flock -n 9 || { echo "daily refresh already running" >&2; exit 0; }
step() { echo "== $(date -u +%H:%M:%S) $*" >>"$LOG"; }
# data/raw and data/manifests live on the Seagate (symlinks); without it, skip
if [ -L data/raw ] && [ ! -d data/raw/games ]; then
    step "data/raw -> $(readlink data/raw) is not available (drive not mounted?); skipped"
    exit 1
fi
run() { "$@" >>"$LOG" 2>&1 || echo "   step failed (exit $?): $*" >>"$LOG"; }

step "ingest ours";      run nice -n 10 $PY -m learning.ingest --team IAmAVirus --output data/raw --limit 1000
step "ingest all teams"; run nice -n 10 $PY -m learning.ingest --all --output data/raw --limit 6000
step "games held: $(wc -l <data/raw/accepted.jsonl) accepted lines"

MIST_C="${MIST_C:-$HOME/git/fowsearch-c}"
if [ -f "$MIST_C/tools/export_moves.py" ]; then
    step "mist-c move export"
    run nice -n 10 python3 "$MIST_C/tools/export_moves.py" data/raw/games data/derived/moves/arena-latest \
        --games 1000000 --since "$(date -u -d '21 days ago' +%F)"
fi
if [ "$DATASET" = 1 ]; then
    step "dataset manifest"; run nice -n 10 $PY -m learning.dataset --raw data/raw --manifest data/manifests/arena-latest.json
fi

step "daily report";     run $PY -m learning.daily_report --raw data/raw --out data/reports/daily
REPORT="data/reports/daily/$(date -u +%F)"
if [ -f "$REPORT.md" ]; then
    git add -f "$REPORT.md" "$REPORT.json" data/reports/daily/latest.md >>"$LOG" 2>&1
    if ! git diff --cached --quiet -- "$REPORT.md" "$REPORT.json" data/reports/daily/latest.md; then
        git -c user.name=henrytan commit -q -m "Daily arena report $(date -u +%F)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- "$REPORT.md" "$REPORT.json" data/reports/daily/latest.md >>"$LOG" 2>&1
        [ "$PUSH" = 1 ] && run bash tools/push_safe.sh
    fi
fi
step "done"
