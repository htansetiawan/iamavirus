#!/bin/bash
# Starts the engine. Changing to the script's own directory first means the
# binary is found regardless of the working directory the arena uses.
#
# FOW_MODE selects the decision procedure: cpp (default), neural or hybrid.
# The neural modes read the release in FOW_MODEL_DIR (default model/, which
# package.sh fills) and fall back to cpp if the graphs cannot be loaded.
# Set it here for a submission once the evaluation report says which mode
# earned release status, e.g. `export FOW_MODE=hybrid`.
set -euo pipefail
cd "$(dirname "$0")"
export FOW_MODE="${FOW_MODE:-hybrid}"
exec ./bot
