"""Command-line interface for git-afm."""

import argparse
import asyncio
import sys
from typing import Optional

from rich.prompt import Confirm

from git_afm import __version__
from git_afm.engine import AFMEngine
from git_afm.git_utils import (
    is_git_repo,
    get_staged_diff,
    get_unstaged_diff,
    stage_all,
    commit_changes,
    copy_to_clipboard,
    get_status_short,
)
from git_afm.ui import (
    console,
    print_banner,
    print_error,
    print_warning,
    print_success,
    display_commit_preview,
    display_pr_preview,
    edit_text_in_editor,
    prompt_action_menu,
)


def parse_args():
    parser = argparse.ArgumentParser(
        prog="git-afm",
        description="Generate Conventional Commits and PRs 100% on-device with Apple Foundation Models.",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Stage all changes (git add -A) before generating commit",
    )
    parser.add_argument(
        "--pr",
        action="store_true",
        help="Generate a comprehensive Pull Request description in Markdown",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Explain the changes in plain language without committing",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Automatically commit without interactive confirmation",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Generate and print message without committing",
    )
    parser.add_argument(
        "--pt",
        action="store_true",
        help="Generate commit/PR description in Portuguese (default is English)",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy generated message/markdown to clipboard",
    )
    parser.add_argument(
        "-m",
        "--context",
        type=str,
        default=None,
        help="Additional context or developer intent to guide the model",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args()


async def run_cli():
    args = parse_args()
    print_banner()

    # 1. Verify git repo
    if not is_git_repo():
        print_error("Not a git repository (or any parent directory).")
        sys.exit(1)

    # 2. Verify Apple Foundation Models availability
    engine = AFMEngine()
    available, reason = engine.check_availability()
    if not available:
        print_error(f"Apple Foundation Models is unavailable: {reason}")
        print_warning("Ensure Apple Intelligence is enabled in System Settings.")
        sys.exit(1)

    # 3. Stage changes if requested
    if args.all:
        ok, out = stage_all()
        if not ok:
            print_error(f"Failed to stage changes: {out}")
            sys.exit(1)
        print_success("Staged all changes.")

    # 4. Check staged vs unstaged diff
    diff = get_staged_diff()
    if not diff.strip():
        unstaged = get_unstaged_diff()
        if not unstaged.strip() and not get_status_short().strip():
            console.print("[yellow]Working tree clean. Nothing to commit.[/yellow]")
            sys.exit(0)

        if unstaged.strip():
            console.print("[yellow]No staged changes found, but unstaged modifications exist.[/yellow]")
            if not args.yes and Confirm.ask("Do you want to stage all changes now?"):
                stage_all()
                diff = get_staged_diff()
            elif args.yes:
                stage_all()
                diff = get_staged_diff()
            else:
                print_warning("No staged changes to analyze. Aborting.")
                sys.exit(0)

    if not diff.strip():
        print_warning("No diff found to analyze. Aborting.")
        sys.exit(0)

    language = "pt" if args.pt else "en"

    # 5. Explain mode
    if args.explain:
        with console.status("[bold cyan]Analyzing diff with Apple Neural Engine...[/bold cyan]"):
            explanation = await engine.explain_diff(diff, language=language)
        console.print("\n[bold cyan]Diff Explanation:[/bold cyan]")
        console.print(explanation)
        sys.exit(0)

    # 6. PR mode
    if args.pr:
        with console.status("[bold magenta]Generating Pull Request description...[/bold magenta]"):
            pr = await engine.generate_pr_summary(diff, language=language, extra_context=args.context)

        md_text = pr.format_markdown()
        display_pr_preview(pr, md_text)

        if args.copy:
            if copy_to_clipboard(md_text):
                print_success("Copied PR markdown to clipboard!")

        if not args.dry_run and not args.copy:
            if Confirm.ask("Copy PR markdown to clipboard?"):
                if copy_to_clipboard(md_text):
                    print_success("Copied to clipboard!")
        sys.exit(0)

    # 7. Commit mode (interactive loop)
    while True:
        with console.status("[bold cyan]Generating Conventional Commit via Apple Foundation Models...[/bold cyan]"):
            commit = await engine.generate_commit(diff, language=language, extra_context=args.context)

        message = commit.format_message()
        display_commit_preview(commit, message)

        if args.dry_run:
            if args.copy:
                copy_to_clipboard(message)
                print_success("Copied to clipboard.")
            sys.exit(0)

        if args.yes:
            ok, out = commit_changes(message)
            if ok:
                print_success(f"Committed successfully:\n{message}")
            else:
                print_error(f"Git commit failed: {out}")
                sys.exit(1)
            sys.exit(0)

        action = prompt_action_menu(language=language)

        if action == "c":
            ok, out = commit_changes(message)
            if ok:
                print_success("Committed successfully!")
            else:
                print_error(f"Git commit failed: {out}")
                sys.exit(1)
            break
        elif action == "e":
            edited_message = edit_text_in_editor(message)
            if not edited_message:
                print_warning("Commit message empty after edit. Aborted.")
                break
            console.print("\n[bold]Edited commit message:[/bold]")
            console.print(edited_message)
            if Confirm.ask("Commit with this edited message?"):
                ok, out = commit_changes(edited_message)
                if ok:
                    print_success("Committed successfully!")
                else:
                    print_error(f"Git commit failed: {out}")
                    sys.exit(1)
            break
        elif action == "r":
            console.print("[dim]Regenerating message...[/dim]")
            continue
        elif action == "y":
            if copy_to_clipboard(message):
                print_success("Copied message to clipboard!")
            if Confirm.ask("Commit now?"):
                ok, out = commit_changes(message)
                if ok:
                    print_success("Committed successfully!")
                else:
                    print_error(f"Git commit failed: {out}")
            break
        elif action == "q":
            console.print("[dim]Aborted without committing.[/dim]")
            break


def main():
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        console.print("\n[dim]Cancelled by user.[/dim]")
        sys.exit(130)


def pr_main():
    """Entry point for direct PR generation (git-afm-pr)."""
    sys.argv.insert(1, "--pr")
    main()


if __name__ == "__main__":
    main()
