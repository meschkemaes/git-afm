"""Unit tests for UI rendering and action menu formatting."""

from git_afm.ui import format_action_menu_text, prompt_action_menu


def test_format_action_menu_text_english():
    text, prompt_label = format_action_menu_text(language="en")
    plain = text.plain

    assert prompt_label == "Action"
    assert "[c] commit" in plain
    assert "[e] edit" in plain
    assert "[r] regenerate" in plain
    assert "[y] copy" in plain
    assert "[q] quit" in plain


def test_format_action_menu_text_portuguese():
    text, prompt_label = format_action_menu_text(language="pt")
    plain = text.plain

    assert prompt_label == "Ação"
    assert "[c] commit" in plain
    assert "[e] editar" in plain
    assert "[r] regenerar" in plain
    assert "[y] copiar" in plain
    assert "[q] sair" in plain


def test_prompt_action_menu_input(monkeypatch):
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda prompt, choices, default: "c")
    assert prompt_action_menu(language="en") == "c"

    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda prompt, choices, default: "E")
    assert prompt_action_menu(language="pt") == "e"
