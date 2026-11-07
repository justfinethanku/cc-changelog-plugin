#!/usr/bin/env python3
"""Local transactions for the commit skill. No remote operations."""

import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def git(*args, env=None, data=None, check=True):
    return subprocess.run(["git", "--literal-pathspecs", *args], env=env,
                          input=data, stdout=subprocess.PIPE, check=check).stdout


def head():
    result = git("rev-parse", "--verify", "HEAD", check=False)
    return result.strip().decode() or None


@contextmanager
def index_lock():
    index = Path(os.fsdecode(git("rev-parse", "--git-path", "index")).strip()).absolute()
    lock = Path(str(index) + ".lock")
    # Only remove our own lock. An existing owner's lock is an error.
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    owned = True

    def publish():
        nonlocal owned
        # After replacement another Git process can create index.lock at once.
        # Cleanup must never unlink that new owner's file.
        owned = False
        os.replace(lock, index)

    try:
        yield index, lock, publish
    finally:
        if owned:
            lock.unlink(missing_ok=True)


def index_env(path):
    return dict(os.environ, GIT_INDEX_FILE=str(path))


def entries(paths, env=None):
    return git("ls-files", "--stage", "-z", "--", *paths, env=env)


def copy_index(index, lock, state):
    if index.exists():
        shutil.copyfile(index, lock)
    else:
        # Do not unlink the live reservation, even for an unborn repository.
        empty = state / "empty-index"
        git("read-tree", "--empty", env=index_env(empty))
        shutil.copyfile(empty, lock)


def remove_record(path):
    zero = b"0" * len(git("hash-object", "--stdin", data=b"").strip())
    return b"0 " + zero + b"\t" + os.fsencode(path) + b"\0"


def stage(state, paths):
    if not paths:
        raise ValueError("empty commit scope")
    state.mkdir()  # New state for each review; never overwrite another review.
    with index_lock() as (index, lock, publish):
        copy_index(index, lock, state)
        env = index_env(lock)
        git("add", "--", *paths, env=env)
        # Preserve scoped staging on check failure, like git add + diff --check.
        shutil.copyfile(lock, state / "staged")
        checked = subprocess.run(
            ["git", "--literal-pathspecs", "diff", "--cached", "--check", "--", *paths],
            env=env, stdout=subprocess.PIPE)
        if checked.returncode:
            publish()
            raise ValueError(checked.stdout.decode() or "stage check failed")
        base = head()
        review_env = index_env(state / "index")
        git("read-tree", base or "--empty", env=review_env)
        # NUL-delimited index records keep arbitrary literal filenames intact.
        records = entries(paths, env)
        removals = b"".join(remove_record(p) for p in paths)
        git("update-index", "-z", "--index-info", env=review_env, data=removals + records)
        tree = git("write-tree", env=review_env).strip().decode()
        branch = git("symbolic-ref", "-q", "HEAD", check=False).strip().decode()
        (state / "review.json").write_text(json.dumps(dict(
            base=base, branch=branch, paths=paths, tree=tree)))
        publish()
        print(git("diff", "--cached", "--stat", env=review_env).decode(), end="")


def commit(state, message):
    review = json.loads((state / "review.json").read_text())
    env = index_env(state / "index")
    with index_lock() as (index, lock, publish):
        if head() != review["base"] or git("symbolic-ref", "-q", "HEAD", check=False).strip().decode() != review["branch"]:
            raise ValueError("HEAD changed; stage and review again")
        if Path(os.fsdecode(git("rev-parse", "--git-path", "MERGE_HEAD")).strip()).exists():
            raise ValueError("finish the merge before a scoped commit")
        # Run validation hooks on the private index. They may reject, but may not
        # silently change the reviewed tree. commit-tree never rereads work files.
        msg = state / "message"
        msg.write_text(message + "\n")
        git("hook", "run", "--ignore-missing", "pre-commit", env=env)
        git("hook", "run", "--ignore-missing", "prepare-commit-msg", "--", str(msg), "message", env=env)
        git("hook", "run", "--ignore-missing", "commit-msg", "--", str(msg), env=env)
        if git("write-tree", env=env).strip().decode() != review["tree"]:
            raise ValueError("hook changed the snapshot; stage and review again")
        if review["base"] and git("rev-parse", review["base"] + "^{tree}").strip().decode() == review["tree"]:
            raise ValueError("no selected changes to commit")
        args = ["commit-tree", review["tree"], "-F", str(msg)]
        if review["base"]:
            args += ["-p", review["base"]]
        signed = git("config", "--bool", "commit.gpgsign", check=False).strip()
        if signed == b"true":
            args += ["-S"]
        sha = git(*args, env=env).strip().decode()
        # Prepare a replacement real index before moving HEAD. Only consume a
        # selected entry if it still equals the staged revision we reviewed.
        copy_index(index, lock, state)
        for path in review["paths"]:
            if entries([path]) == entries([path], index_env(state / "staged")):
                record = entries([path], env)
                git("update-index", "-z", "--index-info", env=index_env(lock),
                    data=remove_record(path) + record)
        # CAS refuses a concurrent commit. Keep the SHA for interrupted recovery.
        (state / "commit").write_text(sha + "\n")
        if git("symbolic-ref", "-q", "HEAD", check=False).strip().decode() != review["branch"]:
            raise ValueError("branch changed; stage and review again")
        # Address the saved branch, rather than dereferencing a mutable HEAD.
        target = review["branch"] or "HEAD"
        git("update-ref", "--no-deref", "-m", "commit: " + message.splitlines()[0],
            target, sha, review["base"] or "0" * len(sha))
        publish()
    print(sha)
    # A post-commit failure cannot undo the commit; report its SHA first.
    git("hook", "run", "--ignore-missing", "post-commit", env=env, check=False)


def atomic_write(path, content):
    if path.is_symlink():
        raise ValueError(f"refusing symlink: {path}")
    fd, tmp = tempfile.mkstemp(prefix=".changelog-write-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as out:
            out.write(content)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, path)
    finally:
        Path(tmp).unlink(missing_ok=True)


def render_index(directory):
    months, keywords = {}, {}
    for path in sorted(directory.glob("*.md"), reverse=True):
        if path.name == "README.md":
            continue
        if path.is_symlink():
            raise ValueError(f"refusing symlink: {path}")
        lines = path.read_text().splitlines()
        title = next((s[2:] for s in lines if s.startswith("# ")), path.stem)
        for i, line in enumerate(lines[:-1]):
            if line == "## Session Summary":
                title = lines[i + 1]
        tags = set()
        for i, line in enumerate(lines):
            if line.startswith("**Keywords") or line == "## Keywords":
                tags.update(re.findall(r"\[([A-Z0-9_]+)\]", line + " " + (lines[i + 1] if i + 1 < len(lines) else "")))
        link = f"[{title}]({path.name})"
        months.setdefault(path.name[:7], []).append(f"- {link} {' '.join('[' + t + ']' for t in sorted(tags))}".rstrip())
        for tag in sorted(tags):
            keywords.setdefault(tag, []).append(link)
    output = ["# Changelog", ""]
    for month, rows in sorted(months.items(), reverse=True):
        output += [f"## {month}", "", *rows, ""]
    output += ["## Keyword Index", ""]
    for tag, links in sorted(keywords.items()):
        output += [f"### [{tag}] ({len(links)})", "", *["- " + link for link in links], ""]
    return "\n".join(output)


@contextmanager
def changelog_lock():
    directory = Path("changelog")
    if directory.is_symlink():
        raise ValueError("refusing symlink changelog directory")
    directory.mkdir(exist_ok=True)
    # Persistent advisory lock: never unlink it (waiters may hold its inode).
    fd = os.open(directory / ".write.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as owner:
        fcntl.flock(owner, fcntl.LOCK_EX)
        yield directory


def generate(name, draft):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}-\d{4}-[A-Za-z0-9-]+\.md", name):
        raise ValueError("expected minute timestamp and alphanumeric/hyphen slug")
    with changelog_lock() as directory:
        content = Path(draft).read_text()
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
        print(path, flush=True)
        with os.fdopen(fd, "w") as entry:
            entry.write(content)
            entry.flush()
            os.fsync(entry.fileno())
        atomic_write(directory / "README.md", render_index(directory))


def rebuild():
    with changelog_lock() as directory:
        atomic_write(directory / "README.md", render_index(directory))


def amend(name, draft):
    if Path(name).name != name or name == "README.md" or not name.endswith(".md"):
        raise ValueError("expected an existing entry basename")
    with changelog_lock() as directory:
        path = directory / name
        if not path.is_file():
            raise ValueError("entry does not exist")
        atomic_write(path, Path(draft).read_text())
        atomic_write(directory / "README.md", render_index(directory))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["generate", "amend", "rebuild", "stage", "commit"])
    parser.add_argument("target", nargs="?")
    parser.add_argument("values", nargs="*")
    args = parser.parse_args()
    if args.action == "generate":
        generate(args.target, *args.values)
    elif args.action == "amend":
        amend(args.target, *args.values)
    elif args.action == "rebuild":
        rebuild()
    elif args.action == "stage":
        stage(Path(args.target).absolute(), args.values)
    else:
        commit(Path(args.target).absolute(), *args.values)


if __name__ == "__main__":
    main()
