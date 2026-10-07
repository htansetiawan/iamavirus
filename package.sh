#!/bin/bash
# Builds the submission archive.
#
# The compiled binary is deliberately excluded: the course builds for Linux
# amd64 and the documentation warns against uploading a host executable.
set -euo pipefail
cd "$(dirname "$0")"

OUT="${1:-/tmp/iamavirus-cpp.zip}"
# An optional release directory (observe.onnx, score.onnx, model_manifest.json)
# is packaged as model/ and selected at play time with FOW_MODE in run.sh.
MODEL="${2:-}"
rm -f "$OUT"
rm -rf model
if [ -n "$MODEL" ]; then
  mkdir -p model
  cp "$MODEL"/observe.onnx "$MODEL"/score.onnx "$MODEL"/model_manifest.json model/
fi
zip -q -r "$OUT" \
  run.sh build.sh test.sh README.md \
  bot.cc engine.cc belief.cc search.cc evaluation.cc observation.cc \
  transposition.cc regret.cc position.cc move.cc bitboard.cc \
  neural_observation.cc neural_inference.cc \
  bitboard.h move.h position.h observation.h evaluation.h transposition.h \
  search.h belief.h regret.h engine.h piece_square.h \
  neural_observation.h neural_inference.h \
  tests tools \
  $( [ -d model ] && echo model ) \
  -x '*.DS_Store' -x '*__pycache__*'
echo "wrote $OUT"
unzip -l "$OUT" | tail -3
