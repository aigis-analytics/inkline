"""Learning store — SQLite signal store for Inkline generation sessions.

Follows XDG conventions: data lives in ~/.local/share/inkline/learning/sessions.db
Override location via INKLINE_LEARNING_DIR environment variable.

Thread-safe: each call opens a short-lived connection with WAL mode enabled.

To disable all learning entirely, set INKLINE_LEARNING_ENABLED=false.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def _default_db_path() -> Path:
    base_env = os.environ.get("INKLINE_LEARNING_DIR", "")
    if base_env:
        base = Path(base_env)
    else:
        base = Path("~/.local/share/inkline/learning").expanduser()
    return base / "sessions.db"


# ---------------------------------------------------------------------------
# Dataclasses (schema mirrors)
# ---------------------------------------------------------------------------

@dataclass
class GenerationSession:
    brand: str
    template: str = ""
    audience: str = ""
    goal: str = ""
    section_count: int = 0
    slide_count: int = 0
    quality_score: int = 0
    quality_grade: str = ""
    anti_pattern_hits: list[str] = field(default_factory=list)
    dm_rules_used: list[str] = field(default_factory=list)
    mode: str = "llm"
    deck_id: str = ""
    accepted: int = 0
    replaced: int = 0
    regen_count: int = 0
    # Auto-assigned on insert
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class SlideChoice:
    session_id: str
    slide_index: int
    slide_type: str
    section_type: str = ""
    dm_rule_id: str = ""
    data_structure: str = ""
    message_type: str = ""
    title_length: int = 0
    has_chart: int = 0
    accepted: int = 1
    regen_count: int = 0


@dataclass
class TitleRewrite:
    brand: str
    original_title: str
    rewritten_title: str
    session_id: str = ""
    slide_index: int = -1
    section_type: str = ""
    rewrite_source: str = "implicit"
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS generation_sessions (
    session_id        TEXT PRIMARY KEY,
    ts                TEXT NOT NULL,
    brand             TEXT NOT NULL,
    template          TEXT,
    audience          TEXT,
    goal              TEXT,
    section_count     INTEGER,
    slide_count       INTEGER,
    quality_score     INTEGER,
    quality_grade     TEXT,
    anti_pattern_hits TEXT,
    dm_rules_used     TEXT,
    mode              TEXT DEFAULT 'llm',
    deck_id           TEXT,
    accepted          INTEGER DEFAULT 0,
    replaced          INTEGER DEFAULT 0,
    regen_count       INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS slide_choices (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id        TEXT NOT NULL REFERENCES generation_sessions(session_id),
    slide_index       INTEGER NOT NULL,
    slide_type        TEXT NOT NULL,
    section_type      TEXT,
    dm_rule_id        TEXT,
    data_structure    TEXT,
    message_type      TEXT,
    title_length      INTEGER,
    has_chart         INTEGER DEFAULT 0,
    accepted          INTEGER DEFAULT 1,
    regen_count       INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS title_rewrites (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                TEXT NOT NULL,
    brand             TEXT NOT NULL,
    session_id        TEXT,
    slide_index       INTEGER,
    section_type      TEXT,
    original_title    TEXT NOT NULL,
    rewritten_title   TEXT NOT NULL,
    rewrite_source    TEXT DEFAULT 'implicit'
);

CREATE TABLE IF NOT EXISTS regen_counts (
    brand             TEXT NOT NULL,
    slide_type        TEXT NOT NULL,
    section_type      TEXT NOT NULL DEFAULT '',
    total_uses        INTEGER DEFAULT 0,
    total_regens      INTEGER DEFAULT 0,
    regen_rate        REAL DEFAULT 0.0,
    last_updated      TEXT,
    PRIMARY KEY (brand, slide_type, section_type)
);
"""

_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# LearningStore
# ---------------------------------------------------------------------------

class LearningStore:
    """Thread-safe SQLite store for generation signals."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or _default_db_path()
        self._enabled = os.environ.get("INKLINE_LEARNING_ENABLED", "true").lower() not in (
            "0", "false", "no", "off"
        )
        if self._enabled:
            self._init_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as conn:
                conn.executescript(_DDL)
                conn.commit()
        except Exception as exc:
            log.warning("LearningStore: failed to initialise DB at %s: %s", self._db_path, exc)
            self._enabled = False

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(str(self._db_path), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Public write API
    # ------------------------------------------------------------------

    def record_session(self, session: GenerationSession) -> str:
        """Record a deck generation session. Returns session_id."""
        if not self._enabled:
            return session.session_id
        try:
            with _LOCK, self._connect() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO generation_sessions
                       (session_id, ts, brand, template, audience, goal,
                        section_count, slide_count, quality_score, quality_grade,
                        anti_pattern_hits, dm_rules_used, mode, deck_id,
                        accepted, replaced, regen_count)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        session.session_id, session.ts, session.brand,
                        session.template, session.audience, session.goal,
                        session.section_count, session.slide_count,
                        session.quality_score, session.quality_grade,
                        json.dumps(session.anti_pattern_hits),
                        json.dumps(session.dm_rules_used),
                        session.mode, session.deck_id,
                        session.accepted, session.replaced, session.regen_count,
                    ),
                )
                conn.commit()
        except Exception as exc:
            log.warning("LearningStore.record_session failed: %s", exc)
        return session.session_id

    def record_slide_choice(self, choice: SlideChoice) -> None:
        """Record one slide's type choice within a session."""
        if not self._enabled:
            return
        try:
            with _LOCK, self._connect() as conn:
                conn.execute(
                    """INSERT INTO slide_choices
                       (session_id, slide_index, slide_type, section_type,
                        dm_rule_id, data_structure, message_type,
                        title_length, has_chart, accepted, regen_count)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        choice.session_id, choice.slide_index, choice.slide_type,
                        choice.section_type, choice.dm_rule_id,
                        choice.data_structure, choice.message_type,
                        choice.title_length, choice.has_chart,
                        choice.accepted, choice.regen_count,
                    ),
                )
                conn.commit()
        except Exception as exc:
            log.warning("LearningStore.record_slide_choice failed: %s", exc)

    def record_title_rewrite(self, rewrite: TitleRewrite) -> None:
        """Record a title rewrite event."""
        if not self._enabled:
            return
        try:
            with _LOCK, self._connect() as conn:
                conn.execute(
                    """INSERT INTO title_rewrites
                       (ts, brand, session_id, slide_index, section_type,
                        original_title, rewritten_title, rewrite_source)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (
                        rewrite.ts, rewrite.brand, rewrite.session_id,
                        rewrite.slide_index, rewrite.section_type,
                        rewrite.original_title, rewrite.rewritten_title,
                        rewrite.rewrite_source,
                    ),
                )
                conn.commit()
        except Exception as exc:
            log.warning("LearningStore.record_title_rewrite failed: %s", exc)

    def update_regen_count(
        self,
        brand: str,
        slide_type: str,
        section_type: str,
        was_regen: bool,
    ) -> None:
        """Increment usage and optionally regen count for a (brand, slide_type, section_type) tuple."""
        if not self._enabled:
            return
        try:
            now = datetime.now(timezone.utc).isoformat()
            with _LOCK, self._connect() as conn:
                conn.execute(
                    """INSERT INTO regen_counts
                       (brand, slide_type, section_type, total_uses, total_regens,
                        regen_rate, last_updated)
                       VALUES (?,?,?,1,?,?,?)
                       ON CONFLICT(brand, slide_type, section_type) DO UPDATE SET
                         total_uses   = total_uses + 1,
                         total_regens = total_regens + excluded.total_regens,
                         regen_rate   = CAST(total_regens + excluded.total_regens AS REAL)
                                        / CAST(total_uses + 1 AS REAL),
                         last_updated = excluded.last_updated""",
                    (
                        brand, slide_type, section_type or "",
                        1 if was_regen else 0,
                        1.0 if was_regen else 0.0,
                        now,
                    ),
                )
                conn.commit()
        except Exception as exc:
            log.warning("LearningStore.update_regen_count failed: %s", exc)

    # ------------------------------------------------------------------
    # Public read API
    # ------------------------------------------------------------------

    def get_high_regen_combos(
        self,
        brand: str,
        min_rate: float = 0.4,
        min_uses: int = 5,
    ) -> list[dict]:
        """Return (slide_type, section_type) pairs with high regen rates."""
        if not self._enabled:
            return []
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """SELECT slide_type, section_type, total_uses, total_regens, regen_rate
                       FROM regen_counts
                       WHERE brand=? AND regen_rate>=? AND total_uses>=?
                       ORDER BY regen_rate DESC""",
                    (brand, min_rate, min_uses),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception as exc:
            log.warning("LearningStore.get_high_regen_combos failed: %s", exc)
            return []

    def get_audience_layout_stats(self, brand: str, audience: str) -> dict[str, dict]:
        """Return slide type distribution for a brand + audience combination."""
        if not self._enabled:
            return {}
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """SELECT sc.section_type, sc.slide_type,
                              COUNT(*) as uses,
                              SUM(sc.accepted) as accepted_count
                       FROM slide_choices sc
                       JOIN generation_sessions gs ON sc.session_id = gs.session_id
                       WHERE gs.brand=? AND gs.audience=?
                       GROUP BY sc.section_type, sc.slide_type
                       ORDER BY uses DESC""",
                    (brand, audience),
                ).fetchall()
            result: dict[str, dict] = {}
            for r in rows:
                sec = r["section_type"] or ""
                if sec not in result:
                    result[sec] = {}
                result[sec][r["slide_type"]] = {
                    "uses": r["uses"],
                    "accepted": r["accepted_count"],
                    "acceptance_rate": round(r["accepted_count"] / r["uses"], 2) if r["uses"] else 0.0,
                }
            return result
        except Exception as exc:
            log.warning("LearningStore.get_audience_layout_stats failed: %s", exc)
            return {}

    def get_section_type_preferences(
        self,
        brand: str,
        section_type: str,
        audience: str | None = None,
    ) -> list[str]:
        """Return slide types ordered by acceptance rate for a section type."""
        if not self._enabled:
            return []
        try:
            params: list[Any] = [brand, section_type]
            audience_clause = ""
            if audience:
                audience_clause = "AND gs.audience=?"
                params.append(audience)
            with self._connect() as conn:
                rows = conn.execute(
                    f"""SELECT sc.slide_type,
                               COUNT(*) as uses,
                               SUM(sc.accepted) as accepted_count,
                               CAST(SUM(sc.accepted) AS REAL) / COUNT(*) as rate
                        FROM slide_choices sc
                        JOIN generation_sessions gs ON sc.session_id = gs.session_id
                        WHERE gs.brand=? AND sc.section_type=? {audience_clause}
                        GROUP BY sc.slide_type
                        HAVING uses >= 3
                        ORDER BY rate DESC, uses DESC""",
                    params,
                ).fetchall()
            return [r["slide_type"] for r in rows]
        except Exception as exc:
            log.warning("LearningStore.get_section_type_preferences failed: %s", exc)
            return []

    def get_audience_layout_prefs(self, brand: str, audience: str) -> str:
        """Format audience-specific layout preferences for prompt injection.

        Returns an empty string when fewer than 3 data points exist.
        """
        if not self._enabled:
            return ""
        stats = self.get_audience_layout_stats(brand, audience)
        if not stats:
            return ""

        lines = [
            f"AUDIENCE LAYOUT PREFERENCES (brand={brand}, audience={audience})",
            "-" * 60,
        ]
        any_data = False
        for section_type, slide_data in sorted(stats.items()):
            best = max(slide_data.items(), key=lambda kv: kv[1]["acceptance_rate"])
            st, info = best
            if info["uses"] < 3:
                continue
            any_data = True
            lines.append(
                f"  {section_type or '(generic)'} -> {st} preferred "
                f"({int(info['acceptance_rate'] * 100)}% acceptance, {info['uses']} uses)"
            )

        if not any_data:
            return ""
        return "\n".join(lines)

    def get_session_stats(self, brand: str, days: int = 30) -> dict:
        """Return summary statistics for CLI/privacy command."""
        if not self._enabled:
            return {"enabled": False}
        try:
            cutoff = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            import datetime as dt_mod
            cutoff -= dt_mod.timedelta(days=days)
            cutoff_str = cutoff.isoformat()
            with self._connect() as conn:
                total_sessions = conn.execute(
                    "SELECT COUNT(*) FROM generation_sessions WHERE brand=? AND ts>=?",
                    (brand, cutoff_str),
                ).fetchone()[0]
                total_rewrites = conn.execute(
                    "SELECT COUNT(*) FROM title_rewrites WHERE brand=? AND ts>=?",
                    (brand, cutoff_str),
                ).fetchone()[0]
                total_slide_choices = conn.execute(
                    """SELECT COUNT(*) FROM slide_choices sc
                       JOIN generation_sessions gs ON sc.session_id=gs.session_id
                       WHERE gs.brand=? AND gs.ts>=?""",
                    (brand, cutoff_str),
                ).fetchone()[0]
            return {
                "enabled": True,
                "brand": brand,
                "days": days,
                "sessions": total_sessions,
                "title_rewrites": total_rewrites,
                "slide_choices": total_slide_choices,
                "db_path": str(self._db_path),
            }
        except Exception as exc:
            log.warning("LearningStore.get_session_stats failed: %s", exc)
            return {"enabled": True, "error": str(exc)}

    def get_title_rewrites(self, brand: str, min_obs: int = 3) -> list[dict]:
        """Fetch title rewrite pairs for pattern extraction."""
        if not self._enabled:
            return []
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """SELECT section_type, original_title, rewritten_title
                       FROM title_rewrites
                       WHERE brand=?
                       ORDER BY ts""",
                    (brand,),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception as exc:
            log.warning("LearningStore.get_title_rewrites failed: %s", exc)
            return []


# ---------------------------------------------------------------------------
# Module-level singleton (lazy-init)
# ---------------------------------------------------------------------------

_store_instance: LearningStore | None = None
_store_lock = threading.Lock()


def get_store(db_path: Path | None = None) -> LearningStore:
    """Return the module-level LearningStore singleton."""
    global _store_instance
    with _store_lock:
        if _store_instance is None:
            _store_instance = LearningStore(db_path)
    return _store_instance
