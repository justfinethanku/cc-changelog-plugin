# 2026-11-06 - Test commit contents and failure recovery
**Keywords:** [TESTING]
**Session:** FLEET-533, Codex burn A, lane 4, tests pass 1

## What Changed
- Verify selected files commit their reviewed working-tree contents, including
  Unicode and changes newer than the staged version.
- Cover already-staged changes and a first commit containing code, an entry,
  the keyword vocabulary and the changelog index.
- Verify whitespace-check and pre-commit hook failures preserve HEAD and work,
  retain unrelated staged changes, and leave a rejected commit retryable.
- Bound each Git/Bash test subprocess to 15 seconds.

## Why
Existing tests checked commit paths but did not assert file contents or these
success and failure paths. The documented Git commands already handle them;
this change adds coverage without changing skill or package behavior.

## Issues Encountered
Staging precedes whitespace validation. Failed validation leaves the selected
changes staged; the tests record this behavior rather than expecting rollback.

## Dependencies
No new dependencies.

## Testing Notes
- All 12 tests pass, including the existing isolated Claude CLI integration.
- Four disposable mutations pass the five original Git tests and fail the
  expanded suite: changing selected contents, omitting whitespace validation,
  bypassing hooks, and requiring an existing HEAD before committing.
- These tests execute documented shell blocks against temporary repositories;
  they do not test model adherence or automatic Markdown generation.

## Next Steps
Other audit dimensions continue through the existing FLEET-533 queue.
