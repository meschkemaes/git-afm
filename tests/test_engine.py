"""Integration tests for AFMEngine running on-device Apple Foundation Models."""

import asyncio

import pytest

from git_afm.engine import AFMEngine
from git_afm.models import ConventionalCommit

pytestmark = pytest.mark.integration


@pytest.fixture
def engine():
    instance = AFMEngine()
    available, reason = instance.check_availability()
    if not available:
        pytest.skip(f"Apple Foundation Models unavailable: {reason}")
    return instance


def test_engine_availability(engine):
    available, reason = engine.check_availability()
    assert available is True, reason


def test_generate_commit_integration(engine):
    sample_diff = """diff --git a/auth.py b/auth.py
new file mode 100644
index 0000000..e69de29
--- /dev/null
+++ b/auth.py
@@ -0,0 +1,5 @@
+def authenticate_user(username: str, token: str) -> bool:
+    \"\"\"Validate user credentials against local session.\"\"\"
+    return username == "admin" and len(token) > 8
"""
    commit = asyncio.run(engine.generate_commit(sample_diff, language="en"))
    assert isinstance(commit, ConventionalCommit)
    assert commit.type in ["feat", "fix", "refactor", "perf", "test", "docs", "chore", "build", "ci"]
    assert commit.subject
    assert len(commit.bullet_points) >= 1
