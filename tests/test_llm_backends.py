from __future__ import annotations

import tomllib
from pathlib import Path
from unittest.mock import patch

from inkline.app.claude_bridge import _LLM_BACKEND_KEY, create_app
from inkline.app.llm_backends import GEMINI_BACKEND, resolve_backend


def test_resolve_backend_auto_prefers_claude_then_gemini():
    def fake_which(executable: str):
        if executable == "claude":
            return None
        if executable == "gemini":
            return "/usr/bin/gemini"
        return None

    with patch("inkline.app.llm_backends.shutil.which", side_effect=fake_which):
        assert resolve_backend("auto").name == "gemini"


def test_gemini_prompt_invocation_uses_stream_json():
    invocation = GEMINI_BACKEND.prompt_invocation(
        system="system text",
        prompt="user prompt",
        max_turns=12,
    )
    assert invocation.stdin_text == ""
    assert "--output-format" in invocation.cmd
    assert "stream-json" in invocation.cmd
    assert "--model" in invocation.cmd
    assert "--sandbox" in invocation.cmd
    assert "true" in invocation.cmd
    assert "--approval-mode" in invocation.cmd
    assert "auto_edit" in invocation.cmd
    assert "--policy" in invocation.cmd
    assert "--include-directories" in invocation.cmd
    policy = Path(invocation.cmd[invocation.cmd.index("--policy") + 1])
    assert policy.suffix == ".toml"
    assert policy.exists()


def test_gemini_policy_denies_shell_and_web_tools():
    invocation = GEMINI_BACKEND.prompt_invocation(
        system="system text",
        prompt="user prompt",
        max_turns=12,
    )
    policy = Path(invocation.cmd[invocation.cmd.index("--policy") + 1])
    data = tomllib.loads(policy.read_text(encoding="utf-8"))
    rules = data["rule"]
    denied = {
        rule["toolName"]
        for rule in rules
        if rule.get("decision") == "deny"
    }
    assert "run_shell_command" in denied
    assert "google_web_search" in denied


def test_gemini_model_comes_from_environment(monkeypatch):
    monkeypatch.setenv("INKLINE_GEMINI_MODEL", "gemini-test-model")
    invocation = GEMINI_BACKEND.prompt_invocation(
        system="system",
        prompt="prompt",
        max_turns=1,
    )
    assert invocation.cmd[invocation.cmd.index("--model") + 1] == "gemini-test-model"


def test_resolve_backend_auto_honors_environment(monkeypatch):
    monkeypatch.setenv("INKLINE_LLM_BACKEND", "gemini")
    assert resolve_backend("auto").name == "gemini"


def test_backend_capabilities_are_typed():
    caps = GEMINI_BACKEND.capabilities()
    assert caps.context_window >= 1_000_000
    assert caps.multimodal is True
    assert caps.context_caching is True


def test_create_app_stores_selected_backend():
    app = create_app("gemini")
    assert app[_LLM_BACKEND_KEY].name == "gemini"
