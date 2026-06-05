#!/usr/bin/env bash
# Wire jobclaw-skills into your agent runtime(s). Thin wrapper over setup_runtime.py.
#
#   ./scripts/install.sh                 # wire all runtimes (codex, cursor, claude, hermes, openclaw)
#   ./scripts/install.sh codex cursor    # wire specific runtimes
#   ./scripts/install.sh all --global    # also link user-level dirs (~/.agents/skills, ~/.hermes/skills)
#   ./scripts/install.sh all --copy      # copy instead of symlink (Windows / restricted FS)
#   ./scripts/install.sh --dry-run       # show what would happen
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$DIR/scripts/setup_runtime.py" "$@"
