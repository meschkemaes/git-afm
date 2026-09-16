"""Data models and @fm.generable schemas for git-afm."""

from typing import List
import apple_fm_sdk as fm


@fm.generable("Conventional Commit")
class ConventionalCommit:
    type: str = fm.guide(
        "Commit type",
        anyOf=["feat", "fix", "refactor", "perf", "test", "docs", "chore", "build", "ci"],
    )
    scope: str = fm.guide(
        "Component or module affected (e.g. cli, engine, models, ui, auth) or empty string if global"
    )
    subject: str = fm.guide(
        "Concise summary of the change in imperative mood without trailing period"
    )
    bullet_points: List[str] = fm.guide(
        "List of 1 to 4 concise bullet points explaining what changed and why"
    )
    breaking_change: bool = fm.guide("True if this commit introduces a breaking change")

    def format_title(self) -> str:
        clean_scope = self.scope.strip().lower() if self.scope else ""
        clean_subject = self.subject.strip().rstrip(".")
        prefix = f"{self.type}({clean_scope})" if clean_scope else self.type
        if self.breaking_change:
            prefix += "!"
        return f"{prefix}: {clean_subject}"

    def format_message(self) -> str:
        title = self.format_title()
        bullets = [b.strip() for b in self.bullet_points if b and b.strip()]
        if not bullets:
            return title

        body = "\n".join(f"- {b.lstrip('- ')}" for b in bullets)
        if self.breaking_change:
            body += "\n\nBREAKING CHANGE: This commit introduces breaking changes."
        return f"{title}\n\n{body}"


@fm.generable("Pull Request Description")
class PullRequestSummary:
    title: str = fm.guide("PR title in Conventional Commit format")
    summary: str = fm.guide("Executive summary paragraph explaining why and what was changed")
    key_changes: List[str] = fm.guide("List of 2 to 6 key changes made in this pull request")
    testing_steps: List[str] = fm.guide("List of 1 to 4 steps to test or verify the changes")

    def format_markdown(self) -> str:
        changes_md = "\n".join(f"- {c.lstrip('- ')}" for c in self.key_changes if c.strip())
        testing_md = "\n".join(f"- [ ] {t.lstrip('- ')}" for t in self.testing_steps if t.strip())
        return f"""## Summary
{self.summary.strip()}

## Key Changes
{changes_md}

## Verification & Testing
{testing_md}
"""
