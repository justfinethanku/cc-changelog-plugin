# 2026-11-06 - Use one plugin package and release manifest
**Keywords:** [CONFIGURATION] [PLUGIN] [REFACTOR] [TESTING]
**Session:** FLEET-533, Codex burn A, lane 7, architecture pass 1

## What Changed
- Point the marketplace source at the repository root so it loads the maintained
  plugin manifest and standard `skills/commit/` directory.
- Correct the manifest's repository URL type and bump its version to 1.0.2.
- Keep release metadata in that manifest; remove duplicate marketplace metadata.
- Correct two packaging examples and document package ownership and data flow.
- Add a package contract test and an optional real Claude CLI installation test.

## Why
Claude Code 2.1.318 rejected the root manifest's object-valued `repository`.
Marketplace installation still worked because its source selected the standalone
skill directory, bypassing that manifest. Root and marketplace loading now agree.
The installed skill is listed as `commit`; its instructions are unchanged.

## Issues Encountered
The original standalone layout is supported by the current CLI; it did load one
skill. This fixes divergent package roots and an invalid manifest, rather than
claiming that the original marketplace installation was entirely broken.

## Dependencies
No new dependencies. The integration test skips if Claude Code is not installed.

## Testing Notes
- Seven behavior/package tests pass with Claude Code 2.1.318, Git, Bash and Python.
- Disposable CLI configurations validate, install and list one enabled skill.
- Restoring the old source path or object-valued repository makes the new tests fail.
- No model requests, production changes or changes to installed user plugins.
- The CLI's catalog icon advisory is outside runtime validation and remains.

## Next Steps
Other audit dimensions continue through the existing FLEET-533 queue.
