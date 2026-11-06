# 2026-11-06 - Resume local commits from their existing operation state
**Keywords:** [REFACTOR] [DOCUMENTATION] [TESTING]
**Session:** FLEET-533 architecture pass 2, item 5494

## What changed
- Define ownership and resume points for generation, staging/review, local commit and push.
- Retain the generated entry and exact scope after local rejection; inspect history after lost output before generating again.
- Explain the session progress record, merge/lock handling and remaining concurrency limits.
- Release plugin 1.0.5; keep all scoped Git command blocks unchanged.

## Why
A disposable fixture ran the real commit command successfully, then simulated a caller failure before completion reached the session. Retrying the existing entry made no duplicate commit. Restarting at generation made a second entry and documentation-only commit. Local recovery previously had no explicit resume procedure.

## Testing notes
- Seven state probes cover first commits with unrelated staged work, unrelated staged deletions, index locks, merge rejection, commit-message rejection/retry, lost caller output and linked worktree isolation.
- Regression tests cover the added local recovery and index cases; existing command and package tests remain in use.
- Tests execute Git commands and model a caller interruption; they do not prove future model adherence or provide an automatic transaction journal.

## Next steps
- FLEET-679 tracks concurrent entry/index writes; FLEET-680 tracks selected-file review snapshot isolation. Neither is fixed by these recovery instructions.
