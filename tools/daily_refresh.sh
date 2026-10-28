#!/usr/bin/env bash
# Daily arena refresh: pull new replays, rebuild the training data, update the
# taxonomy report, commit the report.
#
#   bash tools/daily_refresh.sh [--no-dataset] [--no-push]
#
# Storage: {storage}/iamavirus-data on the machine's bulk drive is the storage
# of record. The path is per machine: set STORE in the environment or write it,
# one line, to the untracked file data/store. data/derived and
# data/manifests/arena-latest{,.json} are symlinks to it (the small tracked
# manifests stay in the repo); the
# replays stay on the local SSD as the working copy (a random replay read is
# 0.1 ms there, about 50 ms on the USB disk) and are archived to it after every
# run (tools/mirror_raw.py: a base tarball plus one per day). Without the
# drive, the ingest and the report still run; the training data and the
# archive are skipped.
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
STORE="${STORE:-$(head -n1 data/store 2>/dev/null)}"
SEAGATE=0; [ -n "$STORE" ] && [ -d "$STORE/raw-archive" ] && SEAGATE=1
[ "$SEAGATE" = 1 ] || step "storage ${STORE:-unset (STORE or data/store)} not available (drive not mounted?): training data and mirror skipped"
run() { "$@" >>"$LOG" 2>&1 || echo "   step failed (exit $?): $*" >>"$LOG"; }

step "ingest ours";      run nice -n 10 $PY -m learning.ingest --team IAmAVirus --output data/raw --limit 1000
step "ingest all teams"; run nice -n 10 $PY -m learning.ingest --all --output data/raw --limit 6000
step "games held: $(wc -l <data/raw/accepted.jsonl) accepted lines"

MIST_C="${MIST_C:-$HOME/git/fowsearch-c}"
if [ "$SEAGATE" = 1 ] && [ -f "$MIST_C/tools/export_moves.py" ]; then
    step "mist-c move export"
    run nice -n 10 python3 "$MIST_C/tools/export_moves.py" data/raw/games data/derived/moves/arena-latest \
        --games 1000000 --since "$(date -u -d '21 days ago' +%F)"
fi
if [ "$SEAGATE" = 1 ] && [ "$DATASET" = 1 ]; then
    step "dataset manifest"; run nice -n 10 $PY -m learning.dataset --raw data/raw --manifest data/manifests/arena-latest.json
fi

if [ "$SEAGATE" = 1 ]; then
    step "mirror replays and reports to $STORE"
    run $PY tools/mirror_raw.py --raw data/raw --store "$STORE/raw-archive"
    run rsync -rt --no-perms --modify-window=1 data/reports/ "$STORE/reports/"
fi
step "daily report";     run $PY -m learning.daily_report --raw data/raw --out data/reports/daily
# the deeper analysis: opponent version changes, rating point flow, queen events,
# king walking, the fog-line hazard table and the short losses (learning.daily_insights)
step "daily insights";   run $PY -m learning.daily_insights --raw data/raw --out data/reports/daily
# the skill scorecard: every team on the same taxonomy metrics over the last three days, our rank
# per category with the reference teams beside us (learning.scorecard; docs/skill-rubric-20261028.md)
step "scorecard";        run nice -n 10 $PY -m learning.scorecard --raw data/raw --out data/reports/daily --days 3
REPORT="data/reports/daily/$(date -u +%F)"
INSIGHTS="data/reports/daily/insights-$(date -u +%F).md"
if [ -f "$REPORT.md" ]; then
    git add -f "$REPORT.md" "$REPORT.json" data/reports/daily/latest.md >>"$LOG" 2>&1
    [ -f "$INSIGHTS" ] && git add -f "$INSIGHTS" data/reports/daily/insights-latest.md >>"$LOG" 2>&1
    SCORE="data/reports/daily/scorecard-$(date -u +%F).md"
    [ -f "$SCORE" ] && git add -f "$SCORE" data/reports/daily/scorecard-latest.md >>"$LOG" 2>&1
    if ! git diff --cached --quiet -- "$REPORT.md" "$REPORT.json" data/reports/daily/latest.md "$INSIGHTS" data/reports/daily/insights-latest.md "$SCORE" data/reports/daily/scorecard-latest.md; then
        git -c user.name=henrytan commit -q -m "Daily arena report $(date -u +%F)" -- "$REPORT.md" "$REPORT.json" data/reports/daily/latest.md "$INSIGHTS" data/reports/daily/insights-latest.md "$SCORE" data/reports/daily/scorecard-latest.md >>"$LOG" 2>&1
        [ "$PUSH" = 1 ] && run bash tools/push_safe.sh
    fi
fi
step "done"
