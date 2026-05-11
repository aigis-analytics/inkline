from __future__ import annotations

from pathlib import Path

from inkline.app.claude_bridge import _with_managed_knowledge_context
from inkline.app.knowledge_bundle import build_or_load_bundle
from inkline.app.llm_backends import GEMINI_BACKEND


def test_knowledge_bundle_builds_and_reuses_cache(tmp_path):
    first = build_or_load_bundle(context_window=200_000, cache_dir=tmp_path)
    second = build_or_load_bundle(context_window=200_000, cache_dir=tmp_path)

    assert first.bundle_hash
    assert first.token_count <= 100_000
    assert first.resources
    assert first.rebuilt is True
    assert second.bundle_hash == first.bundle_hash
    assert second.rebuilt is False


def test_gemini_prompt_gets_managed_knowledge_context(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    system = _with_managed_knowledge_context("base system", GEMINI_BACKEND)

    assert "base system" in system
    assert "MANAGED INKLINE KNOWLEDGE BUNDLE" in system
    assert "bundle_hash" in system
    assert "inkline://layouts" in system
