#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
for asset in mist bin/stockfish data/history.bin data/response.bin; do
    if [ ! -r "$asset" ]; then
        echo "Astra runtime: required asset missing: $asset" >&2
        exit 1
    fi
done
export MIST_STOCKFISH="$PWD/bin/stockfish"
export MIST_HISTORY_TABLE="$PWD/data/history.bin"
export ASTRA_VISIBLE_MODEL="$PWD/data/response.bin"
export ASTRA_VISIBLE_CONFIDENCE=0.25
export ASTRA_VISIBLE_PROJECT=1
export ASTRA_PERSISTENT=1
exec ./mist
