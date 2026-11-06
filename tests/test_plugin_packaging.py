"""Check the package selected by the marketplace, including real CLI discovery."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PluginPackagingTests(unittest.TestCase):
    def test_marketplace_selects_the_maintained_plugin(self):
        marketplace = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
        entry, = marketplace['plugins']
        package = (ROOT / entry['source']).resolve()
        manifest = json.loads((package / '.claude-plugin/plugin.json').read_text())
        self.assertEqual(package, ROOT)
        self.assertEqual(entry['name'], manifest['name'])
        self.assertIsInstance(manifest['repository'], str)
        # Release metadata has one owner, so standalone and marketplace installs agree.
        self.assertNotIn('version', entry)
        self.assertTrue(manifest['version'])
        self.assertTrue((package / 'skills/commit/SKILL.md').is_file())

    @unittest.skipUnless(shutil.which('claude'), 'Claude Code CLI is not installed')
    def test_cli_validates_installs_and_discovers_the_skill(self):
        with tempfile.TemporaryDirectory(prefix='changelog-package-test-') as tmp:
            sandbox = Path(tmp)
            config = sandbox / 'config'
            config.mkdir()
            # Isolate user settings, plugin cache and auth; no model call is made.
            env = {k: v for k, v in os.environ.items()
                   if not k.startswith(('CLAUDE_', 'ANTHROPIC_', 'GIT_'))}
            env['CLAUDE_CONFIG_DIR'] = str(config)

            def cli(*args):
                result = subprocess.run(['claude', 'plugin', *args], cwd=sandbox,
                                        env=env, capture_output=True, text=True, timeout=60)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return result.stdout

            cli('validate', str(ROOT))
            cli('marketplace', 'add', str(ROOT), '--json')
            cli('install', 'changelog@changelog-plugin-marketplace', '--json')
            details = cli('details', 'changelog@changelog-plugin-marketplace')
            self.assertIn('Skills (1)  commit', details)
            manifest = json.loads((ROOT / '.claude-plugin/plugin.json').read_text())
            installed, = json.loads(cli('list', '--json'))
            self.assertEqual(installed['version'], manifest['version'])
            self.assertTrue(installed['enabled'])
            self.assertEqual(Path(installed['readFromFolder']).resolve(), ROOT)


if __name__ == '__main__':
    unittest.main()
