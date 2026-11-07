"""Execute documented shell blocks with controlled concurrent processes.

Main has prose-only generation instructions. The legacy adapter below performs
those exact create/inventory/replace steps; commit tests extract main's actual
shell blocks unchanged. No model invocation or real repositories are used.
"""

import os
from pathlib import Path
import selectors
import signal
import subprocess
import unittest

from test_commit_workflow import GitFixture, SKILL, command_block


def generation():
    if '<!-- changelog-generate -->' in SKILL.read_text():
        return command_block('changelog-generate')
    # Current main Process Flow 5-6: create minute/slug path, fill template,
    # inventory *.md, then write the complete index. No executable block exists.
    return '''mkdir -p changelog
cat "$entry_draft" > "changelog/$entry_name"
printf '%s\\n' "changelog/$entry_name"
inventory=$(find changelog -maxdepth 1 -name '*.md' ! -name README.md | sort)
if test "${PAUSE_INDEX:-}" = yes; then
    echo INDEX_READY
    read -r release
fi
printf '%s\\n' "$inventory" > changelog/README.md'''


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
        if '<!-- scoped-review -->' in SKILL.read_text():
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
        self.assertIn('hook changed the snapshot', result.stderr)
        self.assertEqual(self.git('rev-parse', 'HEAD'), before)
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

    def test_identical_minute_and_slug_keep_both_entries(self):
        other = self.setup_owner_work()
        for draft, text in [('draft-a', '# Writer A\n'), ('draft-b', '# Writer B\n')]:
            self.write(draft, text)
        env = dict(self.env, entry_name='2026-11-06-1700-fix.md', entry_draft='draft-a')
        self.run_command_env(generation(), env)
        env['entry_draft'] = 'draft-b'
        self.run_command_env(generation(), env)
        entries = [p for p in (self.root / 'changelog').glob('*.md') if p.name != 'README.md']
        self.assertEqual({p.read_text() for p in entries}, {'# Writer A\n', '# Writer B\n'})
        index = (self.root / 'changelog/README.md').read_text()
        for path in entries:
            self.assertIn(path.name, index)
        self.assertEqual(self.git('ls-files', '--stage', '--', 'other.txt'), other)

    def run_command_env(self, source, env):
        return subprocess.run(['bash', '-ec', source], cwd=self.root, env=env,
                              capture_output=True, text=True, check=True, timeout=10)

    def instrument_generation(self):
        # Test-only Python startup instrumentation. Production shell commands and
        # helper stay unchanged. Pause immediately before the index rename.
        self.write('instrument/sitecustomize.py', '''import fcntl, os, sys
real_flock, real_replace, real_open = fcntl.flock, os.replace, os.open
def flock(fd, mode):
    print('LOCK_ATTEMPT', flush=True)
    return real_flock(fd, mode)
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
        return dict(self.env, PYTHONPATH=str(self.root / 'instrument'),
                    entry_name='2026-11-06-1700-fix.md')

    def spawn_generation(self, env):
        child = subprocess.Popen(['bash', '-ec', generation()], cwd=self.root, env=env,
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True, bufsize=1, start_new_session=True)
        self.addCleanup(self.stop_child, child)
        return child

    @staticmethod
    def stop_child(child):
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGKILL)
        child.communicate(timeout=5)

    def read_line(self, child):
        pending = getattr(child, '_pending', b'')
        while b'\n' not in pending:
            with selectors.DefaultSelector() as ready:
                ready.register(child.stdout, selectors.EVENT_READ)
                self.assertTrue(ready.select(timeout=5), 'helper protocol timed out')
            chunk = os.read(child.stdout.fileno(), 4096)
            self.assertTrue(chunk, 'helper exited before protocol response')
            pending += chunk
        line, child._pending = pending.split(b'\n', 1)
        return line.decode()

    def line(self, child, expected):
        self.assertEqual(self.read_line(child), expected)

    def test_inventory_and_index_write_are_serialized(self):
        other = self.setup_owner_work()
        env = self.instrument_generation()
        self.write('draft-a', '# Writer A\n')
        self.write('draft-b', '# Writer B\n')
        a = self.spawn_generation(dict(env, entry_draft='draft-a', PAUSE_INDEX='yes'))
        fixed = '<!-- changelog-generate -->' in SKILL.read_text()
        if fixed:
            self.line(a, 'LOCK_ATTEMPT')
        self.line(a, 'changelog/2026-11-06-1700-fix.md')
        self.line(a, 'INDEX_READY')
        b = self.spawn_generation(dict(env, entry_draft='draft-b', entry_name='2026-11-06-1700-other.md'))
        if fixed:
            self.line(b, 'LOCK_ATTEMPT')
            # B has reached the lock while A has an inventory pending rename.
            self.assertFalse((self.root / 'changelog/2026-11-06-1700-other.md').exists())
        else:
            out, err = b.communicate(timeout=5)
            self.assertEqual(b.returncode, 0, err)
        out, err = a.communicate(input='release\n', timeout=5)
        self.assertEqual(a.returncode, 0, err)
        if fixed:
            out, err = b.communicate(timeout=5)
            self.assertEqual(b.returncode, 0, err)
        index = (self.root / 'changelog/README.md').read_text()
        self.assertIn('2026-11-06-1700-fix.md', index)
        self.assertIn('2026-11-06-1700-other.md', index)
        self.assertEqual(self.git('ls-files', '--stage', '--', 'other.txt'), other)

    def test_concurrent_identical_minute_and_slug_get_suffix(self):
        if '<!-- changelog-generate -->' not in SKILL.read_text():
            self.skipTest('lock instrumentation requires the fixed helper')
        env = self.instrument_generation()
        self.write('draft-a', '# Writer A\n')
        self.write('draft-b', '# Writer B\n')
        a = self.spawn_generation(dict(env, entry_draft='draft-a', PAUSE_INDEX='yes'))
        self.line(a, 'LOCK_ATTEMPT')
        self.line(a, 'changelog/2026-11-06-1700-fix.md')
        self.line(a, 'INDEX_READY')
        b = self.spawn_generation(dict(env, entry_draft='draft-b'))
        self.line(b, 'LOCK_ATTEMPT')
        out, err = a.communicate(input='release\n', timeout=5)
        self.assertEqual(a.returncode, 0, err)
        out, err = b.communicate(timeout=5)
        self.assertEqual(b.returncode, 0, err)
        self.assertIn('changelog/2026-11-06-1700-fix-1.md', out)
        self.assertEqual((self.root / 'changelog/2026-11-06-1700-fix.md').read_text(), '# Writer A\n')
        self.assertEqual((self.root / 'changelog/2026-11-06-1700-fix-1.md').read_text(), '# Writer B\n')
        index = (self.root / 'changelog/README.md').read_text()
        self.assertIn('2026-11-06-1700-fix.md', index)
        self.assertIn('2026-11-06-1700-fix-1.md', index)

    def test_interrupted_allocation_and_index_write_preserve_existing_work(self):
        if '<!-- changelog-generate -->' not in SKILL.read_text():
            self.skipTest('interruption instrumentation requires the fixed helper')
        other = self.setup_owner_work()
        env = self.instrument_generation()
        self.write('changelog/2026-11-06-1700-fix.md', '# Existing owner\n')
        self.write('changelog/README.md', '# Existing index\n')
        self.git('add', '--', 'changelog/README.md')
        index_before = (self.root / '.git/index').read_bytes()
        self.write('.git/index.lock', 'another Git owner\n')
        self.write('draft', '# New entry\n')
        for pause, marker in [('PAUSE_ALLOC', 'ALLOCATED'), ('PAUSE_INDEX', 'INDEX_READY')]:
            with self.subTest(phase=pause):
                child = self.spawn_generation(dict(env, entry_draft='draft', **{pause: 'yes'}))
                self.line(child, 'LOCK_ATTEMPT')
                if pause == 'PAUSE_INDEX':
                    self.assertTrue(self.read_line(child).startswith('changelog/'))
                self.line(child, marker)
                # Kill both the shell and helper at the exact boundary.
                os.killpg(child.pid, signal.SIGKILL)
                child.communicate(timeout=5)
                self.assertEqual((self.root / 'changelog/README.md').read_text(), '# Existing index\n')
                self.assertEqual((self.root / 'changelog/2026-11-06-1700-fix.md').read_text(), '# Existing owner\n')
                self.assertEqual(self.git('ls-files', '--stage', '--', 'other.txt'), other)
                self.assertEqual((self.root / '.git/index').read_bytes(), index_before)
                self.assertEqual((self.root / '.git/index.lock').read_text(), 'another Git owner\n')
        self.run_command_env(generation(), dict(env, entry_draft='draft'))
        self.assertIn('2026-11-06-1700-fix.md', (self.root / 'changelog/README.md').read_text())

    def test_rebuild_and_explicit_amend_use_documented_commands(self):
        if '<!-- changelog-generate -->' not in SKILL.read_text():
            self.skipTest('fixed helper commands')
        self.write('draft', '# Original\n**Keywords:** [TESTING]\n')
        env = dict(self.env, entry_name='2026-11-06-1700-fix.md', entry_draft='draft')
        self.run_command_env(generation(), env)
        self.write('draft', '# Amended\n**Keywords:** [BUG_FIX]\n')
        self.run_command_env(command_block('changelog-amend'), env)
        self.run_command_env(command_block('changelog-rebuild'), env)
        index = (self.root / 'changelog/README.md').read_text()
        self.assertIn('Amended', index)
        self.assertIn('[BUG_FIX] (1)', index)
        self.assertNotIn('Original', index)


if __name__ == '__main__':
    unittest.main()
