---
description: Update .claude/PROGRESS.md in the current project with a grounded, verified snapshot of session state before context gets thin, before /compact or /clear, or at a natural milestone.
---

# /checkpoint

Update (or create) `.claude/PROGRESS.md` in the **current project's repo root**
with a snapshot of real state. This file is the source of truth that survives
`/compact`, `/clear`, and new sessions — it is a plain file in the working
directory, not part of the conversation transcript, so none of those commands
can touch it.

## Rules

1. **Read before writing.** If `.claude/PROGRESS.md` already exists, read it
   first and update it — don't blindly overwrite. Keep a "Log" section that
   accumulates entries (newest on top), and a "Current state" section that
   you fully rewrite each time (it should always reflect *now*, not history).

2. **Be grounded — verify, don't recall.** Before writing anything, check it
   against reality, not against your memory of the conversation:
   - Run `git log --oneline -10`, `git status`, `git diff --stat` to see what
     is actually committed vs. uncommitted.
   - Re-check open questions/bugs by actually looking (grep, run tests) if
     that's fast, rather than trusting what you remember discussing.
   - If something the user asked for was NOT done, or was tried and failed,
     say so explicitly. Do not paper over failures or partial work — a
     checkpoint that hides a failure is worse than no checkpoint, because it
     will be trusted next session.

3. **Write for a reader with zero memory of this conversation.** Assume
   whoever reads this next (you, in a fresh session, or the user) knows
   nothing except what's in the repo and this file.

## Structure to write

```markdown
# Progress

## Current state (as of <ISO timestamp>)
- What the project/feature is trying to do (1-3 sentences).
- What is DONE and verified (works, tested, committed — cite commit hashes
  or file paths).
- What is IN PROGRESS (specifically where it's stuck or what's half-done).
- What is NOT started / explicitly deferred, and why.
- Known failures or things that were tried and did NOT work (so they are
  not retried blindly next time).
- Open questions that need a human decision.

## Next steps
Ordered, concrete, actionable — not vague ("keep improving X").

## Log
### <ISO timestamp>
- What changed since the previous checkpoint. Short bullet list.
(older entries below, newest always on top)
```

## After writing

1. Show the user a short diff-style summary of what you added/changed in
   PROGRESS.md — don't just say "done."
2. If the file is new, remind the user it's an untracked file — tell them
   whether you're adding it to git (recommended, so history of the log
   itself is preserved) or leaving it untracked, and ask if unclear.
3. Do NOT run `/compact` or `/clear` yourself after checkpointing — that's
   the user's call to make, not something to chain automatically.
