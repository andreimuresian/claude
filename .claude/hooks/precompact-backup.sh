#!/usr/bin/env bash
# PreCompact hook: runs right before Claude Code compacts the conversation
# (manual /compact OR automatic when the context window fills up).
#
# What it does:
#   1. Saves whatever payload Claude Code sends on stdin (session id, trigger
#      type manual/auto, and transcript path when provided) to a timestamped
#      file, so there is always a raw record of "a compaction happened here".
#   2. Prints a systemMessage back, which Claude Code shows to the user in
#      the UI right before compacting — a visible nudge, not a silent event.
#
# IMPORTANT / honest limitation: this is a "command" hook. It cannot block
# compaction, cannot force Claude to do anything, and cannot inject text into
# Claude's own reasoning before the compact happens (that capability is only
# available on PreToolUse/PostToolUse/PermissionRequest hooks). All it can
# reliably do is (a) leave a backup file and (b) show the human a reminder.
# It is a safety net for the HUMAN, not a control over the MODEL.

set -euo pipefail

BACKUP_DIR="$HOME/.claude/compact-backups"
mkdir -p "$BACKUP_DIR"

TS="$(date +%Y%m%dT%H%M%S)"
PAYLOAD_FILE="$BACKUP_DIR/precompact-$TS.json"

# Save the raw stdin payload verbatim (whatever fields Claude Code sends).
cat > "$PAYLOAD_FILE"

printf '{"systemMessage":"PreCompact backup saved: %s -- if .claude/PROGRESS.md in this project is not up to date, run /checkpoint before you keep going."}' "$PAYLOAD_FILE"
