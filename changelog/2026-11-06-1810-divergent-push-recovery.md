# 2026-11-06 - Document divergent push recovery with a separate worktree

**Keywords:** [DOCUMENTATION] [TESTING]
**Session:** FLEET-533 docs pass 2, item 5497

## What changed

- Add a step-by-step guide for a saved push rejected by divergent remote history.
- Preserve the original worktree's staged and unstaged files while reconciling
  committed entries and rebuilding the shared index in a recovery worktree.
- Explain merge abort/resume, the required review before publication, and the
  ancestor check when push acknowledgement is lost and the remote advances again.
- Link the guide from README troubleshooting. Existing skill commands and
  plugin version remain unchanged.

## Why

The skill says to fetch and inspect divergence, but the existing guide gives no
complete procedure for merging both histories with a conflicting changelog index
while the original worktree contains partially staged unrelated work.

## Testing notes

- Execute the guide's marked Bash blocks against disposable local bare remotes.
  Two sessions commit distinct entries and conflicting index replacements.
- Verify rejection, conflict resolution, abort/resume, both entry payloads and
  index membership, merge parents, saved snapshot publication and containment
  after a later remote commit. Original HEAD, raw index hash, partially staged
  file, unstaged bytes and untracked file remain unchanged at every phase.
- All 23 existing tests pass, including isolated Claude CLI package discovery.
- Validate Markdown links/fragments and inspect the documentation diff.
- No real network/auth failure or model invocation was tested. Resolution is
  manual; no automatic transaction, serialization or conflict resolver is added.

## Next steps

Existing FLEET-679 and FLEET-680 track concurrent generation and selected-file
review races. This guide does not fix those defects or recover uncommitted bytes
that were already overwritten.
