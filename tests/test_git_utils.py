"""Unit tests for git_utils."""

import os
from git_afm.git_utils import (
    is_git_repo,
    is_ignored_diff_file,
    filter_and_truncate_diff,
)


def test_is_git_repo():
    assert is_git_repo() is True


def test_is_ignored_diff_file():
    assert is_ignored_diff_file("package-lock.json") is True
    assert is_ignored_diff_file("src/app/pnpm-lock.yaml") is True
    assert is_ignored_diff_file("Cargo.lock") is True
    assert is_ignored_diff_file("dist/bundle.min.js") is True
    assert is_ignored_diff_file("dist/bundle.js.map") is True
    assert is_ignored_diff_file("src/index.ts") is False
    assert is_ignored_diff_file("git_afm/engine.py") is False


def test_filter_and_truncate_diff_omits_lockfiles():
    diff = """diff --git a/package-lock.json b/package-lock.json
index 123..456 100644
--- a/package-lock.json
+++ b/package-lock.json
@@ -1,5 +1,5 @@
+ "version": "2.0.0"
diff --git a/main.py b/main.py
index abc..def 100644
--- a/main.py
+++ b/main.py
+print("hello")
"""
    filtered = filter_and_truncate_diff(diff)
    assert "[Omitted lockfile/minified file diff]" in filtered
    assert 'print("hello")' in filtered


def test_filter_and_truncate_diff_max_chars():
    huge_diff = "diff --git a/big.txt b/big.txt\n" + ("+line of code\n" * 1000)
    truncated = filter_and_truncate_diff(huge_diff, max_chars=500)
    assert len(truncated) <= 600
    assert "truncated" in truncated.lower()
