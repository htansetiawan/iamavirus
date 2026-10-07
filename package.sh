#!/bin/bash
# Builds the submission archive.
#
#   bash package.sh [out.zip] [release-dir] [mode]
#
# The compiled binary is deliberately excluded: the course builds for Linux
# amd64 and the documentation warns against uploading a host executable.
# An optional release directory (observe.onnx, score.onnx, model_manifest.json)
# is packaged as model/, and `mode` (cpp, neural or hybrid; default cpp) is
# written into the packaged run.sh as the default FOW_MODE.
set -euo pipefail
cd "$(dirname "$0")"

OUT="$(realpath -m "${1:-/tmp/iamavirus-cpp.zip}")"
MODEL="${2:-}"
MODE="${3:-cpp}"
case "$MODE" in cpp|neural|hybrid) ;; *) echo "unknown mode $MODE" >&2; exit 1;; esac
if [ "$MODE" != "cpp" ] && [ -z "$MODEL" ]; then
  echo "mode $MODE needs a release directory" >&2
  exit 1
fi

STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
cp run.sh build.sh test.sh README.md \
  bot.cc engine.cc belief.cc search.cc evaluation.cc observation.cc \
  transposition.cc regret.cc position.cc move.cc bitboard.cc \
  neural_observation.cc neural_inference.cc opponent_model.cc \
  bitboard.h move.h position.h observation.h evaluation.h transposition.h \
  search.h belief.h regret.h engine.h piece_square.h \
  neural_observation.h neural_inference.h opponent_model.h opponent_weights.h "$STAGE/"
mkdir -p "$STAGE/tests" "$STAGE/tools"
cp tests/*.cc tests/*.h tests/*.py "$STAGE/tests/"
cp tools/*.cc "$STAGE/tools/"
if [ -n "$MODEL" ]; then
  mkdir -p "$STAGE/model"
  cp "$MODEL"/observe.onnx "$MODEL"/score.onnx "$MODEL"/model_manifest.json "$STAGE/model/"
fi
sed -i "s/FOW_MODE:-cpp/FOW_MODE:-$MODE/" "$STAGE/run.sh"
grep -q "FOW_MODE:-$MODE" "$STAGE/run.sh"

rm -f "$OUT"
(cd "$STAGE" && zip -q -r "$OUT" . -x '*.DS_Store' -x '*__pycache__*')
echo "wrote $OUT (mode=$MODE${MODEL:+, model=$MODEL})"
unzip -l "$OUT" | tail -1
