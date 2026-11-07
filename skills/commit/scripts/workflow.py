#!/usr/bin/env python3
"""Allocate changelog entries and publish model-written indexes. No Git writes."""

import argparse
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import re
import subprocess
import tempfile


def git_path(option):
    return Path(subprocess.check_output(
        ["git", "rev-parse", option], text=True).strip()).resolve()


def atomic_write(path, content):
    if path.is_symlink():
        raise ValueError(f"refusing symlink: {path}")
    fd, tmp = tempfile.mkstemp(prefix=".changelog-write-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(content)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    finally:
        Path(tmp).unlink(missing_ok=True)


@contextmanager
def changelog_lock():
    directory = git_path("--show-toplevel") / "changelog"
    if directory.is_symlink():
        raise ValueError("refusing symlink changelog directory")
    directory.mkdir(exist_ok=True)
    # Persistent advisory lock: never unlink it (waiters may hold its inode).
    lock = git_path("--git-common-dir") / "changelog.lock"
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as owner:
        fcntl.flock(owner, fcntl.LOCK_EX)
        yield directory


def generate(name, draft):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}-\d{4}-[A-Za-z0-9-]+\.md", name):
        raise ValueError("expected minute timestamp and alphanumeric/hyphen slug")
    with changelog_lock() as directory:
        content = Path(draft).read_bytes()
        suffix = 0
        while True:
            path = directory / (name if not suffix else f"{Path(name).stem}-{suffix}.md")
            try:
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
                break
            except FileExistsError:
                suffix += 1
        # Interrupted allocation can leave an owned partial entry, never delete
        # an existing file. Retry by inspecting/reusing the printed path.
        print(f"changelog/{path.name}", flush=True)
        with os.fdopen(fd, "wb") as entry:
            entry.write(content)
            entry.flush()
            os.fsync(entry.fileno())


def rebuild(draft):
    with changelog_lock() as directory:
        content = Path(draft).read_bytes()
        missing = sorted(path.name for path in directory.glob("*.md")
                         if path.name != "README.md" and os.fsencode(path.name) not in content)
        if missing:
            raise ValueError("index draft is missing entries: " + ", ".join(missing) +
                             "; rebuild the complete draft and retry rebuild --index-draft")
        atomic_write(directory / "README.md", content)


def amend(name, draft):
    if Path(name).name != name or name == "README.md" or not name.endswith(".md"):
        raise ValueError("expected an existing entry basename")
    with changelog_lock() as directory:
        path = directory / name
        if not path.is_file():
            raise ValueError("entry does not exist")
        atomic_write(path, Path(draft).read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    for action, help_text in (("generate", "allocate a new entry without overwriting"),
                              ("amend", "replace an explicitly selected existing entry")):
        sub = actions.add_parser(action, help=help_text)
        sub.add_argument("--entry-name", required=True, help="entry basename")
        sub.add_argument("--entry-draft", required=True, type=Path, help="private Markdown draft")
    sub = actions.add_parser("rebuild", help="publish a complete model-written index under lock")
    sub.add_argument("--index-draft", required=True, type=Path, help="private complete README draft")
    args = parser.parse_args()
    try:
        if args.action == "generate":
            generate(args.entry_name, args.entry_draft)
        elif args.action == "amend":
            amend(args.entry_name, args.entry_draft)
        else:
            rebuild(args.index_draft)
    except (ValueError, OSError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
