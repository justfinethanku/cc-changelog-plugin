# 2026-11-06 - Refuse invalid scoped pushes across macOS shells

**Keywords:** [BUG_FIX] [SECURITY] [TESTING]
**Session:** FLEET-716, Mac Mini 1

## What Changed

- Replace the push block's regex and implicit `set -e` failure handling with
  POSIX character/length checks and explicit exits for every validation failure.
- Brace the saved commit and branch in the refspec so zsh preserves the colon.
- Run every push workflow test under available system Bash, zsh, Homebrew Bash,
  and a distinct Bash on PATH. Support both unittest discovery and module runs.
- Give each invalid-input subtest a fresh bare remote, compare all remote refs,
  and test standalone and conditional callers with 14 invalid inputs each.

## Why

On Apple Bash 3.2.57 the original `[[ "$reviewed_commit" =~
^([0-9a-f]{40}|[0-9a-f]{64})$ ]]` returns 1 for HEAD, but `set -e` does not exit.
The subsequent Git checks accept HEAD and push the moving tip. Five original
subtests fail because the HEAD case changes their shared remote; the zero SHA
and three bad destinations individually fail without pushing.

This is a real Bash 3.2 guard defect. The Mac's default zsh 5.9 rejects all six
original invalid inputs, so Claude Code using that login shell was not exposed
to this invalid-input bypass. Separately, zsh interprets the original
`$reviewed_commit:refs` as parameter modifiers and corrupts valid refspecs.
Explicit validation exits also work when a caller tests the block in `if`,
a context where shell `set -e` behavior cannot be relied on.

## Testing Notes

- Trace the original block with `-x` against fresh local bare remotes under
  Bash 3.2.57, zsh 5.9 and temporary Homebrew Bash 5.3.20; verify every ref.
- Apple Git 2.54.0 is the Git used for local tests. Linux Git 2.43 and 2.30
  results were supplied in the task and were not independently rerun.
- Full suite: 57/57 pass on Python 3.13.12; push workflows: 8/8 per shell,
  including 28 invalid-input subtests per shell. No tests are skipped.
- Apple's default Python 3.9 has a separate pre-existing generation-test
  instrumentation failure: a monkeypatched `os.open` becomes a bound pathlib
  accessor, passing four positional arguments. Run the full suite with the
  already installed Python 3.13.12; generation/commit code stays unchanged.
- No real remote receives test pushes. The temporary Bash copy is not installed.

## Skipped outbound sends

Skip the skill's normal real-remote push step except the authorized PR branch.
No outside-fleet email, message or webhook instruction was found. No Linear
changes or merge are part of this task.
