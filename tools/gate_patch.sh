#!/bin/bash
# Gate a belief/engine patch without touching the working tree:
#   bash tools/gate_patch.sh <patch> <outdir> [core]
# Applies the patch in a throwaway worktree at HEAD, builds the belief and
# engine suites and the benchmark there, runs the suites, then runs the
# benchmark on the fatal plies only (stride 1000, 400k nodes, one search
# thread) for the root binary and for the patched binary in FOW_HISTORY_MODE 0
# and 1, and reports how many fatal-ply choices differ between root and mode 0
# (identity screen) and the summary lines of all three.
set -euo pipefail
PATCH="$(realpath "$1")"; OUT="$(realpath -m "$2")"; CORE="${3:-5}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WT="/tmp/claude-1000/wt-gate-$$"
mkdir -p "$OUT"
git -C "$ROOT" worktree add -q "$WT" HEAD
trap 'git -C "$ROOT" worktree remove --force "$WT" >/dev/null 2>&1 || true' EXIT
cd "$WT"
git apply --check "$PATCH" && git apply "$PATCH"
LIB="engine.cc belief.cc search.cc evaluation.cc observation.cc transposition.cc regret.cc position.cc move.cc bitboard.cc neural_observation.cc neural_inference.cc opponent_model.cc"
g++ -O2 -std=c++20 -Wall -Wextra -Werror -pthread tests/belief_test.cc $LIB -o "$OUT/belief_test"
g++ -O2 -std=c++20 -Wall -Wextra -Werror -pthread tests/engine_test.cc $LIB -o "$OUT/engine_test"
g++ -O2 -std=c++20 -mpopcnt -pthread tools/benchmark_corpus.cc $LIB -o "$OUT/benchmark_patched"
nice -n 8 taskset -c "$CORE" "$OUT/belief_test" 2>&1 | tail -1 | tee "$OUT/belief_suite.txt"
nice -n 8 taskset -c "$CORE" "$OUT/engine_test" 2>&1 | grep -E "failures" | tee "$OUT/engine_suite.txt"
cd "$ROOT"
g++ -O2 -std=c++20 -mpopcnt -pthread tools/benchmark_corpus.cc $LIB -o "$OUT/benchmark_root"
SEATS="$ROOT/data/benchmark-seats.txt"
FOW_BOOK=off FOW_CELL_THREADS=1 nice -n 8 taskset -c "$CORE" "$OUT/benchmark_root" "$SEATS" 1000 400000 verbose > "$OUT/root.txt" 2>&1
FOW_BOOK=off FOW_CELL_THREADS=1 FOW_HISTORY_MODE=0 nice -n 8 taskset -c "$CORE" "$OUT/benchmark_patched" "$SEATS" 1000 400000 verbose > "$OUT/mode0.txt" 2>&1
FOW_BOOK=off FOW_CELL_THREADS=1 FOW_HISTORY_MODE=1 nice -n 8 taskset -c "$CORE" "$OUT/benchmark_patched" "$SEATS" 1000 400000 verbose > "$OUT/mode1.txt" 2>&1
python3 - "$OUT" <<'PY'
import re, sys
out=sys.argv[1]
pat=re.compile(r'^\s+(\S+)\s+vs \S+\s+ply\s+(\d+)\s+real played \S+\s+\(lost\)\s+engine plays (\S+)')
def choices(path):
    d={}
    for line in open(path):
        m=pat.match(line)
        if m: d[(m[1],m[2])]=m[3]
    return d
root=choices(f"{out}/root.txt"); m0=choices(f"{out}/mode0.txt")
common=[k for k in root if k in m0]
diff=sum(1 for k in common if root[k]!=m0[k])
print(f"identity screen: {diff} of {len(common)} fatal-ply choices differ between root and mode 0")
for name in ("root","mode0","mode1"):
    t=open(f"{out}/{name}.txt").read()
    g=lambda p: (re.search(p,t).group(1) if re.search(p,t) else '?')
    print(f"{name:6s} king losses {g(r'immediate king losses\s+: \d+ \(([\d.]+%)\)')} attacker held {g(r'true attacker held at fatal plies ([\d.]+)')} survives {g(r'survives\s+: (\d+)')}")
PY
