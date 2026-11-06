# 2026-11-06 - Document verified installation and maintenance
**Keywords:** [BUG_FIX] [DOCUMENTATION] [PLUGIN] [TESTING]
**Session:** FLEET-533, Codex burn A, lane 6, docs pass 1

## What Changed
- Create the skills parent before manual copies, verify the resulting path, and
  distinguish the source clone from the target project directory.
- Document fully qualified marketplace commands, installed-state verification,
  updates, enable/disable, uninstall, prerequisites, and troubleshooting.
- Explain skill invocation, selected-file commits, first-use artifacts, and
  possible timestamp/index conflicts without promising a Git hook.
- Replace the old cross-product/API examples with a focused installation-method
  guide and current official references. Retain one setup procedure in README.

## Why
The old manual copy fails when `.claude/` is missing. With `.claude/` present but
no `skills/`, GNU cp succeeds while placing `SKILL.md` at `skills/SKILL.md`
instead of `skills/commit/SKILL.md`. The old guide also claimed all Desktop modes
used ZIP uploads and included unverified API calls unlike the current documented
`container.skills` interface.

## Dependencies
No runtime, manifest, or skill-instruction changes.

## Testing Notes
- Execute README setup and maintenance commands against the GitHub marketplace
  using Claude Code 2.1.318 with a temporary HOME/configuration and no model call.
- Verify the enabled plugin and one commit skill, catalog/plugin refresh,
  disabled/enabled states, and empty installed list after uninstall.
- Execute personal and project copies in fresh directories; compare skill bytes
  and repeat the personal copy with a neighbouring skill left intact.
- All 12 existing Git/package tests pass, including local CLI installation.
- Validate the Markdown and its local links/fragments.
- Interactive menus, copied-skill discovery in `/skills`, and an authenticated
  model-driven changelog session were not exercised. Official documentation
  supports those interface instructions; deterministic tests cover Git commands.

## Next Steps
Other audit dimensions continue through the existing FLEET-533 queue.
