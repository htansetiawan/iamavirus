#!/bin/bash
# Builds the engine. The course runtime provides g++ 12 with C++20 and no
# network access, so everything compiled here is in this archive.
set -euo pipefail

SOURCES="bot.cc engine.cc belief.cc search.cc evaluation.cc observation.cc
         transposition.cc regret.cc position.cc move.cc bitboard.cc
         neural_observation.cc neural_inference.cc opponent_model.cc"
BASE="-O2 -std=c++20 -Wall -Wextra -DNDEBUG -pthread"

# POPCNT is used on nearly every line of the search. Without it the compiler
# emits a software fallback, so it is worth enabling -- but only after proving
# the instruction actually runs here, since a SIGILL mid-game would lose every
# match. Builds and games share the same runtime image, so a check at build time
# is meaningful.
EXTRA=""
probe=$(mktemp -d)
cat > "$probe/probe.cc" <<'PROBE'
#include <bit>
#include <cstdint>
int main() { return std::popcount(uint64_t{0xF0F0F0F0F0F0F0F0}) == 32 ? 0 : 1; }
PROBE
if g++ -O2 -std=c++20 -mpopcnt "$probe/probe.cc" -o "$probe/probe" 2>/dev/null \
   && "$probe/probe" 2>/dev/null; then
  EXTRA="-mpopcnt"
  echo "build: hardware popcount available"
else
  echo "build: falling back to portable popcount"
fi
rm -rf "$probe"

# ONNX Runtime, for the neural and hybrid modes. The course runtime installs
# the native SDK at /opt/onnxruntime; ORT_HOME overrides that for local builds.
# Without it the bot still builds and plays in cpp mode, so a missing SDK can
# never be the reason a submission fails.
ORT="${ORT_HOME:-/opt/onnxruntime}"
LINK=""
if [ -f "$ORT/include/onnxruntime_cxx_api.h" ] && ls "$ORT"/lib/libonnxruntime.so* >/dev/null 2>&1; then
  EXTRA="$EXTRA -DFOW_WITH_ONNX -I$ORT/include"
  LINK="-L$ORT/lib -Wl,-rpath,$ORT/lib -lonnxruntime"
  echo "build: ONNX Runtime found at $ORT"
else
  echo "build: no ONNX Runtime; neural and hybrid modes will fall back to cpp"
fi

# Warnings are deliberately not errors here. GCC at -O2 occasionally emits a
# false positive for array bounds or maybe-uninitialized inside heavily inlined
# bitboard loops, and a warning must never be the reason a submission fails to
# build.
# shellcheck disable=SC2086
if g++ $BASE $EXTRA $SOURCES -o bot $LINK; then
  echo "build: done"
  exit 0
fi

# Last resort: a lower optimisation level, in case the failure was an optimiser
# problem rather than a real error. A slower bot still plays; no bot does not.
echo "build: retrying at -O1" >&2
# shellcheck disable=SC2086
# shellcheck disable=SC2086
g++ -O1 -std=c++20 -DNDEBUG -pthread $EXTRA $SOURCES -o bot $LINK
echo "build: done at -O1"
