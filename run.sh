#!/bin/bash
# Starts the engine. Changing to the script's own directory first means the
# binary is found regardless of the working directory the arena uses.
set -euo pipefail
cd "$(dirname "$0")"
exec ./bot
