# 2026-11-06 - Preserve concurrent entries and reviewed commit snapshots

**Keywords:** [BUG_FIX] [PLUGIN] [TESTING]

## What Changed

- Add a bundled standard-library Python helper for the commit skill. Exclusive
  entry allocation adds numeric suffixes for identical minute/slug names.
- Hold a persistent advisory lock from allocation through inventory, metadata
  collection and atomic README replacement. Amendments and rebuilds share it.
- Freeze selected staged blobs in a private index. Validation hooks run against
  that snapshot; changed trees require a new review. Create the exact reviewed
  tree with commit-tree and compare-and-swap the saved branch ref.
- Reconcile only unchanged selected index entries under the real Git index lock.
  Later working edits and newer selected or unrelated staging survive.
- Retain the root package layout and pinned push commands; release version 1.0.6.

## Why

FLEET-679 allowed concurrent sessions to overwrite an entry or publish a stale
inventory. FLEET-680 committed selected working-tree contents again after review,
allowing a later edit into the commit.

## Testing Notes

- The full suite exercises documented shell blocks in disposable repositories,
  including concurrent identical names, inventory/index interleavings, process
  termination, rejection/retry, literal paths, scoped commits and pinned pushes.
- The baseline verifier requires four assertion failures on main: entry loss,
  stale index, post-review edit and retry. Main's generation steps are prose, so
  the baseline explicitly adapts those steps to shell; main's commit blocks run
  unchanged. Fixed generation uses the actual documented helper command.
- Claude CLI validation and isolated local-marketplace installation/discovery
  remain part of the suite. No model invocation or real repository race is tested.

## Recovery

Interrupted generation can retain an owned partial entry and hidden temporary
file while preserving existing entries, the old index and staged work. Repair
that recorded entry and rebuild under the same lock. Keep the private review
state until commit/ref/index reconciliation has been inspected after interruption.
