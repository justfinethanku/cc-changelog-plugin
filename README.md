# Git Changelog Plugin

Automatically creates structured, searchable changelog entries when committing code to git. Unlike traditional single-file changelogs that become unwieldy merge-conflict nightmares and lose context over time, this plugin creates individual timestamped entries that never conflict during merges, preserve complete context for each coding session, and build a rich searchable knowledge base of your project's evolution. Each entry captures not just what changed but WHY decisions were made, problems encountered, and lessons learned - creating a development journal that's infinitely more useful than a chronological list of bullet points. Plus, it's way cooler than anything Mike Dion proposed because it actually solves the real problems developers face: merge conflicts, lost context, and the inability to quickly find that one weird fix you did six months ago at 2am.

## Features

- **Auto-documentation**: Every commit creates a detailed changelog entry
- **Structured format**: Captures what changed, why, issues encountered, testing notes, and next steps
- **Searchable**: Auto-generated index with keyword search
- **Smart keywords**: Suggests keywords based on file paths modified
- **Merge-friendly**: Timestamps prevent filename collisions across branches
- **Universal**: Works with any tech stack (JavaScript, Python, Rust, etc.)

## Installation

### Option 1: Via Plugin Manager (Recommended)

1. **Open your terminal**
2. **Start Claude Code:**
   ```bash
   claude
   ```
3. **Add the marketplace to Claude Code:**
   ```
   /plugin marketplace add https://github.com/justfinethanku/cc-changelog-plugin
   ```
4. **Install the plugin:**
   ```
   /plugin install changelog
   ```
5. **Done!** The plugin is now installed and ready to use

### Option 2: Manual Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/justfinethanku/cc-changelog-plugin
   ```

2. **Choose where to install:**

   **For all projects** (personal skills directory):
   ```bash
   cp -r cc-changelog-plugin/skills/commit ~/.claude/skills/
   ```

   **For current project only** (project-specific):
   ```bash
   cp -r cc-changelog-plugin/skills/commit .claude/skills/
   ```

## Usage

The skill activates automatically when you ask Claude Code to commit changes:

```
"Commit these changes"
"Let's commit this work"
"Create a git commit with changelog"
```

You can also provide a commit message:

```
"Commit with message: Add user authentication"
```

### Skip Changelog (for trivial changes)

```
"Commit without changelog: Fix typo in README"
```

### Amend Last Entry

```
"Amend the last changelog entry with these changes"
```

## What Gets Created

### First Time Setup

When you first commit with the plugin, it creates:

```
changelog/
├── .changelog-keywords.txt    # Predefined and project-specific keywords
└── README.md                  # Auto-generated searchable index
```

### After Each Commit

```
changelog/
└── 2025-01-15-1430-feature-name.md   # Timestamped entry
```

## Changelog Entry Format

Each entry includes:

- **What Changed**: Files modified with descriptions
- **Why**: Decision rationale
- **Issues Encountered**: Problems and workarounds
- **Dependencies**: NPM/pip/cargo packages added
- **Testing Notes**: What was tested, what wasn't, edge cases
- **Next Steps**: Remaining tasks

## Searching Your Changelog

The auto-generated `changelog/README.md` includes:

- **Keyword Index**: All keywords with entry counts
- **Monthly Groups**: Entries organized by month
- **One-line Summaries**: Quick overview of each session

Use Cmd+F to search for keywords like `[DATABASE]`, `[BUG_FIX]`, etc.

## Merge-Friendly Design

- Timestamps in filenames prevent collisions across branches
- Individual changelog entries never conflict during merge
- If `README.md` conflicts, ask Claude to regenerate it

## Example Keywords

Common keywords automatically suggested:

- `[FRONTEND]`, `[BACKEND]`, `[DATABASE]`
- `[API]`, `[UI]`, `[COMPONENTS]`
- `[TESTING]`, `[BUG_FIX]`, `[FEATURE]`
- `[REFACTOR]`, `[PERFORMANCE]`, `[SECURITY]`
- `[DEPLOYMENT]`, `[DOCUMENTATION]`, `[MIGRATION]`

Add project-specific keywords as needed - they're automatically added to the vocabulary.

## Best Practices

**DO:**
- ✅ Create entry for every feature, bug fix, or meaningful change
- ✅ Be specific in "What Changed" (file paths, function names)
- ✅ Explain "Why" decisions were made (most valuable for future you!)
- ✅ Document failed experiments (valuable context)

**DON'T:**
- ❌ Use for typo fixes (say "commit without changelog")
- ❌ Use generic descriptions ("made changes")
- ❌ Skip "Why" section
- ❌ Forget to test before committing

## How It Works

1. **Analyzes changes**: Runs `git diff --stat` to see what changed
2. **Suggests keywords**: Based on file paths modified
3. **Prompts for context**: What, why, issues, testing notes
4. **Creates entry**: Timestamped markdown file in `changelog/`
5. **Updates index**: Regenerates README with all entries
6. **Commits everything**: Code + changelog together
7. **Optional push**: Prompts to push to remote

## Contributing

Issues and PRs welcome at: https://github.com/justfinethanku/cc-changelog-plugin

## License

MIT License - See LICENSE file for details

## Author

Jonathan Edwards
