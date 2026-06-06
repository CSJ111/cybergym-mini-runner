#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export CYBERGYM_TASK_IDS="${CYBERGYM_TASK_IDS:-arvo:368}"
exec bash "$SCRIPT_DIR/setup_cybergym_subset.sh"
