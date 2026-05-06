from __future__ import annotations

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


def test_create_app_stores_selected_backend():
    app = create_app("gemini")
    assert app[_LLM_BACKEND_KEY].name == "gemini"
