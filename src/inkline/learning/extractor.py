"""Pattern extraction pipeline for Inkline self-learning.

Reads accumulated signals from sessions.db and writes learned patterns back
to the existing YAML pattern stores (pattern_memory.py, anti_patterns.py).

Run modes:
- Nightly: ``inkline learn --nightly`` or ``0 2 * * * inkline learn --nightly``
- Manual: ``inkline learn --brand minimal``
- Auto: triggered by session_context after every 10th generation session

All extraction is batch and statistical — no ML, no model weights.
Patterns are written with confidence 0.5 and promoted by subsequent acceptance.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from inkline.learning.store import LearningStore

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Report dataclass
# ---------------------------------------------------------------------------

@dataclass
class ExtractionReport:
    brands_processed: list[str] = field(default_factory=list)
    patterns_added: int = 0
    patterns_updated: int = 0
    dm_rules_updated: int = 0
    anti_patterns_promoted: int = 0
    title_patterns_extracted: int = 0
    audience_prefs_updated: int = 0

    @property
    def summary(self) -> str:
        return (
            f"Brands: {len(self.brands_processed)} | "
            f"Patterns added: {self.patterns_added} | "
            f"Updated: {self.patterns_updated} | "
            f"Anti-patterns promoted: {self.anti_patterns_promoted} | "
            f"Title patterns: {self.title_patterns_extracted} | "
            f"Audience prefs: {self.audience_prefs_updated}"
        )


# ---------------------------------------------------------------------------
# PatternExtractor
# ---------------------------------------------------------------------------

class PatternExtractor:
    """Extracts learnable patterns from the generation session store."""

    def __init__(self, store: "LearningStore") -> None:
        self.store = store

    def run(self, brand: str | None = None) -> ExtractionReport:
        """Run the full extraction pass. Returns a summary report."""
        report = ExtractionReport()

        if not self.store._enabled:  # noqa: SLF001
            log.debug("PatternExtractor: store disabled, skipping")
            return report

        brands_to_process: list[str] = []
        if brand:
            brands_to_process = [brand]
        else:
            try:
                with self.store._connect() as conn:  # noqa: SLF001
                    rows = conn.execute(
                        "SELECT DISTINCT brand FROM generation_sessions"
                    ).fetchall()
                brands_to_process = [r[0] for r in rows]
            except Exception as exc:
                log.warning("PatternExtractor: could not enumerate brands: %s", exc)
                return report

        for b in brands_to_process:
            try:
                self._process_brand(b, report)
                report.brands_processed.append(b)
            except Exception as exc:
                log.warning("PatternExtractor: error processing brand '%s': %s", b, exc)

        return report

    def _process_brand(self, brand: str, report: ExtractionReport) -> None:
        """Run all extraction passes for a single brand."""
        anti_patterns = self._extract_regen_anti_patterns(brand)
        for ap in anti_patterns:
            if self._write_anti_pattern(brand, ap):
                report.anti_patterns_promoted += 1

        title_patterns = self._extract_title_rewrite_patterns(brand)
        for tp in title_patterns:
            if self._write_pattern(brand, tp):
                report.title_patterns_extracted += 1

        audience_prefs = self._extract_audience_prefs(brand)
        if audience_prefs:
            report.audience_prefs_updated += len(audience_prefs)

        quality_trends = self._extract_quality_score_trends(brand)
        for qt in quality_trends:
            if self._write_anti_pattern(brand, qt):
                report.anti_patterns_promoted += 1

    # ------------------------------------------------------------------
    # Regen anti-pattern extraction
    # ------------------------------------------------------------------

    def _extract_regen_anti_patterns(self, brand: str) -> list[dict]:
        """Return anti-patterns derived from high-regen-rate combos."""
        combos = self.store.get_high_regen_combos(brand, min_rate=0.4, min_uses=5)
        results = []
        for combo in combos:
            slide_type = combo["slide_type"]
            section_type = combo["section_type"] or "content"
            regen_pct = int(combo["regen_rate"] * 100)
            results.append({
                "category": "anti_pattern",
                "rule": (
                    f"Avoid {slide_type} for {section_type} content "
                    f"(regen rate: {regen_pct}%)"
                ),
                "slide_type": slide_type,
                "section_type": section_type,
                "confidence": 0.70,
                "source": "regen_rate_analysis",
                "regen_rate": combo["regen_rate"],
            })
        return results

    # ------------------------------------------------------------------
    # Title rewrite pattern extraction
    # ------------------------------------------------------------------

    def _extract_title_rewrite_patterns(self, brand: str) -> list[dict]:
        """Analyse title rewrites to extract learnable naming patterns."""
        rewrites = self.store.get_title_rewrites(brand, min_obs=3)
        if not rewrites:
            return []

        # Group by section_type
        by_section: dict[str, list[tuple[str, str]]] = {}
        for rw in rewrites:
            sec = rw.get("section_type") or "generic"
            pair = (rw["original_title"], rw["rewritten_title"])
            by_section.setdefault(sec, []).append(pair)

        patterns = []
        for section_type, pairs in by_section.items():
            if len(pairs) < 3:
                continue
            patterns.extend(self._analyse_rewrite_pairs(section_type, pairs))

        return patterns

    def _analyse_rewrite_pairs(
        self, section_type: str, pairs: list[tuple[str, str]]
    ) -> list[dict]:
        """Detect structural patterns across before/after title pairs."""
        results = []
        n = len(pairs)

        # Pattern 1: specificity — rewritten titles contain numbers/percentages
        _number_re = re.compile(r"\d[\d,.]*%?|\$[\d,.]+")
        specificity_hits = sum(
            1 for orig, rewr in pairs
            if _number_re.search(rewr) and not _number_re.search(orig)
        )
        if specificity_hits >= max(3, int(n * 0.5)):
            confidence = min(0.5 + 0.05 * specificity_hits, 0.85)
            results.append({
                "category": "title",
                "rule": (
                    f"Action titles for {section_type} should include "
                    f"a specific number or metric"
                ),
                "section_type": section_type,
                "confidence": round(confidence, 2),
                "source": "title_rewrite_analysis",
                "observations": specificity_hits,
            })

        # Pattern 2: verb-first — rewritten titles start with a verb
        _verb_starts = {
            "show", "prove", "deliver", "achieve", "drive", "grow", "reduce",
            "increase", "double", "triple", "cut", "save", "generate", "reach",
            "hit", "exceed", "outperform", "capture", "build", "launch",
        }
        verb_hits = sum(
            1 for orig, rewr in pairs
            if rewr.split()[0].lower().rstrip("s") in _verb_starts
            and not (orig.split()[0].lower().rstrip("s") in _verb_starts)
        )
        if verb_hits >= max(3, int(n * 0.5)):
            confidence = min(0.5 + 0.05 * verb_hits, 0.85)
            results.append({
                "category": "title",
                "rule": (
                    f"Action titles for {section_type} should start "
                    f"with an active verb"
                ),
                "section_type": section_type,
                "confidence": round(confidence, 2),
                "source": "title_rewrite_analysis",
                "observations": verb_hits,
            })

        # Pattern 3: length — rewritten titles consistently shorter
        lengths_orig = [len(orig) for orig, _ in pairs]
        lengths_rewr = [len(rewr) for _, rewr in pairs]
        avg_orig = sum(lengths_orig) / len(lengths_orig)
        avg_rewr = sum(lengths_rewr) / len(lengths_rewr)
        shorter_hits = sum(1 for o, r in zip(lengths_orig, lengths_rewr) if r < o)
        if shorter_hits >= max(3, int(n * 0.6)) and avg_rewr < avg_orig * 0.75:
            target_len = int(avg_rewr * 1.2)  # 20% buffer above average rewritten length
            results.append({
                "category": "title",
                "rule": (
                    f"Titles for {section_type} should be "
                    f"<= {target_len} characters"
                ),
                "section_type": section_type,
                "confidence": 0.55,
                "source": "title_rewrite_analysis",
                "observations": shorter_hits,
            })

        return results

    # ------------------------------------------------------------------
    # Audience preference extraction
    # ------------------------------------------------------------------

    def _extract_audience_prefs(self, brand: str) -> dict:
        """Build audience preference summary (for logging/reporting)."""
        try:
            with self.store._connect() as conn:  # noqa: SLF001
                rows = conn.execute(
                    """SELECT DISTINCT audience FROM generation_sessions
                       WHERE brand=? AND audience != ''""",
                    (brand,),
                ).fetchall()
            audiences = [r[0] for r in rows]
        except Exception:
            return {}

        prefs = {}
        for audience in audiences:
            stats = self.store.get_audience_layout_stats(brand, audience)
            if stats:
                prefs[audience] = stats
        return prefs

    # ------------------------------------------------------------------
    # Quality score trend extraction
    # ------------------------------------------------------------------

    def _extract_quality_score_trends(self, brand: str) -> list[dict]:
        """Detect anti-patterns from consistently low-quality sessions."""
        try:
            with self.store._connect() as conn:  # noqa: SLF001
                # Find slide types that appeared in >50% of low-score sessions
                low_score_sessions = conn.execute(
                    """SELECT session_id FROM generation_sessions
                       WHERE brand=? AND quality_score > 0 AND quality_score < 50""",
                    (brand,),
                ).fetchall()
                if len(low_score_sessions) < 3:
                    return []

                low_ids = [r[0] for r in low_score_sessions]
                placeholders = ",".join("?" * len(low_ids))
                rows = conn.execute(
                    f"""SELECT slide_type, COUNT(DISTINCT session_id) as session_count
                        FROM slide_choices
                        WHERE session_id IN ({placeholders})
                        GROUP BY slide_type
                        ORDER BY session_count DESC""",
                    low_ids,
                ).fetchall()
        except Exception as exc:
            log.debug("PatternExtractor._extract_quality_score_trends: %s", exc)
            return []

        results = []
        threshold = len(low_score_sessions) * 0.5
        for row in rows:
            if row["session_count"] >= threshold:
                results.append({
                    "category": "anti_pattern",
                    "rule": (
                        f"Overuse of {row['slide_type']} correlates with "
                        f"low quality scores"
                    ),
                    "slide_type": row["slide_type"],
                    "confidence": 0.60,
                    "source": "quality_score_analysis",
                })
        return results

    # ------------------------------------------------------------------
    # Writers
    # ------------------------------------------------------------------

    def _write_anti_pattern(self, brand: str, pattern: dict) -> bool:
        """Write a learned anti-pattern into pattern_memory for this brand."""
        try:
            from inkline.intelligence.pattern_memory import (
                load_brand_patterns,
                save_brand_patterns,
                add_pattern,
            )
            rule_text = pattern["rule"]
            # Use add_pattern which handles deduplication internally
            add_pattern(
                brand,
                category=pattern.get("category", "anti_pattern"),
                rule=rule_text,
                confidence=pattern.get("confidence", 0.60),
                source=pattern.get("source", "extractor"),
            )
            return True
        except Exception as exc:
            log.debug("PatternExtractor._write_anti_pattern: %s", exc)
            return False

    def _write_pattern(self, brand: str, pattern: dict) -> bool:
        """Write a learned pattern (e.g. title rule) into pattern_memory."""
        try:
            from inkline.intelligence.pattern_memory import add_pattern
            rule_text = pattern["rule"]
            add_pattern(
                brand,
                category=pattern.get("category", "title"),
                rule=rule_text,
                confidence=pattern.get("confidence", 0.50),
                source=pattern.get("source", "extractor"),
            )
            return True
        except Exception as exc:
            log.debug("PatternExtractor._write_pattern: %s", exc)
            return False


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------

def run_nightly_extraction(brand: str | None = None) -> ExtractionReport:
    """Top-level entry point for nightly extraction.

    Can be wired to cron::

        0 2 * * * inkline learn --nightly

    Or called directly from any scheduler.
    """
    try:
        from inkline.learning.store import get_store
        store = get_store()
        extractor = PatternExtractor(store)
        report = extractor.run(brand=brand)
        log.info("Nightly extraction complete: %s", report.summary)
        return report
    except Exception as exc:
        log.warning("run_nightly_extraction failed: %s", exc)
        return ExtractionReport()
