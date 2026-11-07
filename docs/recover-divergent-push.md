# Recover a divergent changelog push

Use this procedure when a saved changelog commit is rejected because the remote
branch advanced. It reconciles committed entries in a separate worktree while
leaving the original worktree's HEAD, staged changes and working files intact.
It does not restore an entry overwritten before it was committed or serialize
concurrent generators.

## Prepare the recovery

You need Git, Bash, the saved full `reviewed_commit` SHA and `reviewed_branch`
from [scoped push and recovery](../skills/commit/SKILL.md#scoped-push-and-recovery),
and access to the intended remote. Follow the repository's PR and release rules;
a rejected push does not authorize bypassing them. Do not regenerate the session
entry, reset the original index or force-push the rejected commit.

Run the examples step by step in one Bash session, starting at the original
repository root. Stop when a command fails, except for the expected merge
conflict described below. Keep the saved values and recovery path in your task
record so a new session can resume them.

1. Inspect the original state and the configured fetch and push destinations:

   <!-- recovery-inspect -->
   ```bash
   git status --short
   git show --stat --oneline "$reviewed_commit"
   git remote get-url --all origin
   git remote get-url --push --all origin
   ```

   This example assumes one fetch URL and one push URL pointing at the same
   repository. If they differ or there are multiple push destinations, inspect
   the actual destination before continuing; the fetch below would otherwise
   inspect the wrong history. Keep private remote URLs out of public reports.

2. Fetch the destination branch and record its observed tip:

   <!-- recovery-fetch -->
   ```bash
   git check-ref-format "refs/heads/$reviewed_branch" &&
   git cat-file -e "${reviewed_commit}^{commit}" &&
   git fetch --no-tags origin "refs/heads/$reviewed_branch" &&
   remote_tip=$(git rev-parse FETCH_HEAD)
   ```

   If fetching fails, retain the local commit and correct the transport or
   destination problem first. Check whether the remote already contains it:

   <!-- recovery-contained -->
   ```bash
   git merge-base --is-ancestor "$reviewed_commit" "$remote_tip"
   ```

   Exit 0 means the commit was published, even if later remote commits make the
   tip different. Finish this push operation without another entry or commit.
   Exit 1 means it is not an ancestor; other nonzero results are errors to
   investigate. Inspect divergence with
   `git log --left-right --oneline "$reviewed_commit...$remote_tip"`.

## Reconcile the histories

Continue only after confirming both histories belong on the destination branch
and that a merge is allowed by its contribution policy.

1. Set `recovery_dir` to an absolute, nonexistent sibling directory outside the
   original worktree, for example `/PATH/TO/project-push-recovery`. Use the saved
   commit, even if the original local branch has since advanced:

   <!-- recovery-worktree -->
   ```bash
   git worktree add --detach "$recovery_dir" "$reviewed_commit"
   cd "$recovery_dir"
   ```

   This worktree has its own HEAD, files and index. Git configuration, objects
   and refs remain shared. If resuming an existing recovery worktree, inspect
   its status and history instead of creating it again.

2. Start the merge and inspect its result:

   <!-- recovery-merge -->
   ```bash
   git merge --no-commit --no-ff "$remote_tip"
   ```

   A conflicting merge returns nonzero. Run `git status` and inspect
   `git rev-parse --verify MERGE_HEAD` to confirm that a merge is in progress;
   an unrelated error is not permission to proceed. A successful merge also
   pauses before committing because of `--no-commit --no-ff`.

3. Resolve conflicts in this recovery worktree. Retain both sessions' entries
   and intended code. For distinct entries with a conflicting index, rebuild
   `changelog/README.md` from **all retained entry files**, following
   [index metadata collection](../skills/commit/SKILL.md#collect-index-metadata).
   Reconcile the keyword vocabulary too if it changed. An ours/theirs choice
   for the index alone can silently omit the other session's entry. If the same
   entry path has different contents, inspect both versions and reconcile them
   deliberately; the filename is not proof of duplicate content.

4. Stage each resolved path explicitly. For an index-only conflict:

   <!-- recovery-resolve-index -->
   ```bash
   git --literal-pathspecs add -- changelog/README.md
   git diff --name-only --diff-filter=U
   git diff --cached --check
   git diff --cached
   ```

   The unresolved-file list must be empty and the check must pass. Review the
   entire staged merge, including automatically merged paths. Run the project's
   relevant checks. Retain this worktree if resolution is incomplete. To abandon
   this attempt, `git merge --abort` belongs in this dedicated recovery worktree;
   it does not undo the original local commit or a remote push.

5. Commit the reviewed merge in the recovery worktree:

   <!-- recovery-commit -->
   ```bash
   git commit -m 'Merge remote changelog work before publishing'
   reviewed_commit=$(git rev-parse HEAD)
   git show --stat --oneline "$reviewed_commit"
   ```

   Use a normal merge commit here: the skill's scoped snapshot procedure
   cannot complete an in-progress merge. This new SHA replaces the old saved
   push source only after you review its contents and outgoing history.

6. Follow [scoped push and recovery](../skills/commit/SKILL.md#scoped-push-and-recovery)
   with the reconciled SHA and original destination, including renewed review
   and push authorization or the required PR path. If the remote advances again,
   fetch and reassess; do not force the old snapshot. If success output is lost,
   repeat the fetch and ancestor check before doing more work.

Return to the original worktree and inspect `git status` and HEAD. Its local
branch can still differ from the remote: publishing the recovery commit does not
move that branch or consume its staged changes. Keep the recovery path and SHA
until publication is verified; do not automatically reset or merge the original
dirty worktree to make it match.

## Verification and references

Checked with Git 2.43.0 on Linux, November 6, 2026, using disposable local bare
remotes: divergent sessions, an index conflict, a later original local commit,
partially staged unrelated work, merge abort/resume and lost push acknowledgement.
Entry/index reconciliation was performed explicitly; no Claude model invocation
or automatic conflict resolver was tested.

See Git's [worktree documentation](https://git-scm.com/docs/git-worktree),
[merge documentation](https://git-scm.com/docs/git-merge), and
[push documentation](https://git-scm.com/docs/git-push) for command semantics.
