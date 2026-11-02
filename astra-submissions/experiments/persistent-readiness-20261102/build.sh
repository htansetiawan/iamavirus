#!/bin/bash
# Standalone C-engine build, including the learned-response adapter and proofs.
set -uo pipefail
cd "$(dirname "$0")"
[ -f bin/stockfish ] && chmod +x bin/stockfish
SOURCES="src/adapter.c src/belief.c src/board.c src/cfr.c src/eval.c src/front.c src/gtcfr.c src/main.c src/movemodel.c src/proof.c src/response.c src/search.c src/sfeval.c"
FLAGS="-O2 -pthread -D_POSIX_C_SOURCE=199309L"
for CC in gcc cc; do
    if command -v "$CC" >/dev/null 2>&1 && "$CC" -std=c11 $FLAGS $SOURCES -lm -o mist; then
        echo "build: done ($CC)"
        exit 0
    fi
done
if (rm -rf build-xc && mkdir build-xc && for f in $SOURCES; do
    g++ -x c -std=c11 $FLAGS -c "$f" -o "build-xc/$(basename "$f" .c).o" || exit 1
done && g++ $FLAGS build-xc/*.o -lm -o mist); then
    echo "build: done (g++ -x c)"
    exit 0
fi
if g++ -x c++ -std=c++20 -fpermissive -w $FLAGS $SOURCES -lm -o mist; then
    echo "build: done (g++ as C++)"
    exit 0
fi
echo "build: failed" >&2
exit 1
