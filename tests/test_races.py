"""Execute documented shell blocks with controlled concurrent processes."""

import os
from pathlib import Path
import selectors
import signal
import subprocess
import unittest

from test_commit_workflow import GitFixture, SKILL, command_block


class RaceTests(GitFixture):
    def setup_owner_work(self):
        self.write('other.txt', 'other staged\n')
        self.git('add', '--', 'other.txt')
        self.write('other.txt', 'other later working edit\n')
        return self.git('ls-files', '--stage', '--', 'other.txt')

    def start_review(self):
        self.write('app.txt', 'reviewed\n')
        # Persist the shell variable to model separate tool calls.
        source = ('set -e\ncommit_paths=(app.txt)\n' + command_block('scoped-stage') +
                  '\nprintf "%s" "$review_state" > review-path')
        self.run_command(['bash', '-c', source])
        self.env['review_state'] = (self.root / 'review-path').read_text()
        reviewed = self.run_command(['bash', '-c', command_block('scoped-review')])
        self.assertIn('+reviewed', reviewed.stdout)

    def finish_review(self, check=True):
        source = 'commit_paths=(app.txt)\ncommit_message="reviewed commit"\n' + command_block('scoped-commit')
        return self.run_command(['bash', '-c', source], check=check)

    def test_post_review_edit_is_not_committed(self):
        other = self.setup_owner_work()
        self.start_review()
        self.write('app.txt', 'later unreviewed edit\n')
        self.finish_review()
        self.assertEqual(self.git('show', 'HEAD:app.txt'), 'reviewed\n')
        self.assertEqual((self.root / 'app.txt').read_text(), 'later unreviewed edit\n')
        self.assertEqual(self.git('ls-files', '--stage', '--', 'other.txt'), other)
        self.assertEqual((self.root / 'other.txt').read_text(), 'other later working edit\n')

    def test_hook_working_edit_cannot_race_snapshot_commit(self):
        self.start_review()
        self.write('no-hooks/pre-commit', '#!/bin/sh\nprintf "hook later edit\\n" > app.txt\n')
        (self.root / 'no-hooks/pre-commit').chmod(0o755)
        self.finish_review()
        self.assertEqual(self.git('show', 'HEAD:app.txt'), 'reviewed\n')
        self.assertEqual((self.root / 'app.txt').read_text(), 'hook later edit\n')

    def test_hook_staging_changes_requires_review(self):
        self.start_review()
        self.write('no-hooks/pre-commit', '#!/bin/sh\nprintf "hook later edit\\n" > app.txt\ngit add -- app.txt\n')
        (self.root / 'no-hooks/pre-commit').chmod(0o755)
        before = self.git('rev-parse', 'HEAD')
        index = self.git('ls-files', '--stage')
        result = self.finish_review(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('hook changed the commit', result.stderr)
        self.assertIn('+hook later edit', result.stdout)
        self.assertNotEqual(self.git('rev-parse', 'HEAD'), before)
        self.assertEqual(self.git('show', 'HEAD:app.txt'), 'hook later edit\n')
        self.assertEqual(self.git('ls-files', '--stage'), index)

    def test_head_advance_requires_new_review(self):
        self.start_review()
        self.write('later.txt', 'a separate commit\n')
        self.scoped_commit(['later.txt'])
        before = self.git('rev-parse', 'HEAD')
        index = self.git('ls-files', '--stage')
        self.assertNotEqual(self.finish_review(check=False).returncode, 0)
        self.assertEqual(self.git('rev-parse', 'HEAD'), before)
        self.assertEqual(self.git('ls-files', '--stage'), index)

    def test_rejection_and_retry_preserve_later_edits_and_staging(self):
        other = self.setup_owner_work()
        self.start_review()
        self.write('app.txt', 'later staged revision\n')
        self.git('add', '--', 'app.txt')
        later_staged = self.git('ls-files', '--stage', '--', 'app.txt')
        self.write('app.txt', 'still later working edit\n')
        self.write('no-hooks/pre-commit', '#!/bin/sh\necho rejection >&2\nexit 1\n')
        (self.root / 'no-hooks/pre-commit').chmod(0o755)
        before = self.git('rev-parse', 'HEAD')
        self.assertNotEqual(self.finish_review(check=False).returncode, 0)
        self.assertEqual(self.git('rev-parse', 'HEAD'), before)
        self.assertEqual(self.git('ls-files', '--stage', '--', 'app.txt'), later_staged)
        (self.root / 'no-hooks/pre-commit').unlink()
        # Retry the SAME reviewed state, without staging the newer contents.
        self.finish_review()
        self.assertEqual(self.git('show', 'HEAD:app.txt'), 'reviewed\n')
        self.assertEqual(self.git('ls-files', '--stage', '--', 'app.txt'), later_staged)
        self.assertEqual(self.git('ls-files', '--stage', '--', 'other.txt'), other)
        self.assertEqual((self.root / 'app.txt').read_text(), 'still later working edit\n')

    def test_rejecting_hook_that_stages_cannot_change_a_retry_silently(self):
        self.start_review()
        self.write('no-hooks/pre-commit', '#!/bin/sh\nprintf "unreviewed\\n" > app.txt\ngit add app.txt\nexit 1\n')
        (self.root / 'no-hooks/pre-commit').chmod(0o755)
        before = self.git('rev-parse', 'HEAD')
        self.assertNotEqual(self.finish_review(check=False).returncode, 0)
        (self.root / 'no-hooks/pre-commit').unlink()
        retry = self.finish_review(check=False)
        self.assertNotEqual(retry.returncode, 0)
        self.assertIn('Private index changed', retry.stderr)
        self.assertEqual(self.git('rev-parse', 'HEAD'), before)
        self.assertEqual(self.git('show', ':app.txt'), 'reviewed\n')
        self.assertEqual((self.root / 'app.txt').read_text(), 'unreviewed\n')

    def test_concurrent_commit_during_hook_is_refused_by_git(self):
        other = self.setup_owner_work()
        self.start_review()
        before = self.git('rev-parse', 'HEAD')
        self.write('no-hooks/pre-commit', '#!/bin/sh\nif test "${PAUSE_COMMIT:-}" = yes; then\n'
                   '  echo COMMIT_READY >&2\n  read -r release < .git/commit-release\nfi\n')
        (self.root / 'no-hooks/pre-commit').chmod(0o755)
        os.mkfifo(self.root / '.git/commit-release')
        source = 'commit_message="reviewed commit"\n' + command_block('scoped-commit')
        with subprocess.Popen(['bash', '-c', source], cwd=self.root,
                              env=dict(self.env, PAUSE_COMMIT='yes'),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as child:
            try:
                with selectors.DefaultSelector() as ready:
                    ready.register(child.stderr, selectors.EVENT_READ)
                    self.assertTrue(ready.select(timeout=5), 'commit did not reach hook')
                    self.assertEqual(child.stderr.readline().strip(), 'COMMIT_READY')
                self.write('later.txt', 'other commit\n')
                self.scoped_commit(['later.txt'])
                concurrent = self.git('rev-parse', 'HEAD')
                self.assertNotEqual(concurrent, before)
            finally:
                with (self.root / '.git/commit-release').open('w') as release:
                    release.write('release\n')
                out, err = child.communicate(timeout=5)
        self.assertNotEqual(child.returncode, 0, out + err)
        self.assertIn('cannot lock ref', err)
        self.assertEqual(self.git('rev-parse', 'HEAD'), concurrent)
        self.assertEqual(self.git('show', 'HEAD:app.txt'), 'before\n')
        self.assertEqual(self.git('show', ':app.txt'), 'reviewed\n')
        self.assertEqual((self.root / 'app.txt').read_text(), 'reviewed\n')
        self.assertEqual(self.git('ls-files', '--stage', '--', 'other.txt'), other)

    def test_success_records_sha_and_removes_private_review(self):
        self.start_review()
        state = self.root / self.env['review_state']
        result = self.finish_review()
        self.assertIn('Recorded commit: ' + self.git('rev-parse', 'HEAD').strip(), result.stdout)
        self.assertFalse(state.exists())
        self.assertEqual(self.git('status', '--porcelain', '--', 'app.txt'), '')


class GenerationTests(GitFixture):
    name = '2026-11-06-1700-fix.md'

    def setUp(self):
        super().setUp()
        self.env.update(entry_name=self.name, entry_draft='draft', index_draft='index-draft')
        self.write('draft', '# New entry\n')

    def block(self, name, *, check=True, env=None, cwd=None):
        return subprocess.run(['bash', '-ec', command_block(name)], cwd=cwd or self.root,
                              env=env or self.env, capture_output=True, text=True,
                              check=check, timeout=10)

    def draft_index(self):
        # A deterministic stand-in for the model's complete private draft.
        names = sorted(p.name for p in (self.root / 'changelog').glob('*.md')
                       if p.name != 'README.md')
        self.write('index-draft', '# Project index\n\nCustom introduction.\n\n' +
                   '\n'.join(names) + '\n')
        return (self.root / 'index-draft').read_text()

    def test_identical_minute_and_slug_keep_both_entries(self):
        a = self.block('changelog-generate')
        self.write('draft', '# Writer B\n')
        b = self.block('changelog-generate')
        self.assertEqual(a.stdout.strip(), 'changelog/' + self.name)
        second = self.name.replace('.md', '-1.md')
        self.assertEqual(b.stdout.strip(), 'changelog/' + second)
        self.assertEqual((self.root / 'changelog' / self.name).read_text(), '# New entry\n')
        self.assertEqual((self.root / 'changelog' / second).read_text(), '# Writer B\n')
        expected = self.draft_index()
        self.block('changelog-rebuild')
        self.assertEqual((self.root / 'changelog/README.md').read_text(), expected)

    def test_stale_model_index_is_refused_then_complete_rebuild_succeeds(self):
        self.block('changelog-generate')
        self.draft_index()
        self.block('changelog-rebuild')
        old = (self.root / 'changelog/README.md').read_bytes()
        self.block('changelog-generate')
        rejected = self.block('changelog-rebuild', check=False)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn(self.name.replace('.md', '-1.md'), rejected.stderr)
        self.assertIn('rebuild the complete draft', rejected.stderr)
        self.assertEqual((self.root / 'changelog/README.md').read_bytes(), old)
        expected = self.draft_index()
        self.block('changelog-rebuild')
        self.assertEqual((self.root / 'changelog/README.md').read_text(), expected)

    def test_project_layout_is_preserved_byte_for_byte(self):
        source = SKILL.parents[2] / 'changelog'
        for path in source.glob('*.md'):
            self.write('changelog/' + path.name, path.read_text())
        original = (source / 'README.md').read_bytes()
        for expected in (original, original.replace(b'\n', b'\r\n')):
            with self.subTest(crlf=b'\r\n' in expected):
                (self.root / 'index-draft').write_bytes(expected)
                self.block('changelog-rebuild')
                self.assertEqual((self.root / 'changelog/README.md').read_bytes(), expected)

    def test_amendment_then_model_rebuild_preserves_permissions(self):
        self.block('changelog-generate')
        self.write('draft', '# Explicit amendment\n')
        self.run_command(['bash', '-ec', 'umask 077\n' + command_block('changelog-amend')])
        self.assertEqual((self.root / 'changelog' / self.name).read_text(), '# Explicit amendment\n')
        self.draft_index()
        self.run_command(['bash', '-ec', 'umask 077\n' + command_block('changelog-rebuild')])
        for path in (self.root / 'changelog' / self.name, self.root / 'changelog/README.md'):
            self.assertEqual(path.stat().st_mode & 0o777, 0o644)

    def test_subdirectory_commands_use_repo_root_and_no_worktree_lock(self):
        self.write('nested/deep/placeholder', '')
        env = dict(self.env, entry_draft=str(self.root / 'draft'),
                   index_draft=str(self.root / 'index-draft'))
        cwd = self.root / 'nested/deep'
        self.block('changelog-generate', cwd=cwd, env=env)
        self.draft_index()
        self.block('changelog-rebuild', cwd=cwd, env=env)
        self.assertTrue((self.root / '.git/changelog.lock').is_file())
        self.assertFalse((self.root / 'changelog/.write.lock').exists())
        self.assertFalse((cwd / 'changelog').exists())

    def instrument(self):
        # Pause real helper operations without modifying its production code.
        self.write('instrument/sitecustomize.py', '''import fcntl, os, sys
real_flock, real_replace, real_open = fcntl.flock, os.replace, os.open
def flock(fd, mode):
    print('LOCK_ATTEMPT', flush=True)
    result = real_flock(fd, mode)
    print('LOCK_ACQUIRED', flush=True)
    return result
def replace(src, dst, *args, **kwargs):
    if str(dst).endswith('README.md') and os.environ.get('PAUSE_INDEX') == 'yes':
        print('INDEX_READY', flush=True)
        sys.stdin.readline()
    return real_replace(src, dst, *args, **kwargs)
def opened(path, flags, *args, **kwargs):
    fd = real_open(path, flags, *args, **kwargs)
    if os.environ.get('PAUSE_ALLOC') == 'yes' and flags & os.O_EXCL and str(path).endswith('.md'):
        print('ALLOCATED', flush=True)
        sys.stdin.readline()
    return fd
fcntl.flock, os.replace, os.open = flock, replace, opened
''')
        return dict(self.env, PYTHONPATH=str(self.root / 'instrument'))

    def spawn(self, block, env, cwd=None):
        child = subprocess.Popen(['bash', '-ec', command_block(block)], cwd=cwd or self.root, env=env,
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True, bufsize=1, start_new_session=True)
        self.addCleanup(self.stop_child, child)
        return child

    @staticmethod
    def stop_child(child):
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGKILL)
        child.communicate(timeout=5)

    def line(self, child, expected):
        pending = getattr(child, '_pending', b'')
        while b'\n' not in pending:
            with selectors.DefaultSelector() as ready:
                ready.register(child.stdout, selectors.EVENT_READ)
                self.assertTrue(ready.select(timeout=5), 'helper protocol timed out')
            chunk = os.read(child.stdout.fileno(), 4096)
            self.assertTrue(chunk, 'helper exited before protocol response')
            pending += chunk
        line, child._pending = pending.split(b'\n', 1)
        self.assertEqual(line.decode(), expected)

    def finish(self, child, release=False):
        out, err = child.communicate(input='release\n' if release else None, timeout=5)
        self.assertEqual(child.returncode, 0, out + err)
        return out

    def test_concurrent_identical_minute_and_slug_get_suffix(self):
        env = self.instrument()
        a = self.spawn('changelog-generate', dict(env, PAUSE_ALLOC='yes'))
        self.line(a, 'LOCK_ATTEMPT')
        self.line(a, 'LOCK_ACQUIRED')
        self.line(a, 'ALLOCATED')
        self.write('draft-b', '# Writer B\n')
        b = self.spawn('changelog-generate', dict(env, entry_draft='draft-b'))
        self.line(b, 'LOCK_ATTEMPT')
        self.assertFalse((self.root / 'changelog' / self.name.replace('.md', '-1.md')).exists())
        self.finish(a, release=True)
        self.assertIn(self.name.replace('.md', '-1.md'), self.finish(b))
        self.assertEqual((self.root / 'changelog' / self.name).read_text(), '# New entry\n')
        self.assertEqual((self.root / 'changelog' / self.name.replace('.md', '-1.md')).read_text(), '# Writer B\n')

    def test_inventory_check_and_atomic_publication_block_allocation(self):
        self.block('changelog-generate')
        self.draft_index()
        env = self.instrument()
        a = self.spawn('changelog-rebuild', dict(env, PAUSE_INDEX='yes'))
        self.line(a, 'LOCK_ATTEMPT')
        self.line(a, 'LOCK_ACQUIRED')
        self.line(a, 'INDEX_READY')
        b = self.spawn('changelog-generate', env)
        self.line(b, 'LOCK_ATTEMPT')
        self.assertFalse((self.root / 'changelog' / self.name.replace('.md', '-1.md')).exists())
        self.finish(a, release=True)
        self.finish(b)
        # Allocation occurred AFTER publication. Its owner's stale draft cannot publish.
        rejected = self.block('changelog-rebuild', check=False)
        self.assertNotEqual(rejected.returncode, 0)
        self.draft_index()
        self.block('changelog-rebuild')
        self.assertIn(self.name.replace('.md', '-1.md'), (self.root / 'changelog/README.md').read_text())

    def test_linked_worktrees_share_one_lock(self):
        worktree = self.root / 'linked'
        self.git('worktree', 'add', '-q', '--detach', str(worktree), 'HEAD')
        env = self.instrument()
        a = self.spawn('changelog-generate', dict(env, PAUSE_ALLOC='yes'))
        self.line(a, 'LOCK_ATTEMPT')
        self.line(a, 'LOCK_ACQUIRED')
        self.line(a, 'ALLOCATED')
        b = self.spawn('changelog-generate', dict(env, entry_draft=str(self.root / 'draft')), cwd=worktree)
        self.line(b, 'LOCK_ATTEMPT')
        self.assertFalse((worktree / 'changelog' / self.name).exists())
        self.finish(a, release=True)
        self.finish(b)
        self.assertTrue((worktree / 'changelog' / self.name).is_file())
        self.assertFalse((worktree / '.git/changelog.lock').exists())
        common = self.git('rev-parse', '--git-common-dir').strip()
        inode = (self.root / common / 'changelog.lock').stat().st_ino
        self.block('changelog-generate')
        self.assertEqual((self.root / common / 'changelog.lock').stat().st_ino, inode)

    def test_interrupted_allocation_and_publication_preserve_existing_work(self):
        self.write('other.txt', 'other staged\n')
        self.git('add', '--', 'other.txt')
        self.write('other.txt', 'later working edit\n')
        self.write('changelog/' + self.name, '# Existing entry\n')
        self.write('changelog/README.md', '# Existing index\n')
        self.git('add', '--', 'changelog/README.md')
        index_before = (self.root / '.git/index').read_bytes()
        self.write('.git/index.lock', 'another Git owner\n')
        env = self.instrument()
        for block, pause, marker in [('changelog-generate', 'PAUSE_ALLOC', 'ALLOCATED'),
                                      ('changelog-rebuild', 'PAUSE_INDEX', 'INDEX_READY')]:
            with self.subTest(phase=pause):
                self.draft_index()
                child = self.spawn(block, dict(env, **{pause: 'yes'}))
                self.line(child, 'LOCK_ATTEMPT')
                self.line(child, 'LOCK_ACQUIRED')
                self.line(child, marker)
                os.killpg(child.pid, signal.SIGKILL)
                child.communicate(timeout=5)
                self.assertEqual((self.root / 'changelog/README.md').read_text(), '# Existing index\n')
                self.assertEqual((self.root / 'changelog' / self.name).read_text(), '# Existing entry\n')
                self.assertEqual((self.root / '.git/index').read_bytes(), index_before)
                self.assertEqual((self.root / '.git/index.lock').read_text(), 'another Git owner\n')
                self.assertEqual((self.root / 'other.txt').read_text(), 'later working edit\n')
        self.draft_index()
        self.block('changelog-rebuild')


if __name__ == '__main__':
    unittest.main()
