"""Federated community pattern sharing for Inkline.

Opt-out community sharing of safe structural signals (no brand names, no titles,
no content). All sharing is one-way export; there is no server-side sync.

Privacy hard boundary: brand names, titles, goal strings, and content NEVER
appear in export_pattern_delta() output, regardless of configuration.

Configuration: ~/.config/inkline/learning_config.yaml

    federation:
      enabled: true               # master opt-out switch
      export_dm_rules: true       # DM rule acceptance rates (no content)
      export_anti_patterns: true  # Anti-pattern hit rates (no content)
      export_brand_patterns: false  # NOT recommended
      community_endpoint: ""      # POST target (future)
      use_community_starter_patterns: true

To disable all outbound sharing::

    inkline privacy --disable
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config path
# ---------------------------------------------------------------------------

_CONFIG_DIR = Path("~/.config/inkline").expanduser()
_LEARNING_CONFIG = _CONFIG_DIR / "learning_config.yaml"

_DEFAULT_CONFIG: dict[str, Any] = {
    "implicit_acceptance_nudge": 0.005,
    "explicit_acceptance_nudge": 0.01,
    "implicit_acceptance_window_hours": 24,
    "implicit_learning_enabled": True,
    "federation": {
        "enabled": True,
        "export_dm_rules": True,
        "export_anti_patterns": True,
        "export_brand_patterns": False,
        "community_endpoint": "",
        "use_community_starter_patterns": True,
    },
}

SCHEMA_VERSION = "1.0"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class FederationDisabledError(RuntimeError):
    """Raised when export is attempted but federation.enabled=false."""


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def load_learning_config() -> dict[str, Any]:
    """Load learning config, falling back to defaults."""
    try:
        import yaml  # type: ignore[import-untyped]
        if _LEARNING_CONFIG.exists():
            with _LEARNING_CONFIG.open() as f:
                loaded = yaml.safe_load(f) or {}
            # Deep-merge with defaults
            result = dict(_DEFAULT_CONFIG)
            result.update(loaded)
            if "federation" in loaded:
                merged_fed = dict(_DEFAULT_CONFIG["federation"])
                merged_fed.update(loaded["federation"])
                result["federation"] = merged_fed
            return result
    except ImportError:
        pass
    except Exception as exc:
        log.debug("federation: could not load learning_config.yaml: %s", exc)
    return dict(_DEFAULT_CONFIG)


def save_learning_config(config: dict[str, Any]) -> None:
    """Persist learning config to disk."""
    try:
        import yaml  # type: ignore[import-untyped]
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with _LEARNING_CONFIG.open("w") as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
    except ImportError:
        # yaml not installed — write minimal JSON fallback
        _LEARNING_CONFIG.with_suffix(".json").write_text(json.dumps(config, indent=2))
    except Exception as exc:
        log.warning("federation: could not save learning_config.yaml: %s", exc)


def set_federation_enabled(enabled: bool) -> None:
    """Enable or disable federation in the persisted config."""
    cfg = load_learning_config()
    if "federation" not in cfg:
        cfg["federation"] = dict(_DEFAULT_CONFIG["federation"])
    cfg["federation"]["enabled"] = enabled
    save_learning_config(cfg)
    log.info("Federation %s", "enabled" if enabled else "disabled")


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_pattern_delta(
    since: datetime,
    include_dm_rules: bool = True,
    include_anti_patterns: bool = False,
    dry_run: bool = False,
) -> dict:
    """Export an anonymised pattern delta for community sharing.

    The delta contains ONLY:
    - DM rule acceptance rates by (data_structure, message_type) — no brand
    - Anti-pattern hit frequencies — no brand, no content
    - Quality score trend (improving/stable/degrading) — no details
    - Software version and schema version

    No brand names, no titles, no content, no audience strings.

    Parameters
    ----------
    since : datetime
        Only include data recorded after this timestamp.
    include_dm_rules : bool
        Include DM rule structural rates (default True).
    include_anti_patterns : bool
        Include anti-pattern hit counts (default False).
    dry_run : bool
        If True, return the delta dict without posting to any endpoint.

    Returns
    -------
    dict
        The anonymised delta. Brand names are replaced with numeric hashes.

    Raises
    ------
    FederationDisabledError
        When federation.enabled is False in the config.
    """
    cfg = load_learning_config()
    fed = cfg.get("federation", {})

    if not fed.get("enabled", True):
        raise FederationDisabledError(
            "Federation is disabled. Run 'inkline privacy --enable' to re-enable."
        )

    since_str = since.isoformat() if since.tzinfo else since.replace(tzinfo=timezone.utc).isoformat()

    try:
        from inkline import __version__ as inkline_version
    except Exception:
        inkline_version = "unknown"

    delta: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "inkline_version": inkline_version,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "since": since_str,
    }

    try:
        from inkline.learning.store import get_store
        store = get_store()

        if include_dm_rules and fed.get("export_dm_rules", True):
            delta["dm_rule_rates"] = _export_dm_rule_rates(store, since_str)

        if include_anti_patterns and fed.get("export_anti_patterns", True):
            delta["anti_pattern_rates"] = _export_anti_pattern_rates(store, since_str)

        delta["quality_trend"] = _export_quality_trend(store, since_str)

    except Exception as exc:
        log.warning("federation.export_pattern_delta: store query failed: %s", exc)
        delta["error"] = f"Partial export: {exc}"

    if not dry_run:
        endpoint = fed.get("community_endpoint", "")
        if endpoint:
            _post_to_endpoint(endpoint, delta)
        else:
            log.info("federation: no community_endpoint configured — delta not posted")

    return delta


def _export_dm_rule_rates(store, since_str: str) -> list[dict]:
    """Export DM rule structural rates — NO brand names, NO content."""
    # We derive structural rates from slide_choices:
    # group by (data_structure, message_type) — these are generic axis labels
    try:
        with store._connect() as conn:  # noqa: SLF001
            rows = conn.execute(
                """SELECT sc.data_structure, sc.message_type,
                          COUNT(*) as uses,
                          SUM(sc.accepted) as accepted_count
                   FROM slide_choices sc
                   JOIN generation_sessions gs ON sc.session_id=gs.session_id
                   WHERE gs.ts >= ?
                     AND sc.data_structure != ''
                   GROUP BY sc.data_structure, sc.message_type
                   HAVING uses >= 3""",
                (since_str,),
            ).fetchall()
        return [
            {
                "data_structure": r["data_structure"],
                "message_type": r["message_type"] or "",
                "uses": r["uses"],
                "acceptance_rate": round(r["accepted_count"] / r["uses"], 3) if r["uses"] else 0.0,
            }
            for r in rows
        ]
    except Exception as exc:
        log.debug("_export_dm_rule_rates failed: %s", exc)
        return []


def _export_anti_pattern_rates(store, since_str: str) -> list[dict]:
    """Export anti-pattern hit counts — NO brand names, NO content."""
    try:
        with store._connect() as conn:  # noqa: SLF001
            rows = conn.execute(
                """SELECT anti_pattern_hits FROM generation_sessions
                   WHERE ts >= ? AND anti_pattern_hits != '[]' AND anti_pattern_hits != ''""",
                (since_str,),
            ).fetchall()

        # Tally hit counts per rule_id
        hit_counts: dict[str, int] = {}
        for row in rows:
            try:
                hits = json.loads(row[0])
                for h in hits:
                    rule_id = str(h)
                    # Only export alphanumeric rule IDs (e.g. "LP-01") — no content
                    if _is_safe_rule_id(rule_id):
                        hit_counts[rule_id] = hit_counts.get(rule_id, 0) + 1
            except Exception:
                continue

        return [
            {"rule_id": k, "hits": v}
            for k, v in sorted(hit_counts.items(), key=lambda kv: -kv[1])
        ]
    except Exception as exc:
        log.debug("_export_anti_pattern_rates failed: %s", exc)
        return []


def _export_quality_trend(store, since_str: str) -> str:
    """Return "improving", "stable", or "degrading" — no details."""
    try:
        with store._connect() as conn:  # noqa: SLF001
            rows = conn.execute(
                """SELECT quality_score FROM generation_sessions
                   WHERE ts >= ? AND quality_score > 0
                   ORDER BY ts""",
                (since_str,),
            ).fetchall()
        scores = [r[0] for r in rows]
        if len(scores) < 4:
            return "insufficient_data"
        mid = len(scores) // 2
        first_half_avg = sum(scores[:mid]) / mid
        second_half_avg = sum(scores[mid:]) / (len(scores) - mid)
        diff = second_half_avg - first_half_avg
        if diff > 2:
            return "improving"
        if diff < -2:
            return "degrading"
        return "stable"
    except Exception:
        return "unknown"


def _is_safe_rule_id(rule_id: str) -> bool:
    """Rule IDs like 'LP-01', 'DM-001' are safe. Free-text is not."""
    import re
    return bool(re.fullmatch(r"[A-Z]{1,4}-[A-Z0-9]{1,6}", rule_id))


def _post_to_endpoint(endpoint: str, delta: dict) -> None:
    """POST the delta to the community endpoint."""
    try:
        import urllib.request
        data = json.dumps(delta).encode()
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            log.info("federation: posted to %s — status %d", endpoint, resp.status)
    except Exception as exc:
        log.warning("federation: POST to %s failed (non-fatal): %s", endpoint, exc)


# ---------------------------------------------------------------------------
# Privacy summary
# ---------------------------------------------------------------------------

def get_privacy_summary(brand: str = "") -> str:
    """Return a human-readable summary of stored data and federation status."""
    cfg = load_learning_config()
    fed = cfg.get("federation", {})
    lines = [
        "Inkline Learning & Privacy Summary",
        "=" * 40,
        "",
        "DATA STORED LOCALLY",
        f"  Location: ~/.local/share/inkline/learning/sessions.db",
        f"  Generation sessions: yes (brand, template, audience, quality score)",
        f"  Slide type choices: yes (per-slide, per-session)",
        f"  Title rewrites: yes (before/after pairs)",
        f"  Regen counts: yes (per brand/slide_type/section_type)",
        "",
        "FEDERATION STATUS",
        f"  Master switch: {'ENABLED' if fed.get('enabled', True) else 'DISABLED'}",
        f"  Export DM rules: {fed.get('export_dm_rules', True)}",
        f"  Export anti-patterns: {fed.get('export_anti_patterns', True)}",
        f"  Export brand patterns: {fed.get('export_brand_patterns', False)}",
        f"  Community endpoint: {fed.get('community_endpoint', '(not configured)')}",
        "",
        "WHAT IS EXPORTED (when enabled)",
        "  - DM rule acceptance rates by (data_structure, message_type) — no brand names",
        "  - Anti-pattern hit counts by rule ID — no content",
        "  - Quality trend (improving/stable/degrading) — no details",
        "  - Software version",
        "",
        "WHAT IS NEVER EXPORTED",
        "  - Brand names",
        "  - Slide titles or content",
        "  - Goal and audience strings",
        "  - Pattern rule text",
        "",
        "To disable all outbound sharing:",
        "  inkline privacy --disable",
    ]

    if brand:
        try:
            from inkline.learning.store import get_store
            stats = get_store().get_session_stats(brand, days=30)
            lines += [
                "",
                f"RECENT ACTIVITY (last 30 days, brand={brand})",
                f"  Sessions: {stats.get('sessions', 0)}",
                f"  Title rewrites captured: {stats.get('title_rewrites', 0)}",
                f"  Slide choices recorded: {stats.get('slide_choices', 0)}",
            ]
        except Exception:
            pass

    return "\n".join(lines)
