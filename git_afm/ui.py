"""Terminal UI and rich rendering for git-afm."""

import os
import sys
import tempfile
import subprocess
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.prompt import Prompt

from git_afm.models import ConventionalCommit, PullRequestSummary

console = Console()


def print_banner():
    """Render welcome header."""
    text = Text.from_markup(
        "[bold cyan]git-afm[/bold cyan] [dim] Powered 100% on-device by Apple Foundation Models[/dim]"
    )
    console.print(text)


def print_error(msg: str):
    """Render error message."""
    console.print(f"[bold red]Error:[/bold red] {msg}", file=sys.stderr)


def print_warning(msg: str):
    """Render warning message."""
    console.print(f"[bold yellow]Warning:[/bold yellow] {msg}")


def print_success(msg: str):
    """Render success message."""
    console.print(f"[bold green]✓[/bold green] {msg}")


def display_commit_preview(commit: ConventionalCommit, message_text: str):
    """Display rendered commit card."""
    title_style = "bold yellow" if commit.breaking_change else "bold green"
    header = f"[{title_style}]Type:[/{title_style}] {commit.type}"
    if commit.scope:
        header += f" | [bold cyan]Scope:[/bold cyan] {commit.scope}"
    if commit.breaking_change:
        header += " | [bold red]💥 BREAKING CHANGE[/bold red]"

    panel = Panel(
        Text(message_text),
        title=header,
        title_align="left",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)


def display_pr_preview(pr: PullRequestSummary, markdown_text: str):
    """Display rendered Pull Request markdown card."""
    syntax = Syntax(markdown_text, "markdown", theme="monokai", word_wrap=True)
    panel = Panel(
        syntax,
        title=f"[bold green]Pull Request:[/bold green] {pr.title}",
        title_align="left",
        border_style="magenta",
        padding=(1, 2),
    )
    console.print(panel)


def edit_text_in_editor(initial_text: str) -> str:
    """Open $EDITOR (or nano/vim) with initial text and return modified string."""
    editor = os.environ.get("EDITOR", "nano")
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w+", delete=False) as tf:
        tf.write(initial_text)
        temp_path = tf.name

    try:
        subprocess.call([editor, temp_path])
        with open(temp_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def format_action_menu_text(language: str = "en") -> tuple[Text, str]:
    """Build Rich Text object and prompt label for action menu."""
    text = Text()
    if language == "pt":
        items = [
            ("c", "bold cyan", "commit"),
            ("e", "bold yellow", "editar"),
            ("r", "bold magenta", "regenerar"),
            ("y", "bold blue", "copiar"),
            ("q", "bold red", "sair"),
        ]
        prompt_label = "Ação"
    else:
        items = [
            ("c", "bold cyan", "commit"),
            ("e", "bold yellow", "edit"),
            ("r", "bold magenta", "regenerate"),
            ("y", "bold blue", "copy"),
            ("q", "bold red", "quit"),
        ]
        prompt_label = "Action"

    for i, (key, style, label) in enumerate(items):
        if i > 0:
            text.append("   ")
        text.append(f"[{key}]", style=style)
        text.append(f" {label}")
    return text, prompt_label


def prompt_action_menu(language: str = "en") -> str:
    """Prompt user for action on generated commit."""
    text, prompt_label = format_action_menu_text(language=language)
    console.print(text)
    choice = Prompt.ask(prompt_label, choices=["c", "e", "r", "y", "q"], default="c")
    return choice.lower()

