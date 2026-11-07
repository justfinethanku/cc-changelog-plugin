# 2026-11-06 - Preserve concurrent entries and reviewed commit snapshots

**Keywords:** [BUG_FIX] [PLUGIN] [TESTING]

## What Changed

- Use a standard-library Python helper only for generation. Exclusive entry
  allocation adds numeric suffixes for identical minute/slug names.
- Share a persistent advisory lock in Git's common directory across worktrees.
  Resolve changelog files from the repository root, including from subdirectories.
- Keep the model-written README layout. Publish a private draft atomically only
  if it includes every current entry basename; refuse stale drafts and request
  a complete rebuild. Replacement files are chmod 0644 before publication.
- Freeze selected staged blobs in a private index with stock Git shell commands.
  Normal Git commit runs hooks and handles ref locking; compare the final commit
  to the reviewed tree and ask for review if a hook changed it.
- Preserve the shared index's content, including unrelated and newer selected
  staging, and later working edits. Refresh stat information after success and
  remove the private review directory once the commit SHA is recorded.
- Retain the root package layout and pinned push commands; release version 1.0.6.

## Why

FLEET-679 allowed concurrent sessions to overwrite an entry or publish a stale
inventory. FLEET-680 committed selected working-tree contents again after review,
allowing a later edit into the commit.

## Testing Notes

- The full suite exercises documented shell blocks in disposable repositories,
  including concurrent identical names, inventory/index interleavings, process
  termination, rejection/retry, literal paths, scoped commits and pinned pushes.
- The PR body records fail-on-main evidence for entry loss, stale index,
  post-review edit and retry. The maintained suite executes the documented
  commands directly, without a baseline adapter or implementation branches.
- Index tests verify byte-for-byte preservation of this repository's README,
  stale-draft refusal and retry, common locks across worktrees, subdirectory
  invocation and replacement permissions. Python 3.8+ generation supports
  Linux/macOS; fcntl means Windows is not supported. Committing needs no Python.
- Claude CLI validation and isolated local-marketplace installation/discovery
  remain part of the suite. No model invocation or real repository race is tested.

## Recovery

Interrupted generation can retain an owned partial entry and hidden temporary
file while preserving existing entries, the old index and staged work. Repair
that recorded entry and rebuild under the same lock. Keep the private review
state on rejection; inspect history after an interruption before retry or cleanup.
