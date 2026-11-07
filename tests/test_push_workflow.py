"""Execute the documented push procedure against disposable local bare remotes."""

from pathlib import Path
import shutil
import unittest

if __package__:
    from .test_commit_workflow import GitFixture, command_block
else:
    from test_commit_workflow import GitFixture, command_block


def available_shells():
    """Test system shells, Homebrew Bash, and a distinct Bash on PATH."""
    candidates = [("system_bash", "/bin/bash"), ("system_zsh", "/bin/zsh"),
                  ("homebrew_bash", "/opt/homebrew/bin/bash"),
                  ("homebrew_intel_bash", "/usr/local/bin/bash"),
                  ("path_bash", shutil.which("bash"))]
    seen = set()
    for name, path in candidates:
        if path and Path(path).is_file() and Path(path).resolve() not in seen:
            seen.add(Path(path).resolve())
            yield name, path


class PushWorkflowTests(GitFixture):
    shell = "/bin/bash"

    def setUp(self):
        super().setUp()
        self.branch = "reviewed-destination"
        self.remote = self.root / "remote.git"
        self.git("init", "--bare", "-q", str(self.remote))
        self.git("remote", "add", "origin", str(self.remote))
        self.initial = self.git("rev-parse", "HEAD").strip()
        self.git("push", "origin", f"HEAD:refs/heads/{self.branch}")
        self.write("app.txt", "reviewed change\n")
        self.scoped_commit(["app.txt"])
        self.reviewed = self.git("rev-parse", "HEAD").strip()

    def push_reviewed(self, commit=None, branch=None, check=True, conditional=False):
        block = command_block("scoped-push")
        if conditional:
            # Model a caller checking success: errexit is ignored in this context.
            block = "if " + block + "\nthen exit 0; else exit 1; fi"
        source = '\n'.join(('reviewed_commit="$1"', 'reviewed_branch="$2"', block))
        return self.run_command([self.shell, "-c", source, "push-test",
                                 self.reviewed if commit is None else commit,
                                 self.branch if branch is None else branch], check)

    def remote_git(self, *args):
        return self.git("--git-dir", str(self.remote), *args).strip()

    def later_commit(self):
        self.write("private-later.txt", "synthetic unreviewed marker\n")
        self.scoped_commit(["private-later.txt"])
        return self.git("rev-parse", "HEAD").strip()

    def test_branch_advance_does_not_expand_reviewed_push(self):
        later = self.later_commit()
        self.write("unrelated.txt", "staged by another owner\n")
        self.git("add", "--", "unrelated.txt")
        index = self.git("ls-files", "--stage")
        self.push_reviewed()
        self.assertEqual(self.remote_git("rev-parse", self.branch), self.reviewed)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), later)
        self.assertEqual(self.git("ls-files", "--stage"), index)
        self.assertNotIn("private-later.txt", self.remote_git("ls-tree", "--name-only", self.branch))

    def test_rejected_push_retries_same_commit_after_head_moves(self):
        hook = self.remote / "hooks/pre-receive"
        hook.write_text("#!/bin/sh\necho synthetic-remote-rejection >&2\nexit 1\n")
        hook.chmod(0o755)
        before = self.git("rev-list", "--count", "HEAD")
        result = self.push_reviewed(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("synthetic-remote-rejection", result.stderr)
        self.assertEqual(self.remote_git("rev-parse", self.branch), self.initial)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.reviewed)
        self.assertEqual(self.git("rev-list", "--count", "HEAD"), before)
        hook.unlink()
        later = self.later_commit()
        self.push_reviewed()
        self.push_reviewed()  # Lost success acknowledgement: retry is idempotent.
        self.assertEqual(self.remote_git("rev-parse", self.branch), self.reviewed)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), later)

    def test_remote_advance_is_not_overwritten(self):
        later = self.later_commit()
        self.git("push", "origin", f"{later}:refs/heads/{self.branch}")
        result = self.push_reviewed(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.remote_git("rev-parse", self.branch), later)

    def test_configured_tags_mirror_and_ref_mapping_do_not_expand_scope(self):
        self.git("tag", "-am", "private annotation", "private-tag", self.reviewed)
        self.git("branch", "private-branch", self.reviewed)
        self.git("config", "push.followTags", "true")
        self.git("config", "remote.origin.mirror", "true")
        self.git("config", "remote.origin.push", "refs/heads/*:refs/heads/*")
        self.push_reviewed()
        self.assertEqual(self.remote_git("for-each-ref", "--format=%(refname)"),
                         f"refs/heads/{self.branch}")
        self.assertEqual(self.remote_git("rev-parse", self.branch), self.reviewed)

    def test_saved_destination_survives_checkout_change_and_detached_head(self):
        self.git("checkout", "-q", "--detach", self.initial)
        self.push_reviewed()
        self.assertEqual(self.remote_git("rev-parse", self.branch), self.reviewed)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.initial)

    def assert_invalid_inputs_refused(self, conditional=False):
        blob = self.git("rev-parse", "HEAD:app.txt").strip()
        cases = (("", self.branch), ("HEAD", self.branch), ("0" * 40, self.branch),
                 (self.reviewed, ""), (self.reviewed, "bad:refs/heads/other"),
                 (self.reviewed, "*"), (self.reviewed[:12], self.branch),
                 ("f" * 39, self.branch), ("f" * 41, self.branch),
                 ("f" * 63, self.branch), ("f" * 65, self.branch),
                 ("g" * 40, self.branch), ("0" * 64, self.branch),
                 (blob, self.branch))
        for number, (commit, branch) in enumerate(cases):
            with self.subTest(commit=commit, branch=branch):
                # Isolate cases: a bad push must not cause cascading failures.
                self.remote = self.root / f"invalid-{number}.git"
                self.git("init", "--bare", "-q", str(self.remote))
                self.git("remote", "set-url", "origin", str(self.remote))
                self.git("push", "origin", f"{self.initial}:refs/heads/{self.branch}")
                before = self.remote_git("for-each-ref", "--format=%(refname) %(objectname)")
                result = self.push_reviewed(commit, branch, check=False, conditional=conditional)
                # Check every ref even if the block incorrectly reports success.
                self.assertEqual(self.remote_git("for-each-ref", "--format=%(refname) %(objectname)"),
                                 before, result.stdout + result.stderr)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_invalid_snapshot_or_destination_cannot_delete_or_expand_refs(self):
        self.assert_invalid_inputs_refused()

    def test_invalid_inputs_refused_when_caller_checks_status(self):
        self.assert_invalid_inputs_refused(conditional=True)

    def test_local_push_hook_rejection_preserves_partial_index_and_retry_snapshot(self):
        self.write("other.txt", "tracked original\n")
        self.scoped_commit(["other.txt"])
        later = self.git("rev-parse", "HEAD").strip()
        self.write("other.txt", "staged revision\n")
        self.git("add", "--", "other.txt")
        self.write("other.txt", "later unstaged revision\n")
        self.write("local-only.txt", "untracked revision\n")
        index = self.git("ls-files", "--stage")
        status = self.git("status", "--porcelain")
        count = self.git("rev-list", "--count", "HEAD")
        hook = self.root / "no-hooks/pre-push"
        self.write("no-hooks/pre-push", "#!/bin/sh\n"
                   "printf '%s\\n' \"$@\" > .git/pre-push-args\n"
                   "cat > .git/pre-push-input\n"
                   "echo synthetic-local-push-rejection >&2\nexit 1\n")
        hook.chmod(0o755)
        rejected = self.push_reviewed(check=False)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("synthetic-local-push-rejection", rejected.stderr)
        self.assertEqual((self.root / ".git/pre-push-args").read_text().splitlines(),
                         ["origin", str(self.remote)])
        self.assertEqual((self.root / ".git/pre-push-input").read_text().split(),
                         [self.reviewed, self.reviewed, f"refs/heads/{self.branch}", self.initial])
        self.assertEqual(self.remote_git("rev-parse", self.branch), self.initial)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), later)
        self.assertEqual(self.git("ls-files", "--stage"), index)

        hook.unlink()  # Correct only the synthetic hook failure, then retry.
        self.push_reviewed()
        self.push_reviewed()
        self.assertEqual(self.remote_git("rev-parse", self.branch), self.reviewed)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), later)
        self.assertEqual(self.git("rev-list", "--count", "HEAD"), count)
        self.assertEqual(self.git("ls-files", "--stage"), index)
        self.assertEqual(self.git("status", "--porcelain"), status)
        self.assertEqual((self.root / "other.txt").read_text(), "later unstaged revision\n")
        self.assertEqual((self.root / "local-only.txt").read_text(), "untracked revision\n")


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for name, shell in available_shells():
        case = type("PushWorkflowTests_" + name, (PushWorkflowTests,), {"shell": shell})
        suite.addTests(loader.loadTestsFromTestCase(case))
    return suite
