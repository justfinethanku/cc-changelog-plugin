"""Exercise the skill's documented Git commands in disposable repositories."""

import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


SKILL = Path(__file__).resolve().parents[1] / "skills/commit/SKILL.md"


def command_block(name):
    match = re.search(r"<!-- " + re.escape(name) + r" -->\s*```bash\n(.*?)\n```",
                      SKILL.read_text(), re.S)
    if not match:
        raise AssertionError(f"Missing executable example: {name}")
    return match.group(1)


class CommitWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.sandbox = tempfile.TemporaryDirectory(prefix="changelog-commit-test-")
        self.addCleanup(self.sandbox.cleanup)
        self.root = Path(self.sandbox.name)
        # Ignore the caller's Git identity, index and hooks. Never touch a remote.
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                         "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
                         "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.invalid"})
        self.git("init", "-q")
        self.git("config", "core.hooksPath", str(self.root / "no-hooks"))
        self.write("app.txt", "before\n")
        self.git("add", "--", "app.txt")
        self.git("commit", "-qm", "initial")

    def run_command(self, args, check=True):
        return subprocess.run(args, cwd=self.root, env=self.env, capture_output=True,
                              text=True, check=check, timeout=15)

    def git(self, *args):
        return self.run_command(["git", *args]).stdout

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def scoped_commit(self, paths, message="Scoped change", check=True):
        # The paths and message enter Bash as arguments, never executable source.
        source = '\n'.join((
            'set -e', 'commit_message="$1"', 'shift', 'commit_paths=("$@")',
            command_block("scoped-stage"), command_block("scoped-commit")))
        return self.run_command(["bash", "-c", source, "scoped-test", message, *paths], check)

    def committed_paths(self):
        return set(self.git("diff-tree", "--no-commit-id", "--name-only", "-z", "-r", "HEAD")
                   .rstrip("\0").split("\0"))

    def test_local_only_and_unrelated_staged_files_stay_out(self):
        self.write("app.txt", "after\n")
        self.write("local-credentials.txt", "synthetic local-only marker\n")
        self.write("unrelated.txt", "someone else's staged change\n")
        self.git("add", "--", "unrelated.txt")
        index_before = self.git("ls-files", "--stage", "--", "unrelated.txt")
        self.write("changelog/entry.md", "# Entry\n")
        self.write("changelog/README.md", "# Index\n")
        self.write("changelog/private-notes.md", "private local-only marker\n")
        paths = ["app.txt", "changelog/entry.md", "changelog/README.md"]
        self.scoped_commit(paths)
        self.assertEqual(self.committed_paths(), set(paths))
        self.assertEqual(self.git("diff", "--cached", "--name-only").strip(), "unrelated.txt")
        self.assertEqual(self.git("ls-files", "--stage", "--", "unrelated.txt"), index_before)
        self.assertTrue((self.root / "local-credentials.txt").exists())
        self.assertTrue((self.root / "changelog/private-notes.md").exists())

    def test_filenames_and_message_are_literal_data(self):
        paths = ["file with spaces.txt", "[ab].txt", ":(glob)*.txt", "--all",
                 "$(touch PWNED).txt", "`touch PWNED2`.txt", "single'quote.txt",
                 "line\nbreak.txt"]
        for name in paths:
            self.write(name, "reviewed\n")
        self.write("a.txt", "not selected by [ab].txt\n")
        self.write("other.txt", "not selected by glob magic\n")
        message = "fix: $(touch MESSAGE_PWNED) `touch MESSAGE_PWNED2` 'quoted'\n\nDetails"
        self.scoped_commit(paths, message)
        self.assertEqual(self.committed_paths(), set(paths))
        self.assertEqual(self.git("log", "-1", "--format=%B").strip(), message)
        for name in ("PWNED", "PWNED2", "MESSAGE_PWNED", "MESSAGE_PWNED2"):
            self.assertFalse((self.root / name).exists())

    def test_tracked_deletion_is_included(self):
        (self.root / "app.txt").unlink()
        self.write("replacement.txt", "replacement\n")
        self.scoped_commit(["app.txt", "replacement.txt"])
        self.assertEqual(self.committed_paths(), {"app.txt", "replacement.txt"})
        self.assertNotIn("app.txt", self.git("ls-tree", "--name-only", "HEAD").splitlines())

    def test_commit_contains_reviewed_working_tree_contents(self):
        # The skill promises whole selected files, even if their index is older.
        self.write("app.txt", "intermediate staged revision\n")
        self.git("add", "--", "app.txt")
        final = "reviewed final revision\nUnicode: café 日本語\n"
        self.write("app.txt", final)
        entry = "# Document the final revision\n**Keywords:** [TESTING]\n"
        self.write("changelog/entry.md", entry)
        self.scoped_commit(["app.txt", "changelog/entry.md"])
        self.assertEqual(self.git("show", "HEAD:app.txt"), final)
        self.assertEqual(self.git("show", "HEAD:changelog/entry.md"), entry)
        self.assertEqual(self.git("diff", "HEAD", "--", "app.txt"), "")
        self.assertEqual(self.git("diff", "--cached", "--", "app.txt"), "")

    def test_already_staged_change_is_committed(self):
        final = "ready in the index\n"
        self.write("app.txt", final)
        self.git("add", "--", "app.txt")
        self.assertEqual(self.git("diff", "--", "app.txt"), "")
        self.scoped_commit(["app.txt"])
        self.assertEqual(self.git("show", "HEAD:app.txt"), final)
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_first_commit_creates_code_and_changelog(self):
        # An unborn HEAD must work too: first-time setup is a documented flow.
        self.root = self.root / "fresh-repository"
        self.root.mkdir()
        self.git("init", "-q")
        self.git("config", "core.hooksPath", str(self.root / "no-hooks"))
        files = {"app.txt": "first version\n",
                 "changelog/.changelog-keywords.txt": "[TESTING]\n",
                 "changelog/entry.md": "# First entry\n",
                 "changelog/README.md": "# Index\n"}
        for name, content in files.items():
            self.write(name, content)
        self.scoped_commit(list(files))
        self.assertEqual(self.git("rev-list", "--count", "HEAD").strip(), "1")
        self.assertEqual(set(self.git("ls-tree", "-r", "--name-only", "HEAD").splitlines()),
                         set(files))
        for name, content in files.items():
            self.assertEqual(self.git("show", f"HEAD:{name}"), content)
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_whitespace_check_failure_stops_before_commit(self):
        self.write("unrelated.txt", "already staged\n")
        self.git("add", "--", "unrelated.txt")
        index_before = self.git("ls-files", "--stage", "--", "unrelated.txt")
        before = self.git("rev-parse", "HEAD")
        invalid = "trailing whitespace   \n"
        self.write("app.txt", invalid)
        result = self.scoped_commit(["app.txt"], check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("trailing whitespace", result.stdout + result.stderr)
        self.assertEqual(self.git("rev-parse", "HEAD"), before)
        self.assertEqual(self.git("ls-files", "--stage", "--", "unrelated.txt"), index_before)
        # Staging happened before validation; it is not rolled back by this flow.
        self.assertEqual(self.git("show", ":app.txt"), invalid)
        self.assertEqual((self.root / "app.txt").read_text(), invalid)

    def test_rejecting_hook_preserves_head_index_and_work(self):
        self.write("unrelated.txt", "already staged\n")
        self.git("add", "--", "unrelated.txt")
        index_before = self.git("ls-files", "--stage", "--", "unrelated.txt")
        before = self.git("rev-parse", "HEAD")
        final = "reviewed but rejected\n"
        self.write("app.txt", final)
        self.write("no-hooks/pre-commit", "#!/bin/sh\necho synthetic-hook-rejection >&2\nexit 1\n")
        (self.root / "no-hooks/pre-commit").chmod(0o755)
        result = self.scoped_commit(["app.txt"], check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("synthetic-hook-rejection", result.stderr)
        self.assertEqual(self.git("rev-parse", "HEAD"), before)
        self.assertEqual(self.git("ls-files", "--stage", "--", "unrelated.txt"), index_before)
        self.assertEqual(self.git("show", ":app.txt"), final)
        self.assertEqual((self.root / "app.txt").read_text(), final)
        self.assertFalse((self.root / ".git/index.lock").exists())
        # Removing the synthetic rejection must leave the same work retryable.
        (self.root / "no-hooks/pre-commit").unlink()
        self.scoped_commit(["app.txt"])
        self.assertEqual(self.git("show", "HEAD:app.txt"), final)
        self.assertEqual(self.git("diff", "--cached", "--name-only").strip(), "unrelated.txt")

    def test_failed_staging_does_not_commit_unrelated_index(self):
        self.write("unrelated.txt", "already staged\n")
        self.git("add", "--", "unrelated.txt")
        before = self.git("rev-parse", "HEAD")
        result = self.scoped_commit(["missing.txt"], check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git("rev-parse", "HEAD"), before)
        self.assertEqual(self.git("diff", "--cached", "--name-only").strip(), "unrelated.txt")

    def test_empty_scope_does_not_commit_unrelated_index(self):
        self.write("unrelated.txt", "already staged\n")
        self.git("add", "--", "unrelated.txt")
        before = self.git("rev-parse", "HEAD")
        self.assertNotEqual(self.scoped_commit([], check=False).returncode, 0)
        self.assertEqual(self.git("rev-parse", "HEAD"), before)


if __name__ == "__main__":
    unittest.main()
