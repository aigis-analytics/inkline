"""Tests for the pluggable LLM caller in DesignAdvisor + the Claude Code helper.

These tests do NOT require an Anthropic API key, network access, or the
``claude`` CLI. The Claude-Code-availability test simply checks the helper's
detection logic; the LLM-injection test uses a stub callable.
"""

from __future__ import annotations

import pytest

from inkline.intelligence import (
    DesignAdvisor,
    LLMCaller,
    build_claude_code_caller,
    claude_code_available,
    ClaudeCodeNotInstalled,
)


# ── DesignAdvisor accepts a custom LLM caller ─────────────────────────────


def test_design_advisor_accepts_llm_caller():
    """The constructor must accept an llm_caller parameter and store it."""
    def stub(system: str, user: str) -> str:
        return "[]"
    advisor = DesignAdvisor(brand="minimal", llm_caller=stub)
    assert advisor.llm_caller is stub


def test_design_advisor_uses_injected_caller_in_llm_mode(monkeypatch):
    """LLM mode must route through the injected caller, not the Anthropic SDK."""
    captured = {}

    def stub(system: str, user: str) -> str:
        captured["system"] = system
        captured["user"] = user
        # Return a minimal but valid slide spec the parser will accept
        return '```json\n[{"slide_type": "title", "data": {"company": "X"}}]\n```'

    advisor = DesignAdvisor(brand="minimal", mode="llm", llm_caller=stub)
    slides = advisor.design_deck(
        title="Test",
        sections=[{"type": "executive_summary", "narrative": "Hello"}],
    )
    # The injected caller was actually used
    assert "system" in captured and "user" in captured
    assert "Test" in captured["user"]
    # And the parser turned its output into a slide list
    assert isinstance(slides, list) and len(slides) == 1
    assert slides[0]["slide_type"] == "title"


def test_design_advisor_llm_mode_works_without_api_key_when_caller_present():
    """If an llm_caller is supplied, llm-mode should activate even with no API key."""
    def stub(system: str, user: str) -> str:
        return '```json\n[{"slide_type": "content", "data": {"section": "S", "title": "T", "items": ["a"]}}]\n```'

    advisor = DesignAdvisor(brand="minimal", mode="llm", api_key="", llm_caller=stub)
    # Should NOT silently fall back to rules mode just because api_key is empty
    slides = advisor.design_deck(
        title="Test",
        sections=[{"type": "x", "items": ["a", "b"]}],
    )
    assert len(slides) == 1
    assert slides[0]["slide_type"] == "content"


def test_design_advisor_falls_back_to_rules_when_no_caller_and_no_key(monkeypatch):
    """No caller AND no API key → must skip LLM and use rules mode."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    advisor = DesignAdvisor(brand="minimal", mode="llm", api_key="")
    assert advisor.api_key == ""
    assert advisor.llm_caller is None
    # Should not raise — rules mode produces a deterministic deck
    slides = advisor.design_deck(
        title="Test",
        sections=[{"type": "x", "items": ["a", "b"]}],
    )
    assert isinstance(slides, list)
    assert len(slides) >= 1


def test_llm_caller_type_alias_is_exported():
    """LLMCaller type alias must be importable from the intelligence package."""
    # It's a Callable type — calling assert on its existence is enough
    assert LLMCaller is not None


# ── Claude Code helper ────────────────────────────────────────────────────


def test_claude_code_available_returns_bool():
    """The detection helper must return a bool without raising."""
    result = claude_code_available()
    assert isinstance(result, bool)


def test_build_claude_code_caller_when_cli_present():
    """If the claude CLI is installed, we can build a caller without raising."""
    if not claude_code_available():
        pytest.skip("claude CLI not on $PATH")
    caller = build_claude_code_caller(model="sonnet", timeout=60)
    assert callable(caller)


def test_build_claude_code_caller_raises_when_cli_missing(monkeypatch):
    """When the CLI is missing, the constructor must raise ClaudeCodeNotInstalled."""
    monkeypatch.setattr(
        "inkline.intelligence.claude_code.shutil.which",
        lambda name: None,
    )
    with pytest.raises(ClaudeCodeNotInstalled):
        build_claude_code_caller()
