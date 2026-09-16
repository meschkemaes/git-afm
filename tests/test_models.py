"""Unit tests for models and schema formatting."""

from git_afm.models import ConventionalCommit, PullRequestSummary


def test_conventional_commit_formatting():
    commit = ConventionalCommit(
        type="feat",
        scope="cli",
        subject="add interactive confirmation menu",
        bullet_points=[
            "Support commit, edit, and regenerate actions",
            "Integrate pbcopy for clipboard support",
        ],
        breaking_change=False,
    )

    assert commit.format_title() == "feat(cli): add interactive confirmation menu"
    msg = commit.format_message()
    assert msg.startswith("feat(cli): add interactive confirmation menu\n\n")
    assert "- Support commit, edit, and regenerate actions" in msg
    assert "BREAKING CHANGE" not in msg


def test_conventional_commit_breaking_change():
    commit = ConventionalCommit(
        type="refactor",
        scope="",
        subject="change engine interface to async",
        bullet_points=["Update AFMEngine methods"],
        breaking_change=True,
    )

    assert commit.format_title() == "refactor!: change engine interface to async"
    msg = commit.format_message()
    assert "BREAKING CHANGE: This commit introduces breaking changes." in msg


def test_pull_request_summary_markdown():
    pr = PullRequestSummary(
        title="feat(engine): integrate Apple Foundation Models",
        summary="This PR replaces third party LLMs with Apple on-device models.",
        key_changes=["Add AFMEngine class", "Use Apple Neural Engine on M4"],
        testing_steps=["Run pytest tests/", "Execute git-afm --dry-run"],
    )

    md = pr.format_markdown()
    assert "## Summary" in md
    assert "Apple on-device models" in md
    assert "- Add AFMEngine class" in md
    assert "- [ ] Run pytest tests/" in md
