# Choose an installation method for Git Changelog

Git Changelog is a Claude Code plugin. It supplies instructions for Claude to
use the Git checkout and file tools available in your local session. It has no
Git hook, background service, bundled model, or separate package dependencies.

The [README installation guide](README.md#installation) is the maintained setup
procedure. The commands were checked with Claude Code 2.1.318 on Linux on
November 6, 2026. Installation and discovery were tested without model requests;
an authenticated, model-driven changelog session was not tested in that check.

## Marketplace plugin or copied skill

| Method | Installed content | How to maintain it |
| --- | --- | --- |
| Marketplace plugin | Plugin manifest and `skills/commit/SKILL.md` | Update the marketplace and plugin through Claude Code |
| Personal skill | A copy at `~/.claude/skills/commit/SKILL.md` | Pull the source repository and copy the skill again |
| Project skill | A copy at `.claude/skills/commit/SKILL.md` in your target repository | Pull and copy updates, then commit the project skill for collaborators |

Choose one method for a project to avoid loading duplicate instructions. The
marketplace identifier is `changelog@changelog-plugin-marketplace`. The manifest's
display name is Git Changelog. Its skill directory is `commit`; plugin skills use
a namespace, so the explicit command is `/changelog:commit`.

Personal and project skills are directory-based. Create the `skills` parent
directory before copying `commit` into it. A `SKILL.md` directly under
`.claude/skills/` is not the intended layout. The copy also does not register a
marketplace plugin, so `claude plugin list` is not a verification command for it.
Use `/skills` in a local Claude Code session to inspect copied skills.

For plugin authors, `.claude-plugin/marketplace.json` points `source` at `./` so
its package uses `.claude-plugin/plugin.json` and `skills/` together. Pointing
directly at `./skills/commit` bypasses the maintained plugin manifest. See the
[plugin manifest reference](https://code.claude.com/docs/en/plugins-reference)
and [skill locations and naming](https://code.claude.com/docs/en/skills).

## Other Claude surfaces

Choose by the session you are running, rather than the application window's
name. The Desktop app can host Claude Code and other modes with different
installation and execution environments. A local personal skill does not make
your local Git checkout available to a cloud session.

This repository does not supply or test a separate claude.ai, Cowork, or Claude
API package. Uploading a skill file does not provide the local Git tools and
checkout that this workflow expects. For those products, follow their current
environment and packaging instructions:

- [Claude Code plugin installation across surfaces](https://code.claude.com/docs/en/discover-plugins)
- [Skills in Cowork and cloud sessions](https://code.claude.com/docs/en/skills#use-skills-in-cowork-and-cloud-sessions)
- [Agent Skills with the Claude API](https://platform.claude.com/docs/en/build-with-claude/skills-guide)

The API guide describes skill upload/versioning and selection through
`container.skills`, with code execution in the API's container. It does not
install this repository into a local Claude Code session. This page links to
that maintained interface instead of providing an untested API example.
