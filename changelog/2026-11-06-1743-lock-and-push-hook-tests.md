# 2026-11-06 - Test lock ownership and local push rejection recovery

**Keywords:** [TESTING]

## What changed

- Exercise the documented stage and commit blocks while a separate live process
  holds a synthetic index lock. Verify rejection preserves its lock, HEAD,
  selected work and another owner's partially staged file, then retry with the
  same entry after the owner releases the lock.
- Exercise the documented push block with a rejecting local `pre-push` hook.
  Check its actual arguments and ref input, remote state, saved commit and dirty
  index. Correct the synthetic rejection and repeat the saved push without
  creating a commit or publishing the later local HEAD.

## Why

The existing 21 tests did not detect deleting another operation's lock at either
local boundary or bypassing a local push hook. These failures need different
recovery from a remote hook rejection.

## Testing notes

- All 23 tests pass, including isolated Claude CLI package discovery.
- Each of three disposable command mutations passes the original 21 tests and
  fails the expanded suite: remove the lock before staging, remove it before
  committing, and bypass the local push hook with `--no-verify`.
- Repositories, bare remotes, hooks and locks are disposable local fixtures.
  Startup synchronization and subprocess execution have bounded waits.
- No runtime command or dependency changed. Model adherence and concurrent
  changelog generation are not established by these tests. Existing generation
  and selected-file snapshot defects remain tracked as FLEET-679 and FLEET-680.
