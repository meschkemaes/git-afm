"""Git inspection, diff formatting, and execution utilities."""

import os
import re
import subprocess
from typing import Optional, Tuple, List

IGNORE_PATTERNS = [
    r"package-lock\.json$",
    r"pnpm-lock\.yaml$",
    r"yarn\.lock$",
    r"Cargo\.lock$",
    r"poetry\.lock$",
    r"Gemfile\.lock$",
    r"composer\.lock$",
    r"\.min\.(js|css)$",
    r"\.map$",
]

def run_cmd(cmd: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """Execute a command returning (code, stdout, stderr)."""
    try:
        res = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return res.returncode, res.stdout, res.stderr
    except Exception as e:
        return 1, "", str(e)


def is_git_repo(cwd: Optional[str] = None) -> bool:
    """Check whether the given directory is inside a git working tree."""
    code, out, _ = run_cmd(["git", "rev-parse", "--is-inside-work-tree"], cwd=cwd)
    return code == 0 and out.strip() == "true"


def get_current_branch(cwd: Optional[str] = None) -> str:
    """Get the name of the current active branch."""
    code, out, _ = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
    return out.strip() if code == 0 else "HEAD"


def get_staged_diff(cwd: Optional[str] = None) -> str:
    """Get git diff for staged files."""
    code, out, _ = run_cmd(["git", "diff", "--cached", "--no-color"], cwd=cwd)
    return out if code == 0 else ""


def get_unstaged_diff(cwd: Optional[str] = None) -> str:
    """Get git diff for unstaged tracked and modified files."""
    code, out, _ = run_cmd(["git", "diff", "--no-color"], cwd=cwd)
    return out if code == 0 else ""


def get_status_short(cwd: Optional[str] = None) -> str:
    """Get concise git status."""
    code, out, _ = run_cmd(["git", "status", "--short"], cwd=cwd)
    return out if code == 0 else ""


def stage_all(cwd: Optional[str] = None) -> Tuple[bool, str]:
    """Stage all changes (git add -A)."""
    code, out, err = run_cmd(["git", "add", "-A"], cwd=cwd)
    return code == 0, err or out


def commit_changes(message: str, cwd: Optional[str] = None) -> Tuple[bool, str]:
    """Execute git commit with the given message."""
    code, out, err = run_cmd(["git", "commit", "-m", message], cwd=cwd)
    return code == 0, (out or err).strip()


def copy_to_clipboard(text: str) -> bool:
    """Copy text to macOS clipboard using pbcopy."""
    try:
        proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, text=True)
        proc.communicate(input=text)
        return proc.returncode == 0
    except Exception:
        return False


def is_ignored_diff_file(file_path: str) -> bool:
    """Check if file diff should be omitted (e.g. lockfiles, minified bundles)."""
    for pat in IGNORE_PATTERNS:
        if re.search(pat, file_path, re.IGNORECASE):
            return True
    return False


def filter_and_truncate_diff(diff_text: str, max_chars: int = 12000) -> str:
    """Clean diff text: omit heavy lockfiles, compress large diffs to fit context window."""
    if not diff_text.strip():
        return ""

    # Split by diff header
    chunks = re.split(r"(?=diff --git )", diff_text)
    processed_chunks = []

    for chunk in chunks:
        if not chunk.strip():
            continue

        match = re.match(r"diff --git a/(\S+) b/(\S+)", chunk)
        file_name = match.group(1) if match else "unknown"

        if is_ignored_diff_file(file_name):
            processed_chunks.append(
                f"diff --git a/{file_name} b/{file_name}\n[Omitted lockfile/minified file diff]\n"
            )
        elif len(chunk) > 4000:
            # File diff is huge, keep head and summarize
            lines = chunk.splitlines()
            head_lines = "\n".join(lines[:60])
            processed_chunks.append(
                f"{head_lines}\n... [Remaining {len(lines) - 60} lines truncated for {file_name}]\n"
            )
        else:
            processed_chunks.append(chunk)

    combined = "\n".join(processed_chunks)
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n\n... [Diff truncated to fit context window]"

    return combined
