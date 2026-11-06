# Git Changelog Plugin

Create structured, searchable changelog entries while committing code with
Claude Code. The skill records what changed, why decisions were made, problems
encountered, testing notes, and next steps in individual Markdown files. A
regenerated index groups entries by month and keyword.

The workflow runs when Claude invokes the skill. It does not intercept every
`git commit`: there is no Git hook or background process. You can request a
changelog in conversation or invoke the installed plugin skill explicitly.

## Prerequisites

- A local Claude Code installation. Setup commands below were checked with
  **Claude Code 2.1.318 on Linux** on November 6, 2026. See the official
  [Claude Code setup guide](https://code.claude.com/docs/en/setup) to install it.
- Git and Bash available to Claude Code, and a Git repository containing work
  you intend to commit. Configure your Git author identity before committing.
- Network access to GitHub for marketplace installation and updates.
- A working Claude Code sign-in or provider configuration for actual skill use.
  Installing and inspecting the plugin does not make a model request.

There is no `npm install`, Python environment, or separate API key for this
plugin. Python 3 is needed only to run the contributor tests.

## Installation

### Install from the marketplace

Run these commands in your terminal. The default user scope makes the plugin
available to you across projects on this machine.

<!-- install-marketplace -->
```bash
claude plugin marketplace add https://github.com/justfinethanku/cc-changelog-plugin
claude plugin install changelog@changelog-plugin-marketplace --scope user
```

Verify the installed version, enabled state, and skill inventory:

<!-- verify-marketplace -->
```bash
claude plugin list --json
claude plugin details changelog@changelog-plugin-marketplace
```

The list should include `changelog@changelog-plugin-marketplace` with
`enabled: true`. Details should show Git Changelog and one skill named `commit`.
Restart an existing Claude Code session after installation, then work from the
Git repository you want to document.

In an interactive Claude Code terminal session, the equivalent commands are
`/plugin marketplace add https://github.com/justfinethanku/cc-changelog-plugin`
and `/plugin install changelog@changelog-plugin-marketplace`. The install command
opens the plugin details panel; choose an installation scope and complete the
installation there.

### Copy the skill manually

Use this alternative when you want a personal or project skill instead of a
marketplace plugin. It does not register a plugin or receive plugin updates.
Choose one installation method to avoid loading duplicate copies. Review any
existing `commit` skill before copying: the copy overwrites same-named files.

First clone the source into a working directory:

<!-- clone-manual -->
```bash
git clone https://github.com/justfinethanku/cc-changelog-plugin
```

For a personal skill, run from the directory containing that clone:

<!-- install-personal -->
```bash
mkdir -p ~/.claude/skills
cp -R cc-changelog-plugin/skills/commit ~/.claude/skills/
test -f ~/.claude/skills/commit/SKILL.md
```

For a project skill, run from the root of your **target Git repository**:

<!-- install-project -->
```bash
mkdir -p .claude/skills
cp -R /PATH/TO/cc-changelog-plugin/skills/commit .claude/skills/
test -f .claude/skills/commit/SKILL.md
```

Replace `/PATH/TO/cc-changelog-plugin` with the absolute path to the source clone.
Commit `.claude/skills/commit/` if you want collaborators to receive this skill.
The `test -f` commands exit successfully without output when the layout is correct.
Start a new local Claude Code session and use `/skills` to inspect the copied
skill. Copied skills do not appear in `claude plugin list`.

See [installation methods and Claude surfaces](CLAUDE_SKILLS_EXPLAINED.md) for
how a plugin differs from copied skills and API or cloud environments.

## Try the workflow

From a Git repository with a change you intend to commit, start Claude Code:

```bash
claude
```

For a marketplace installation, enter:

```text
/changelog:commit
```

You can also ask in conversation, for example:

```text
Create a git commit with a changelog for these changes.
Commit with message: Add user authentication.
```

Claude can select the skill from its description; the explicit command avoids
relying on automatic selection. Review the proposed scope, entry, and diff.
The workflow asks for context, writes an entry and index, commits the selected
files, and offers to push. Unrelated staged files stay staged. Selected files
are committed in full; separate unrelated hunks in those files first.

After the workflow, inspect the result with:

```bash
git show --stat --oneline HEAD
git status --short
```

Check that the commit contains the intended code and changelog files and that
the reported SHA matches. A push is a separate step requiring a configured
remote and access to it. The conversational flow is model-driven; installation
and deterministic Git tests do not guarantee every model's adherence.

For a trivial change, ask `Commit without changelog: Fix typo in README`.
To continue the same session entry, ask `Amend the last changelog entry with
these changes`. This edits the entry; it does not by itself request a Git
`commit --amend` or a history rewrite.

## Generated files and search

On first use, the workflow creates a keyword vocabulary, an index, and an entry:

```text
changelog/
├── .changelog-keywords.txt
├── README.md
└── YYYY-MM-DD-HHMM-descriptive-slug.md
```

Entries include **What Changed**, **Why**, **Issues Encountered**,
**Dependencies**, **Testing Notes**, and **Next Steps**. The index contains
monthly groups, summaries, and a keyword index. Search it with your editor's
find command for tags such as `[DATABASE]`, `[BUG_FIX]`, or `[DOCUMENTATION]`.
The skill suggests tags from changed paths and can add project-specific tags.

Separate entries reduce contention, but timestamps have minute precision and
the same timestamp and slug can collide. Inspect an existing destination before
writing and choose a distinct slug for a different session. The shared
`changelog/README.md` and keyword file can also conflict. After reconciling entry
files in a merge, ask Claude to regenerate the index from all retained entries.

## Update or disable the plugin

Refresh the marketplace catalog and then update the installed user-scope plugin:

<!-- update-marketplace -->
```bash
claude plugin marketplace update changelog-plugin-marketplace
claude plugin update changelog@changelog-plugin-marketplace --scope user
```

Restart Claude Code and repeat the verification commands to check the enabled
state, version, and skill inventory. Updating the marketplace alone refreshes
its catalog; it is not the same as updating the installed plugin.

Temporarily disable and later re-enable a user-scope installation with:

<!-- toggle-marketplace -->
```bash
claude plugin disable changelog@changelog-plugin-marketplace --scope user
claude plugin enable changelog@changelog-plugin-marketplace --scope user
```

To uninstall it, use:

<!-- uninstall-marketplace -->
```bash
claude plugin uninstall changelog@changelog-plugin-marketplace --scope user
```

Restart the session after changes. These commands manage the plugin; they do
not remove committed project changelog files. For a manual copy, pull the source
clone and repeat the appropriate copy command to update it. Remove that copied
skill directory when you no longer want it loaded, preserving any local edits.

## Troubleshooting

- **Marketplace or plugin not found:** add the marketplace, refresh its catalog,
  and use the full `changelog@changelog-plugin-marketplace` identifier.
- **Copy reports a missing directory, or the skill is absent:** create the
  parent with `mkdir -p`, and check for `skills/commit/SKILL.md` at the chosen
  personal or project location. A file at `skills/SKILL.md` is one level too high.
- **Plugin is installed but the skill is unavailable:** inspect `plugin list`
  and `plugin details`, enable it in the intended scope, and start a new session.
  Use `/skills` to inspect available skills and `/changelog:commit` for the
  plugin's explicit command. Check for a duplicate personal or project copy.
- **No changes:** inspect `git status` in the target repository. The skill
  exits without creating a commit when there is no work.
- **Git rejects a commit:** fix the reported author identity, whitespace, or
  hook failure, then review and retry. Staging can remain after a failed check.

See [Claude Code plugin management](https://code.claude.com/docs/en/discover-plugins)
for other installation scopes and current commands.

## Plugin structure

The marketplace installs this repository root (`"source": "./"`). The root
`.claude-plugin/plugin.json` owns the plugin metadata and release version;
`skills/commit/SKILL.md` contains the skill. Keep the marketplace entry pointed
at the root so marketplace installation and direct plugin loading use the same
manifest. The marketplace entry only supplies the name, source and listing
summary. In Claude Code 2.1.318, the installed skill is listed as `commit`
(the directory name), and the plugin is displayed as Git Changelog. Conversational
activation still uses the description in `SKILL.md`.

The skill runs through Claude Code's tools: it reads Git changes and changelog
metadata, writes the new entry and index, then stages and commits the reviewed
files. Index generation searches titles, summaries and keywords in batches;
entries with unusual layouts get targeted reads. It still rebuilds the complete
index after edits or merges. There is no background hook or bundled generation
service.

## Contributing

Issues and PRs welcome at: https://github.com/justfinethanku/cc-changelog-plugin

Run the regression tests from the repository root with Git, Bash and Python 3:

```bash
python3 -m unittest discover -s tests -v
```

With the Claude Code CLI installed, the suite also validates the package and
installs it from a local marketplace in a temporary configuration directory. It
checks the loaded skill inventory without making model requests or changing your
installed plugins. Without the CLI, that integration test is skipped. Validate
the manifests directly from the repository root with:

```bash
claude plugin validate .
```

See the [Claude Code plugin manifest reference](https://code.claude.com/docs/en/plugins-reference)
for the standard layout and metadata fields.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Author

Jonathan Edwards
