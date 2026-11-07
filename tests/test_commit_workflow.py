"""Exercise the skill's documented Git commands in disposable repositories."""

import os
from pathlib import Path
import re
import selectors
import subprocess
import sys
import tempfile
import unittest


SKILL = Path(__file__).resolve().parents[1] / "skills/commit/SKILL.md"


def command_block(name):
    match = re.search(r"<!-- " + re.escape(name) + r" -->\s*```bash\n(.*?)\n```",
                      SKILL.read_text(), re.S)
    if not match:
        raise AssertionError(f"Missing executable example: {name}")
    return match.group(1)


class GitFixture(unittest.TestCase):
    def setUp(self):
        self.sandbox = tempfile.TemporaryDirectory(prefix="changelog-commit-test-")
        self.addCleanup(self.sandbox.cleanup)
        self.root = Path(self.sandbox.name)
        # Ignore the caller's Git identity, index and hooks. Never touch a remote.
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env["commit_helper"] = str(SKILL.parent / "scripts/workflow.py")
        self.env["review_state"] = str(self.root / "review-unused")
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
            command_block("scoped-stage"),
            command_block("scoped-review") if '<!-- scoped-review -->' in SKILL.read_text() else ':',
            command_block("scoped-commit")))
        return self.run_command(["bash", "-c", source, "scoped-test", message, *paths], check)

    def committed_paths(self):
        return set(self.git("diff-tree", "--no-commit-id", "--name-only", "-z", "-r", "HEAD")
                   .rstrip("\0").split("\0"))


class CommitWorkflowTests(GitFixture):
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

    def test_first_commit_preserves_an_unrelated_staged_file(self):
        self.root = self.root / "fresh-repository"
        self.root.mkdir()
        self.git("init", "-q")
        self.git("config", "core.hooksPath", str(self.root / "no-hooks"))
        self.write("unrelated.txt", "someone else's first staged file\n")
        self.git("add", "--", "unrelated.txt")
        unrelated = self.git("ls-files", "--stage", "--", "unrelated.txt")
        self.write("app.txt", "first version\n")
        self.write("changelog/entry.md", "# First operation\n")
        self.scoped_commit(["app.txt", "changelog/entry.md"])
        self.assertEqual(set(self.git("ls-tree", "-r", "--name-only", "HEAD").splitlines()),
                         {"app.txt", "changelog/entry.md"})
        self.assertEqual(self.git("ls-files", "--stage", "--", "unrelated.txt"), unrelated)
        self.assertEqual(self.git("diff", "--cached", "--name-only").strip(), "unrelated.txt")

    def test_unrelated_staged_deletion_survives_a_scoped_commit(self):
        self.write("other.txt", "keep in this commit\n")
        self.git("add", "--", "other.txt")
        self.git("commit", "-qm", "track another file")
        self.git("rm", "--", "other.txt")
        staged = self.git("diff", "--cached", "--raw")
        self.write("app.txt", "requested change\n")
        self.scoped_commit(["app.txt"])
        self.assertEqual(self.git("show", "HEAD:other.txt"), "keep in this commit\n")
        self.assertEqual(self.git("diff", "--cached", "--raw"), staged)
        self.assertFalse((self.root / "other.txt").exists())

    def test_identify_committed_operation_after_caller_failure_and_branch_advance(self):
        # Model lost caller output after Git succeeds, not a Git error return.
        # Recovery is model-driven: execute its history inspection in this fixture.
        entry = "changelog/entry.md"
        self.write("unrelated.txt", "staged by another owner\n")
        self.git("add", "--", "unrelated.txt")
        unrelated = self.git("ls-files", "--stage", "--", "unrelated.txt")
        base = self.git("rev-parse", "HEAD").strip()
        self.write("app.txt", "requested change\n")
        self.write(entry, "# Existing operation\n")
        source = '\n'.join(('set -e', 'commit_message="requested operation"',
                            'commit_paths=("app.txt" "changelog/entry.md")',
                            command_block("scoped-stage"), command_block("scoped-commit"),
                            'exit 70'))
        result = self.run_command(["bash", "-c", source], check=False)
        self.assertEqual(result.returncode, 70)
        committed = self.git("rev-parse", "HEAD").strip()
        self.assertNotEqual(committed, base)
        self.write("later.txt", "later operation\n")
        self.scoped_commit(["later.txt"])
        later_head = self.git("rev-parse", "HEAD").strip()
        index = self.git("ls-files", "--stage")

        candidate = self.git("--literal-pathspecs", "log", "--all", "-1", "--format=%H",
                             "--", entry).strip()
        self.assertEqual(candidate, committed)
        self.assertNotEqual(candidate, later_head)
        self.assertEqual(self.git("rev-parse", candidate + "^1").strip(), base)
        self.assertEqual(self.git("show", "-s", "--format=%s", candidate).strip(),
                         "requested operation")
        self.assertEqual(self.git("show", candidate + ":" + entry), "# Existing operation\n")
        paths = self.git("diff-tree", "--no-commit-id", "--name-only", "-r", candidate)
        self.assertEqual(set(paths.splitlines()), {"app.txt", entry})
        # Inspect and record this SHA; no replacement generation or commit.
        self.assertEqual(self.git("rev-list", "--count", "HEAD").strip(), "3")
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), later_head)
        self.assertEqual(self.git("ls-files", "--stage"), index)
        self.assertEqual(self.git("ls-files", "--stage", "--", "unrelated.txt"), unrelated)
        self.assertEqual(list((self.root / "changelog").glob("*.md")), [self.root / entry])

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

    def test_live_index_lock_preserves_partial_index_and_allows_same_entry_retry(self):
        self.write("other.txt", "original\n")
        self.scoped_commit(["other.txt"])
        self.write("other.txt", "someone else's staged revision\n")
        self.git("add", "--", "other.txt")
        self.write("other.txt", "someone else's later working revision\n")
        unrelated = self.git("ls-files", "--stage", "--", "other.txt")
        entry = "changelog/entry.md"

        for phase in ("stage", "commit"):
            with self.subTest(phase=phase):
                self.write("app.txt", f"requested {phase} change\n")
                self.write(entry, f"# Same operation after {phase} rejection\n")
                setup = 'commit_paths=("app.txt" "changelog/entry.md")\ncommit_message="retry"\n'
                if phase == "commit":
                    self.run_command(["bash", "-c", setup + command_block("scoped-stage") +
                                      '\nprintf "%s" "$review_state" > saved-review-state'])
                    setup += 'review_state=$(cat saved-review-state)\n'
                before = self.git("rev-parse", "HEAD")
                index = self.git("ls-files", "--stage")
                # A separate live process owns a synthetic lock until released.
                # Avoid sleeps/races: it signals after exclusive creation.
                lock = self.root / ".git/index.lock"
                owner_code = (
                    "import pathlib,sys\n"
                    "p=pathlib.Path(sys.argv[1])\n"
                    "with p.open('xb') as f: f.write(b'other-operation-lock')\n"
                    "print('ready', flush=True)\n"
                    "try: sys.stdin.read()\n"
                    "finally: p.unlink(missing_ok=True)\n"
                )
                with subprocess.Popen([sys.executable, "-c", owner_code, str(lock)],
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True) as owner:
                    try:
                        with selectors.DefaultSelector() as ready:
                            ready.register(owner.stdout, selectors.EVENT_READ)
                            self.assertTrue(ready.select(timeout=5), "Lock owner did not start")
                            self.assertEqual(owner.stdout.readline().strip(), "ready")
                        result = self.run_command([
                            "bash", "-c", setup + command_block("scoped-" + phase)
                        ], check=False)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn("index.lock", result.stderr)
                        self.assertIsNone(owner.poll())
                        self.assertEqual(lock.read_bytes(), b"other-operation-lock")
                        self.assertEqual(self.git("rev-parse", "HEAD"), before)
                        self.assertEqual(self.git("ls-files", "--stage"), index)
                    finally:
                        owner.communicate(input="", timeout=5)
                self.assertEqual(owner.returncode, 0)
                self.assertFalse(lock.exists())
                self.scoped_commit(["app.txt", entry])
                self.assertEqual(self.git("show", "HEAD:app.txt"), f"requested {phase} change\n")
                self.assertEqual(self.git("ls-files", "--stage", "--", "other.txt"), unrelated)
                self.assertEqual((self.root / "other.txt").read_text(),
                                 "someone else's later working revision\n")
                self.assertEqual(list((self.root / "changelog").glob("*.md")),
                                 [self.root / entry])


if __name__ == "__main__":
    unittest.main()
