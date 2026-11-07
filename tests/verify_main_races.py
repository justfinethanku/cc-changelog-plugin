"""Export main to a disposable directory and require the four race failures.

Run from the repository root: python3 tests/verify_main_races.py [main-ref]
"""

import io
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile


root = Path(__file__).resolve().parents[1]
ref = sys.argv[1] if len(sys.argv) > 1 else 'origin/main'
sha = subprocess.check_output(['git', 'rev-parse', ref], cwd=root, text=True).strip()
archive = subprocess.check_output(['git', 'archive', sha], cwd=root)
with tempfile.TemporaryDirectory(prefix='changelog-main-races-') as tmp:
    target = Path(tmp)
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        source.extractall(target, filter='data')
    # Use the same harness/fixtures against the exported skill, not a patched
    # copy of its commands. Generation's prose adapter is explained in the test.
    for name in ('test_races.py', 'test_commit_workflow.py'):
        shutil.copyfile(root / 'tests' / name, target / 'tests' / name)
    names = [
        'test_identical_minute_and_slug_keep_both_entries',
        'test_inventory_and_index_write_are_serialized',
        'test_post_review_edit_is_not_committed',
        'test_rejection_and_retry_preserve_later_edits_and_staging',
    ]
    result = subprocess.run([sys.executable, '-m', 'unittest', '-v',
                             *['test_races.RaceTests.' + name for name in names]],
                            cwd=target / 'tests', capture_output=True, text=True,
                            timeout=60)
    output = result.stdout + result.stderr
    print(f'Baseline main: {sha}\n{output}', end='')
    if result.returncode != 1 or 'FAILED (failures=4)' not in output:
        raise SystemExit('Expected exactly four assertion failures, no test errors')
    for name in names:
        if f'FAIL: {name} ' not in output:
            raise SystemExit(f'Missing expected race assertion: {name}')
    print('Verified: all four race assertions fail on main.')
