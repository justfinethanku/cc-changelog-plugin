"""Execute the documented push procedure against disposable local bare remotes."""

from test_commit_workflow import GitFixture, command_block


class PushWorkflowTests(GitFixture):
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

    def push_reviewed(self, commit=None, branch=None, check=True):
        source = '\n'.join(('reviewed_commit="$1"', 'reviewed_branch="$2"',
                            command_block("scoped-push")))
        return self.run_command(["bash", "-c", source, "push-test",
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

    def test_invalid_snapshot_or_destination_cannot_delete_or_expand_refs(self):
        for commit, branch in (("", self.branch), ("HEAD", self.branch),
                               ("0" * 40, self.branch), (self.reviewed, ""),
                               (self.reviewed, "bad:refs/heads/other"),
                               (self.reviewed, "*")):
            with self.subTest(commit=commit, branch=branch):
                self.assertNotEqual(self.push_reviewed(commit, branch, check=False).returncode, 0)
                self.assertEqual(self.remote_git("rev-parse", self.branch), self.initial)
