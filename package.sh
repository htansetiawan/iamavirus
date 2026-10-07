#!/bin/bash
# Builds the submission archive.
#
# The compiled binary is deliberately excluded: the course builds for Linux
# amd64 and the documentation warns against uploading a host executable.
set -euo pipefail
cd "$(dirname "$0")"

OUT="${1:-/tmp/iamavirus-cpp.zip}"
rm -f "$OUT"
zip -q -r "$OUT" \
  run.sh build.sh test.sh README.md \
  bot.cc engine.cc belief.cc search.cc evaluation.cc observation.cc \
  transposition.cc regret.cc position.cc move.cc bitboard.cc \
  bitboard.h move.h position.h observation.h evaluation.h transposition.h \
  search.h belief.h regret.h engine.h piece_square.h \
  tests tools \
  -x '*.DS_Store' -x '*__pycache__*'
echo "wrote $OUT"
unzip -l "$OUT" | tail -3
