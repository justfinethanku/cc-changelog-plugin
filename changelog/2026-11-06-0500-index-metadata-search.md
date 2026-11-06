# 2026-11-06 - Collect index metadata in batches
**Keywords:** [PERFORMANCE] [PLUGIN] [TESTING]
**Session:** FLEET-533, Codex burn A, lane 8, performance pass 1

## What Changed
- Replace per-entry full reads during index generation with a batched Grep
  content query for titles, keywords and legacy summary/keyword sections.
- Reconcile search results with the file inventory and use targeted reads for
  missing metadata or unusual layouts, including nonstandard filenames.
- Keep full index rebuilding, scoped Git commands and installation unchanged.
- Release the instruction update as plugin version 1.0.3.

## Why
The previous index procedure loaded every entry's complete body into the
conversation to extract a few metadata fields. The five existing entries total
10,628 bytes. A ripgrep content query using the documented pattern and one line
of context returns 1,990 bytes while preserving index metadata and memberships.

## Dependencies
No new runtime dependencies. The skill uses the existing Glob, Grep and Read
tools; ripgrep was used locally to measure the search output.

## Testing Notes
- Compare metadata, monthly memberships and keyword memberships for all five
  existing entries, including both historical layouts.
- Synthetic fixtures cycle those layouts with unique filenames and added body
  details. With 1,000 entries and about 8 KB of added detail each, full reads
  total 10,338,600 bytes and the search returns 327,197 bytes.
- These are response-byte measurements, not token counts, model latency or
  end-to-end authenticated Claude session measurements. Search still scans the
  entry files locally, and the generated index still grows with entry count.

## Next Steps
Other audit dimensions continue through the existing FLEET-533 queue.
