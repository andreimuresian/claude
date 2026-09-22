#!/usr/bin/env bash
# PostCompact hook: runs right after a compaction finishes (manual or auto).
# Appends a timestamped record of the event (including whatever payload
# Claude Code sends, which may include the resulting summary) to a single
# running log file. This is the audit trail: "when did compaction happen,
# and what did the tool report about it" -- so nothing is invisible.

set -euo pipefail

BACKUP_DIR="$HOME/.claude/compact-backups"
mkdir -p "$BACKUP_DIR"

LOG_FILE="$BACKUP_DIR/postcompact-log.txt"

{
  printf '\n===== PostCompact %s =====\n' "$(date -Iseconds)"
  cat
  printf '\n'
} >> "$LOG_FILE"
