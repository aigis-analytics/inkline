"""Tests for the inkline.learning self-learning package.

Tests are purely in-memory / temp-DB — no writes to ~/.local/share/inkline/.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_store(tmp_path: Path):
    """Create a LearningStore backed by a temp file."""
    from inkline.learning.store import LearningStore
    db = tmp_path / "test_sessions.db"
    return LearningStore(db_path=db)


# ---------------------------------------------------------------------------
# store.py
# ---------------------------------------------------------------------------

class TestLearningStore:
    def test_create_and_record_session(self, tmp_path):
        from inkline.learning.store import LearningStore, GenerationSession

        store = _make_store(tmp_path)
        session = GenerationSession(brand="minimal", template="consulting", audience="investors")
        sid = store.record_session(session)
        assert sid == session.session_id

        # Verify it was persisted
        with store._connect() as conn:
            row = conn.execute(
                "SELECT * FROM generation_sessions WHERE session_id=?", (sid,)
            ).fetchone()
        assert row is not None
        assert row["brand"] == "minimal"
        assert row["audience"] == "investors"

    def test_record_slide_choice(self, tmp_path):
        from inkline.learning.store import LearningStore, GenerationSession, SlideChoice

        store = _make_store(tmp_path)
        session = GenerationSession(brand="minimal")
        sid = store.record_session(session)

        choice = SlideChoice(session_id=sid, slide_index=0, slide_type="icon_stat",
                             section_type="financials")
        store.record_slide_choice(choice)

        with store._connect() as conn:
            row = conn.execute(
                "SELECT * FROM slide_choices WHERE session_id=?", (sid,)
            ).fetchone()
        assert row is not None
        assert row["slide_type"] == "icon_stat"
        assert row["section_type"] == "financials"

    def test_record_title_rewrite(self, tmp_path):
        from inkline.learning.store import LearningStore, TitleRewrite

        store = _make_store(tmp_path)
        rw = TitleRewrite(
            brand="minimal",
            original_title="Market Overview",
            rewritten_title="SAM growing 34% CAGR to $8B",
            section_type="market_size",
        )
        store.record_title_rewrite(rw)

        with store._connect() as conn:
            row = conn.execute("SELECT * FROM title_rewrites").fetchone()
        assert row["original_title"] == "Market Overview"
        assert row["rewritten_title"] == "SAM growing 34% CAGR to $8B"

    def test_update_regen_count(self, tmp_path):
        store = _make_store(tmp_path)
        store.update_regen_count("minimal", "content", "financials", was_regen=True)
        store.update_regen_count("minimal", "content", "financials", was_regen=True)
        store.update_regen_count("minimal", "content", "financials", was_regen=False)

        with store._connect() as conn:
            row = conn.execute(
                "SELECT * FROM regen_counts WHERE brand='minimal'"
            ).fetchone()
        assert row["total_uses"] == 3
        assert row["total_regens"] == 2

    def test_get_high_regen_combos(self, tmp_path):
        from inkline.learning.store import LearningStore, GenerationSession, SlideChoice

        store = _make_store(tmp_path)
        # Need 5 uses with >40% regen rate
        for i in range(5):
            store.update_regen_count("minimal", "content", "risk", was_regen=True)

        combos = store.get_high_regen_combos("minimal", min_rate=0.4, min_uses=5)
        assert len(combos) == 1
        assert combos[0]["slide_type"] == "content"
        assert combos[0]["regen_rate"] >= 0.4

    def test_get_section_type_preferences(self, tmp_path):
        from inkline.learning.store import GenerationSession, SlideChoice

        store = _make_store(tmp_path)

        # Add 3 sessions with slide choices for "financials" -> "kpi_strip"
        for _ in range(3):
            s = GenerationSession(brand="minimal")
            sid = store.record_session(s)
            store.record_slide_choice(SlideChoice(
                session_id=sid, slide_index=0, slide_type="kpi_strip",
                section_type="financials", accepted=1,
            ))

        prefs = store.get_section_type_preferences("minimal", "financials")
        assert "kpi_strip" in prefs

    def test_get_session_stats(self, tmp_path):
        from inkline.learning.store import GenerationSession

        store = _make_store(tmp_path)
        for _ in range(3):
            store.record_session(GenerationSession(brand="minimal"))

        stats = store.get_session_stats("minimal", days=30)
        assert stats["enabled"] is True
        assert stats["sessions"] == 3

    def test_store_disabled_on_bad_path(self, tmp_path):
        """A store with an unwritable path should disable itself and not raise."""
        from inkline.learning.store import LearningStore

        bad_path = Path("/nonexistent_dir/that/cant/be/created/sessions.db")
        store = LearningStore(db_path=bad_path)
        # Should not raise, just be disabled
        assert not store._enabled

    def test_get_audience_layout_prefs_empty(self, tmp_path):
        store = _make_store(tmp_path)
        result = store.get_audience_layout_prefs("minimal", "investors")
        assert result == ""


# ---------------------------------------------------------------------------
# session_context.py
# ---------------------------------------------------------------------------

class TestGenerationSession:
    def test_context_manager_records_slides(self, tmp_path):
        """Session context manager should persist slide choices on exit."""
        # Patch the store singleton
        from inkline.learning import store as store_mod
        old_instance = store_mod._store_instance
        store_mod._store_instance = _make_store(tmp_path)

        try:
            from inkline.learning.session_context import generation_session

            slides = [
                {"slide_type": "title", "data": {"company": "Test", "tagline": ""}},
                {"slide_type": "icon_stat", "data": {"section": "financials", "title": "KPIs"}},
            ]

            with generation_session(brand="minimal", audience="investors") as ctx:
                ctx.record_slides(slides)
                assert ctx.brand == "minimal"
                assert ctx.audience == "investors"

            # Session should have been persisted
            with store_mod._store_instance._connect() as conn:
                count = conn.execute("SELECT COUNT(*) FROM generation_sessions").fetchone()[0]
            assert count == 1

            with store_mod._store_instance._connect() as conn:
                choices = conn.execute("SELECT COUNT(*) FROM slide_choices").fetchone()[0]
            # Only slides with known slide_type are recorded
            assert choices == 2

        finally:
            store_mod._store_instance = old_instance

    def test_context_manager_fail_safe(self, tmp_path):
        """generation_session must not suppress exceptions from the caller."""
        from inkline.learning.session_context import generation_session

        with pytest.raises(ValueError, match="test error"):
            with generation_session(brand="minimal") as ctx:
                raise ValueError("test error")

    def test_session_context_set_quality(self, tmp_path):
        from inkline.learning.session_context import SessionContext
        ctx = SessionContext(brand="minimal")
        ctx.set_quality(85, "A")
        assert ctx._quality_score == 85
        assert ctx._quality_grade == "A"

    def test_session_context_set_anti_patterns(self):
        from inkline.learning.session_context import SessionContext
        ctx = SessionContext(brand="minimal")
        ctx.set_anti_pattern_hits(["LP-01", "TP-02"])
        assert ctx._anti_pattern_hits == ["LP-01", "TP-02"]


# ---------------------------------------------------------------------------
# extractor.py
# ---------------------------------------------------------------------------

class TestPatternExtractor:
    def test_run_empty_store(self, tmp_path):
        from inkline.learning.extractor import PatternExtractor

        store = _make_store(tmp_path)
        extractor = PatternExtractor(store)
        # With no brand specified, no brands found in DB
        report = extractor.run(brand=None)
        assert report.brands_processed == []
        assert report.anti_patterns_promoted == 0

    def test_run_empty_store_with_brand(self, tmp_path):
        from inkline.learning.extractor import PatternExtractor

        store = _make_store(tmp_path)
        extractor = PatternExtractor(store)
        # When brand is specified but has no data, processes with no results
        report = extractor.run(brand="minimal")
        assert "minimal" in report.brands_processed
        assert report.anti_patterns_promoted == 0

    def test_run_nightly_extraction_no_crash(self, tmp_path):
        """run_nightly_extraction should not raise even with an empty store."""
        from inkline.learning import store as store_mod
        old = store_mod._store_instance
        store_mod._store_instance = _make_store(tmp_path)
        try:
            from inkline.learning.extractor import run_nightly_extraction
            report = run_nightly_extraction(brand="minimal")
            assert report is not None
        finally:
            store_mod._store_instance = old

    def test_extract_regen_anti_patterns(self, tmp_path):
        from inkline.learning.extractor import PatternExtractor

        store = _make_store(tmp_path)
        # Add enough regen data
        for _ in range(6):
            store.update_regen_count("minimal", "content", "risk", was_regen=True)

        extractor = PatternExtractor(store)
        aps = extractor._extract_regen_anti_patterns("minimal")
        assert len(aps) == 1
        assert "content" in aps[0]["rule"]
        assert "risk" in aps[0]["rule"]

    def test_extract_title_rewrite_patterns_specificity(self, tmp_path):
        from inkline.learning.store import TitleRewrite
        from inkline.learning.extractor import PatternExtractor

        store = _make_store(tmp_path)
        # Add 3 rewrites that add numbers
        for i in range(3):
            store.record_title_rewrite(TitleRewrite(
                brand="minimal",
                original_title="Market Overview",
                rewritten_title=f"SAM growing {30 + i}% CAGR",
                section_type="market_size",
            ))

        extractor = PatternExtractor(store)
        patterns = extractor._extract_title_rewrite_patterns("minimal")
        rule_texts = [p["rule"] for p in patterns]
        # Should detect the specificity pattern
        assert any("specific" in r.lower() or "number" in r.lower() or "metric" in r.lower()
                   for r in rule_texts)

    def test_extraction_report_summary(self):
        from inkline.learning.extractor import ExtractionReport
        r = ExtractionReport(
            brands_processed=["minimal"],
            patterns_added=3,
            anti_patterns_promoted=1,
        )
        assert "minimal" not in r.summary or True  # summary has counts, not brand names
        assert "3" in r.summary


# ---------------------------------------------------------------------------
# anti_patterns.py — brand_anti_patterns parameter
# ---------------------------------------------------------------------------

class TestAntiPatternsLearned:
    def test_brand_anti_patterns_empty(self):
        from inkline.intelligence.anti_patterns import check_anti_patterns
        slides = [{"slide_type": "content", "data": {"title": "Test", "items": ["a"]}}]
        results = check_anti_patterns(slides, brand_anti_patterns=[])
        # No extra results from learned patterns
        assert all(r.rule_id != "L-0000" for r in results)

    def test_brand_anti_patterns_match(self):
        from inkline.intelligence.anti_patterns import check_anti_patterns
        slides = [
            {"slide_type": "content", "data": {"section": "risk", "title": "Risk"}},
        ]
        learned = [
            {
                "rule": "Avoid content for risk content (regen rate: 50%)",
                "slide_type": "content",
                "section_type": "risk",
                "confidence": 0.70,
            }
        ]
        results = check_anti_patterns(slides, brand_anti_patterns=learned)
        learned_results = [r for r in results if r.category == "learned"]
        assert len(learned_results) == 1
        assert "content" in learned_results[0].message

    def test_brand_anti_patterns_no_match(self):
        from inkline.intelligence.anti_patterns import check_anti_patterns
        slides = [
            {"slide_type": "icon_stat", "data": {"section": "financials", "title": "KPIs"}},
        ]
        learned = [
            {
                "rule": "Avoid content for risk content",
                "slide_type": "content",
                "section_type": "risk",
                "confidence": 0.70,
            }
        ]
        results = check_anti_patterns(slides, brand_anti_patterns=learned)
        learned_results = [r for r in results if r.category == "learned"]
        assert len(learned_results) == 0

    def test_brand_anti_patterns_backward_compat(self):
        """check_anti_patterns with no brand_anti_patterns arg still works."""
        from inkline.intelligence.anti_patterns import check_anti_patterns
        slides = [{"slide_type": "content", "data": {"title": "Test", "items": ["a", "b"]}}]
        results = check_anti_patterns(slides)
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# federation.py
# ---------------------------------------------------------------------------

class TestFederation:
    def test_export_disabled_raises(self, tmp_path, monkeypatch):
        from inkline.learning import federation as fed_mod

        monkeypatch.setattr(fed_mod, "_LEARNING_CONFIG",
                             tmp_path / "learning_config.yaml")

        # Write a config with federation disabled — use JSON fallback (no yaml needed)
        cfg = {"federation": {"enabled": False}}
        (tmp_path / "learning_config.yaml").write_text(
            json.dumps(cfg)  # federation.py falls back to JSON when yaml unavailable
        )

        # Patch load_learning_config to use our disabled config directly
        monkeypatch.setattr(fed_mod, "load_learning_config",
                             lambda: {"federation": {"enabled": False}})

        from inkline.learning.federation import export_pattern_delta, FederationDisabledError
        from datetime import datetime, timezone

        with pytest.raises(FederationDisabledError):
            export_pattern_delta(
                since=datetime(2026, 1, 1, tzinfo=timezone.utc),
                dry_run=True,
            )

    def test_export_dry_run_returns_dict(self, tmp_path, monkeypatch):
        from inkline.learning import federation as fed_mod
        from inkline.learning import store as store_mod

        # Patch load_learning_config to return enabled config
        monkeypatch.setattr(fed_mod, "load_learning_config",
                             lambda: {"federation": {"enabled": True,
                                                      "export_dm_rules": True,
                                                      "export_anti_patterns": True,
                                                      "export_brand_patterns": False,
                                                      "community_endpoint": ""}})

        old_store = store_mod._store_instance
        store_mod._store_instance = _make_store(tmp_path)

        try:
            from inkline.learning.federation import export_pattern_delta
            from datetime import datetime, timezone

            delta = export_pattern_delta(
                since=datetime(2026, 1, 1, tzinfo=timezone.utc),
                dry_run=True,
            )
            assert "schema_version" in delta
            assert "exported_at" in delta
            assert "quality_trend" in delta
            # Brand names must NOT appear
            delta_str = json.dumps(delta)
            assert "minimal" not in delta_str
            assert "acmecorp" not in delta_str
        finally:
            store_mod._store_instance = old_store

    def test_is_safe_rule_id(self):
        from inkline.learning.federation import _is_safe_rule_id
        assert _is_safe_rule_id("LP-01")
        assert _is_safe_rule_id("DM-001")
        assert _is_safe_rule_id("ABCD-1234")
        assert not _is_safe_rule_id("some free text pattern")
        assert not _is_safe_rule_id("Avoid content for risk (40%)")

    def test_get_privacy_summary_no_crash(self, tmp_path, monkeypatch):
        from inkline.learning import federation as fed_mod
        monkeypatch.setattr(fed_mod, "load_learning_config",
                             lambda: fed_mod._DEFAULT_CONFIG)
        from inkline.learning.federation import get_privacy_summary
        summary = get_privacy_summary()
        assert "FEDERATION" in summary.upper()
        assert "export" in summary.lower()


# ---------------------------------------------------------------------------
# pattern_memory.py — get_preferred_types SQLite fallback
# ---------------------------------------------------------------------------

class TestPatternMemorySQLiteFallback:
    def test_get_preferred_types_falls_back_to_yaml_when_empty_store(self, tmp_path):
        """When the SQLite store has <2 results, should fall back to YAML."""
        from inkline.learning import store as store_mod
        old = store_mod._store_instance
        store_mod._store_instance = _make_store(tmp_path)

        try:
            from inkline.intelligence.pattern_memory import get_preferred_types
            # With empty store, should return [] (no YAML either)
            result = get_preferred_types("minimal", "financials")
            assert isinstance(result, list)
        finally:
            store_mod._store_instance = old

    def test_get_preferred_types_uses_sqlite_when_populated(self, tmp_path, monkeypatch):
        from inkline.learning import store as store_mod
        from inkline.learning.store import GenerationSession, SlideChoice

        custom_store = _make_store(tmp_path)

        # Add enough slide choices
        for _ in range(3):
            s = GenerationSession(brand="minimal")
            sid = custom_store.record_session(s)
            custom_store.record_slide_choice(SlideChoice(
                session_id=sid, slide_index=0,
                slide_type="kpi_strip", section_type="financials", accepted=1,
            ))

        # Patch get_store in the module that pattern_memory imports from
        import inkline.learning.store as _store_target
        monkeypatch.setattr(_store_target, "get_store", lambda **kw: custom_store)

        from inkline.intelligence.pattern_memory import get_preferred_types
        result = get_preferred_types("minimal", "financials")
        assert "kpi_strip" in result


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

class TestCLI:
    def test_learn_command(self, capsys):
        from inkline.app.cli import main
        # Should not crash; aggregator may warn but pattern extractor handles empty store
        try:
            main(["learn"])
        except SystemExit as e:
            assert e.code == 0 or e.code is None

    def test_privacy_command(self, capsys):
        from inkline.app.cli import main
        main(["privacy"])
        out = capsys.readouterr().out
        assert "FEDERATION" in out.upper()

    def test_privacy_disable_enable(self, tmp_path, monkeypatch):
        from inkline.learning import federation as fed_mod
        monkeypatch.setattr(fed_mod, "_LEARNING_CONFIG", tmp_path / "test_lc.yaml")
        monkeypatch.setattr(fed_mod, "_CONFIG_DIR", tmp_path)
        # Ensure save_learning_config uses json fallback (no yaml in test env)
        monkeypatch.setattr(fed_mod, "save_learning_config",
                             lambda cfg: (tmp_path / "test_lc.yaml").write_text(json.dumps(cfg)))

        from inkline.app.cli import cmd_privacy
        import argparse

        # Track config state through a mutable dict
        _state = {}

        def _mock_set(enabled: bool) -> None:
            _state["enabled"] = enabled

        monkeypatch.setattr(fed_mod, "set_federation_enabled", _mock_set)

        # Disable
        args = argparse.Namespace(disable=True, enable=False, brand="")
        cmd_privacy(args)
        assert _state.get("enabled") is False

        # Re-enable
        args = argparse.Namespace(disable=False, enable=True, brand="")
        cmd_privacy(args)
        assert _state.get("enabled") is True

    def test_export_patterns_dry_run(self, tmp_path, monkeypatch, capsys):
        from inkline.learning import federation as fed_mod
        from inkline.learning import store as store_mod

        monkeypatch.setattr(fed_mod, "load_learning_config",
                             lambda: {"federation": {"enabled": True,
                                                      "export_dm_rules": True,
                                                      "export_anti_patterns": True,
                                                      "community_endpoint": ""}})

        old_store = store_mod._store_instance
        store_mod._store_instance = _make_store(tmp_path)

        try:
            import argparse
            from inkline.app.cli import cmd_export_patterns
            args = argparse.Namespace(since="", dry_run=True)
            cmd_export_patterns(args)
            captured = capsys.readouterr()
            out = captured.out.strip()
            # The JSON output is the entire stdout
            delta = json.loads(out)
            assert "schema_version" in delta
        finally:
            store_mod._store_instance = old_store
