# Changelog Index

This directory contains detailed changelog entries for each development session. Each entry captures what changed, why decisions were made, issues encountered, and lessons learned.

## How to Use This Changelog

- **Browse by date**: Entries are organized by month below
- **Search by keyword**: Use Cmd+F to search for keywords like `[API]`, `[BUG_FIX]`, etc.
- **Find specific changes**: Each entry has a descriptive filename and summary
- **Understand decisions**: Every entry explains the "why" behind changes

## Entries by Month

### 2026-11

#### [2026-11-06-2025-macos-push-guard.md](2026-11-06-2025-macos-push-guard.md)
Refuse invalid scoped pushes across macOS shells
**Keywords**: `[BUG_FIX]` `[SECURITY]` `[TESTING]`

#### [2026-11-06-1900-changelog-races.md](2026-11-06-1900-changelog-races.md)
Preserve concurrent entries and reviewed commit snapshots
**Keywords**: `[BUG_FIX]` `[PLUGIN]` `[TESTING]`

#### [2026-11-06-1810-divergent-push-recovery.md](2026-11-06-1810-divergent-push-recovery.md)
Document divergent push recovery with a separate worktree
**Keywords**: `[DOCUMENTATION]` `[TESTING]`

#### [2026-11-06-1743-lock-and-push-hook-tests.md](2026-11-06-1743-lock-and-push-hook-tests.md)
Test lock ownership and local push rejection recovery
**Keywords**: `[TESTING]`

#### [2026-11-06-1740-local-commit-recovery.md](2026-11-06-1740-local-commit-recovery.md)
Resume local commits from their existing operation state
**Keywords**: `[REFACTOR]` `[DOCUMENTATION]` `[TESTING]`

#### [2026-11-06-1715-pinned-pushes.md](2026-11-06-1715-pinned-pushes.md)
Pin reviewed commits for push and recovery
**Keywords**: `[BUG_FIX]` `[PLUGIN]` `[SECURITY]` `[TESTING]`

#### [2026-11-06-0510-verified-installation.md](2026-11-06-0510-verified-installation.md)
Document verified installation and maintenance
**Keywords**: `[BUG_FIX]` `[DOCUMENTATION]` `[PLUGIN]` `[TESTING]`

#### [2026-11-06-0500-index-metadata-search.md](2026-11-06-0500-index-metadata-search.md)
Collect index metadata in batches
**Keywords**: `[PERFORMANCE]` `[PLUGIN]` `[TESTING]`

#### [2026-11-06-0436-commit-behavior-tests.md](2026-11-06-0436-commit-behavior-tests.md)
Test commit contents and failure recovery
**Keywords**: `[TESTING]`

#### [2026-11-06-0423-plugin-packaging.md](2026-11-06-0423-plugin-packaging.md)
Use one plugin package and release manifest
**Keywords**: `[CONFIGURATION]` `[PLUGIN]` `[REFACTOR]` `[TESTING]`

#### [2026-11-06-0405-scoped-commits-security.md](2026-11-06-0405-scoped-commits-security.md)
Scope commits to reviewed files
**Keywords**: `[BUG_FIX]` `[DOCUMENTATION]` `[SECURITY]` `[TESTING]`

### 2025-01

#### [2025-01-22-1415-readme-superiority-explanation.md](2025-01-22-1415-readme-superiority-explanation.md)
Enhanced README to explain why this changelog approach is superior to traditional single-file changelogs
**Keywords**: `[CHANGELOG]` `[DOCUMENTATION]` `[PLUGIN]` `[README]`

#### [2025-01-22-1345-marketplace-setup.md](2025-01-22-1345-marketplace-setup.md)
Set up GitHub repository and configured Claude Code plugin marketplace for the changelog plugin
**Keywords**: `[CONFIGURATION]` `[DEPLOYMENT]` `[DOCUMENTATION]` `[GITHUB]` `[MARKETPLACE]` `[PLUGIN]`

## Keyword Index

Quick reference for finding entries by topic:

- **[BUG_FIX]** (5 entries): 2026-11-06-2025, 2026-11-06-1900, 2026-11-06-1715, 2026-11-06-0510, 2026-11-06-0405
- **[CHANGELOG]** (1 entry): 2025-01-22-1415
- **[CONFIGURATION]** (2 entries): 2026-11-06-0423, 2025-01-22-1345
- **[DEPLOYMENT]** (1 entry): 2025-01-22-1345
- **[DOCUMENTATION]** (6 entries): 2026-11-06-1810, 2026-11-06-1740, 2026-11-06-0510, 2026-11-06-0405, 2025-01-22-1415, 2025-01-22-1345
- **[GITHUB]** (1 entry): 2025-01-22-1345
- **[MARKETPLACE]** (1 entry): 2025-01-22-1345
- **[PERFORMANCE]** (1 entry): 2026-11-06-0500
- **[PLUGIN]** (7 entries): 2026-11-06-1900, 2026-11-06-1715, 2026-11-06-0510, 2026-11-06-0500, 2026-11-06-0423, 2025-01-22-1415, 2025-01-22-1345
- **[README]** (1 entry): 2025-01-22-1415
- **[REFACTOR]** (2 entries): 2026-11-06-1740, 2026-11-06-0423
- **[SECURITY]** (3 entries): 2026-11-06-2025, 2026-11-06-1715, 2026-11-06-0405
- **[TESTING]** (11 entries): 2026-11-06-2025, 2026-11-06-1900, 2026-11-06-1810, 2026-11-06-1743, 2026-11-06-1740, 2026-11-06-1715, 2026-11-06-0510, 2026-11-06-0500, 2026-11-06-0436, 2026-11-06-0423, 2026-11-06-0405

## Statistics

- **Total Entries**: 13
- **Date Range**: 2025-01-22 to 2026-11-06
- **Most Used Keywords**: TESTING (11), PLUGIN (7), DOCUMENTATION (6)
