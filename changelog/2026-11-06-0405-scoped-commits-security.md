# 2026-11-06 - Scope commits to reviewed files
**Keywords:** [SECURITY] [BUG_FIX] [TESTING] [DOCUMENTATION]
**Session:** FLEET-533, Codex burn A, lane 3, security pass 1

## What Changed
- Replaced broad repository/directory staging with explicit literal file paths.
- Commit the reviewed file list with `--only`, preserving unrelated staged work.
- Explain how to handle filenames, messages and changelog contents as data, and
  check changelog destinations before writing.
- Added five disposable-repository regression tests that execute the skill's
  documented commands, plus the local test command in the README.
- Bumped the plugin and marketplace patch version to 1.0.1 for this fix.

## Why
The old `git add .` workflow committed an unrelated local-only file in a sandbox.
Explicit staging alone still committed an unrelated pre-staged file with a plain
commit. File-scoped staging and committing address both reproduced cases.

## Issues Encountered
The Codex skill validator rejects the pre-existing human-readable skill name on
both original main and this branch. Current Claude Code documentation permits
plain spaces in names; this audit preserves the plugin's existing name rather
than treating a Codex-specific validation rule as a Claude Code defect.

## Dependencies
None. Tests use Python's standard library, Bash and Git; the plugin still has no
runtime package dependencies.

## Testing Notes
- Five Git sandbox tests pass: local-only/unrelated staged files, literal hostile
  paths and messages, tracked deletion, failed stage, and empty scope.
- All three negative controls are detected: broad staging/plain commit, plain
  commit with unrelated staged work, and Git pathspec magic enabled.
- Gitleaks 8.30.1 full-history scan: 18 commits, no leaks found; a synthetic
  positive control is detected. Scanner output was redacted.
- These tests verify documented commands, not whether every future language-model
  invocation follows the instructions. No authenticated Claude session was run.

## Next Steps
- Continue other audit dimensions through the FLEET-533 queue.
