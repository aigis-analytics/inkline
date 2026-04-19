"""Generation session context manager.

Wraps a design_deck() call and automatically records signals to the learning
store without changing the caller API.

Usage::

    from inkline.learning import generation_session

    with generation_session(brand="minimal", audience="investors") as ctx:
        slides = advisor.design_deck(...)
        ctx.record_slides(slides)

The context manager is a no-op when INKLINE_LEARNING_ENABLED=false or when
the learning store is unavailable (disk full, permission error, etc.).
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Generator

log = logging.getLogger(__name__)


@dataclass
class SessionContext:
    """Mutable context object passed into the ``with`` block."""

    brand: str
    template: str = ""
    audience: str = ""
    goal: str = ""
    deck_id: str = ""
    mode: str = "llm"
    session_id: str = ""
    _slides: list[dict] = field(default_factory=list, repr=False)
    _quality_score: int = 0
    _quality_grade: str = ""
    _anti_pattern_hits: list[str] = field(default_factory=list)
    _dm_rules_used: list[str] = field(default_factory=list)

    def record_slides(self, slides: list[dict[str, Any]]) -> None:
        """Call after design_deck() completes to register slide choices."""
        self._slides = slides or []

    def set_quality(self, score: int, grade: str = "") -> None:
        """Optionally record the quality score from quality_scorer."""
        self._quality_score = score
        self._quality_grade = grade

    def set_anti_pattern_hits(self, hits: list[str]) -> None:
        """Optionally record which anti-pattern rules fired."""
        self._anti_pattern_hits = hits or []

    def set_dm_rules(self, rules: list[str]) -> None:
        """Optionally record which DM rules were applied."""
        self._dm_rules_used = rules or []


@contextmanager
def generation_session(
    brand: str,
    template: str = "",
    audience: str = "",
    goal: str = "",
    deck_id: str = "",
    mode: str = "llm",
) -> Generator[SessionContext, None, None]:
    """Context manager that wraps a design_deck() call and records signals.

    On exit, writes the generation session and all slide choices to the
    LearningStore. If the store is unavailable, a warning is logged and
    generation proceeds normally — this is fully fail-safe.

    Parameters
    ----------
    brand : str
        Brand identifier (e.g. "minimal").
    template : str
        Template name used for this generation.
    audience : str
        Audience hint (e.g. "investors", "board").
    goal : str
        Goal string passed by the user.
    deck_id : str
        Optional user-assigned deck identifier for tracking across sessions.
    mode : str
        Intelligence mode: "llm", "rules", or "advised".
    """
    ctx = SessionContext(
        brand=brand,
        template=template,
        audience=audience,
        goal=goal,
        deck_id=deck_id,
        mode=mode,
    )

    start_ts = time.monotonic()

    try:
        yield ctx
    except Exception:
        # Re-raise — never swallow errors from the caller
        raise
    finally:
        # Always attempt to persist, even if an exception occurred
        _persist_session(ctx, start_ts)


def _persist_session(ctx: SessionContext, start_ts: float) -> None:
    """Write session + slide choices to the store. Fully fail-safe."""
    try:
        from inkline.learning.store import GenerationSession, SlideChoice, get_store

        store = get_store()
        if not store._enabled:  # noqa: SLF001
            return

        duration_ms = int((time.monotonic() - start_ts) * 1000)

        session = GenerationSession(
            brand=ctx.brand,
            template=ctx.template,
            audience=ctx.audience,
            goal=ctx.goal,
            section_count=0,  # Not easily derivable here; caller may set via ctx
            slide_count=len(ctx._slides),
            quality_score=ctx._quality_score,
            quality_grade=ctx._quality_grade,
            anti_pattern_hits=ctx._anti_pattern_hits,
            dm_rules_used=ctx._dm_rules_used,
            mode=ctx.mode,
            deck_id=ctx.deck_id,
        )
        session_id = store.record_session(session)
        ctx.session_id = session_id

        # Record individual slide choices
        for idx, slide in enumerate(ctx._slides):
            stype = slide.get("slide_type", "")
            if not stype:
                continue
            data = slide.get("data", {})
            title = data.get("title", data.get("company", ""))
            has_chart = int(bool(
                data.get("image_path") or data.get("chart_request") or data.get("charts")
            ))
            choice = SlideChoice(
                session_id=session_id,
                slide_index=idx,
                slide_type=stype,
                section_type=data.get("section", ""),
                title_length=len(title),
                has_chart=has_chart,
            )
            store.record_slide_choice(choice)

        log.debug(
            "LearningStore: session %s recorded (%d slides, %dms)",
            session_id[:8], len(ctx._slides), duration_ms,
        )

        # Trigger incremental extraction after every 10th session for this brand
        _maybe_trigger_extraction(ctx.brand, store)

    except Exception as exc:
        log.warning("LearningStore: failed to persist session (generation unaffected): %s", exc)


def _maybe_trigger_extraction(brand: str, store) -> None:
    """After every 10th session for a brand, run incremental extraction."""
    try:
        with store._connect() as conn:  # noqa: SLF001
            count = conn.execute(
                "SELECT COUNT(*) FROM generation_sessions WHERE brand=?", (brand,)
            ).fetchone()[0]
        if count % 10 == 0:
            import threading
            def _run():
                try:
                    from inkline.learning.extractor import PatternExtractor
                    extractor = PatternExtractor(store)
                    report = extractor.run(brand=brand)
                    log.info("LearningStore: incremental extraction complete — %s", report.summary)
                except Exception as exc:
                    log.debug("LearningStore: incremental extraction skipped: %s", exc)
            threading.Thread(target=_run, daemon=True).start()
    except Exception:
        pass
