#!/bin/bash
# Builds and runs every unit test, then the differential test against the
# course referee if a Python environment with python-chess is available.
set -euo pipefail
cd "$(dirname "$0")"

LIB="engine.cc belief.cc search.cc evaluation.cc observation.cc
     transposition.cc regret.cc position.cc move.cc bitboard.cc
     neural_observation.cc neural_inference.cc opponent_model.cc"
FLAGS="-O2 -std=c++20 -Wall -Wextra -Werror -pthread"
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT

status=0
for suite in bitboard position observation evaluation search belief regret engine neural; do
  test -f "tests/${suite}_test.cc" || continue
  # shellcheck disable=SC2086
  g++ $FLAGS "tests/${suite}_test.cc" $LIB -o "$OUT/${suite}_test"
  "$OUT/${suite}_test" || status=1
done

if [ -n "${FOW_PYTHON:-}" ] && [ -x "${FOW_PYTHON}" ]; then
  # shellcheck disable=SC2086
  g++ $FLAGS tools/conformance_main.cc $LIB -o "$OUT/conformance"
  FOW_CONFORMANCE_BINARY="$OUT/conformance" \
    "$FOW_PYTHON" tests/conformance_test.py --games "${FOW_GAMES:-150}" || status=1
else
  echo "conformance test skipped (set FOW_PYTHON to a python with python-chess)"
fi
exit $status
