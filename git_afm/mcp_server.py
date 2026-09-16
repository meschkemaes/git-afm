"""Local Model Context Protocol (MCP) server powered by Apple Foundation Models."""

import sys
from mcp.server.fastmcp import FastMCP
from git_afm.engine import AFMEngine

mcp = FastMCP("apple-foundation-models", instructions="Local on-device Apple Foundation Models server")
_engine = None


def get_engine() -> AFMEngine:
    global _engine
    if _engine is None:
        _engine = AFMEngine()
        ok, reason = _engine.check_availability()
        if not ok:
            raise RuntimeError(f"Apple Foundation Models unavailable: {reason}")
    return _engine


@mcp.tool()
async def generate_conventional_commit(diff: str, language: str = "en", context: str = "") -> str:
    """Generate a formatted Conventional Commit from a git diff using Apple Foundation Models."""
    engine = get_engine()
    commit = await engine.generate_commit(diff, language=language, extra_context=context or None)
    return commit.format_message()


@mcp.tool()
async def generate_pr_summary(diff: str, language: str = "en", context: str = "") -> str:
    """Generate a structured Markdown Pull Request description from a git diff."""
    engine = get_engine()
    pr = await engine.generate_pr_summary(diff, language=language, extra_context=context or None)
    return pr.format_markdown()


@mcp.tool()
async def explain_diff(diff: str, language: str = "en") -> str:
    """Explain what changed in a git diff in plain language."""
    engine = get_engine()
    return await engine.explain_diff(diff, language=language)


def main():
    """Run the local AFM MCP server via stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
