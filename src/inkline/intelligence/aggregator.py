"""Decision matrix feedback aggregator.

Reads feedback_log.jsonl and updates confidence scores + observation counts
on decision matrix rules. Also promotes candidate rules and demotes
low-confidence active rules.

Usage::

    from inkline.intelligence.aggregator import Aggregator
    agg = Aggregator()
    report = agg.run_full_pass()     # process all unprocessed feedback
    print(report)

Or from CLI: ``inkline learn``
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

_CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "inkline"
FEEDBACK_LOG = _CONFIG_DIR / "feedback_log.jsonl"
DECISION_MATRIX_PATH = _CONFIG_DIR / "decision_matrix.yaml"
DEFAULT_MATRIX_PATH = Path(__file__).parent / "decision_matrix_default.yaml"

# Rule promotion threshold: accept at least 5 observations AND ≥70% acceptance
PROMOTE_MIN_OBS = 5
PROMOTE_MIN_RATE = 0.70

# Demotion threshold: at least 10 observations AND confidence < 40%
DEMOTE_MIN_OBS = 10
DEMOTE_MAX_CONF = 0.40


# ---------------------------------------------------------------------------
# YAML helpers
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        import yaml
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        import json as _j
        try:
            with open(path, encoding="utf-8") as f:
                return _j.load(f)
        except Exception:
            return {}


def _save_yaml(path: Path, data: dict) -> None:
    try:
        import yaml
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    except ImportError:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Decision matrix loader
# ---------------------------------------------------------------------------

def load_decision_matrix() -> dict:
    """Load the active decision matrix, falling back to bundled default."""
    if DECISION_MATRIX_PATH.exists():
        return _load_yaml(DECISION_MATRIX_PATH)
    # Bootstrap from bundled default
    dm = _load_yaml(DEFAULT_MATRIX_PATH)
    _save_yaml(DECISION_MATRIX_PATH, dm)
    return dm


def save_decision_matrix(dm: dict) -> None:
    dm["last_updated"] = datetime.now().isoformat()
    _save_yaml(DECISION_MATRIX_PATH, dm)


# ---------------------------------------------------------------------------
# Feedback log helpers
# ---------------------------------------------------------------------------

def append_feedback_event(event: dict) -> None:
    """Append a single feedback event to the log."""
    FEEDBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(FEEDBACK_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    log.info("Feedback recorded: action=%s rule=%s", event.get("action"), event.get("dm_rule_id"))


def read_feedback_log() -> list[dict]:
    """Return all events from the feedback log."""
    if not FEEDBACK_LOG.exists():
        return []
    events = []
    with open(FEEDBACK_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return events


# ---------------------------------------------------------------------------
# Core aggregation
# ---------------------------------------------------------------------------

class Aggregator:
    """Processes feedback events and updates the decision matrix."""

    def __init__(self) -> None:
        self._dm = load_decision_matrix()

    def process_event(self, event: dict) -> None:
        """Apply a single feedback event to the in-memory matrix."""
        rule_id = event.get("dm_rule_id")
        if not rule_id:
            return

        rule = self._find_rule(rule_id)
        if rule is None:
            # Could be a candidate rule proposed by a previous modification
            self._handle_new_rule_candidate(event)
            return

        rule["observations"] = rule.get("observations", 0) + 1
        action = event.get("action", "")

        if action == "accepted":
            rule["confidence"] = min(0.99, rule.get("confidence", 0.5) + 0.01)

        elif action == "rejected":
            rule["confidence"] = max(0.10, rule.get("confidence", 0.5) - 0.05)
            if rule["confidence"] < DEMOTE_MAX_CONF:
                rule["status"] = "flagged"
                log.warning("Rule %s flagged for review (confidence=%.2f)", rule_id, rule["confidence"])

        elif action == "modified":
            rule["confidence"] = max(0.10, rule.get("confidence", 0.5) - 0.03)
            modified_to = event.get("modified_to")
            if modified_to:
                self._propose_new_rule(
                    data_structure=event.get("data_structure", ""),
                    message_type=event.get("message_type", ""),
                    chart_type=modified_to,
                    enforce=event.get("enforce_overrides", {}),
                    source_event=event.get("event_id", ""),
                )

    def run_full_pass(self) -> str:
        """Process all feedback events from the log. Returns a summary report."""
        events = read_feedback_log()
        if not events:
            return "No feedback events found. Nothing to process."

        counts: dict[str, int] = {"accepted": 0, "rejected": 0, "modified": 0, "unknown": 0}
        for event in events:
            self.process_event(event)
            counts[event.get("action", "unknown")] = counts.get(event.get("action", "unknown"), 0) + 1

        # Promotion pass — promote candidates that meet thresholds
        promoted = self._promotion_pass()

        # Demotion pass — demote active rules with too-low confidence
        demoted = self._demotion_pass()

        save_decision_matrix(self._dm)

        lines = [
            f"Processed {len(events)} feedback events:",
            f"  Accepted: {counts.get('accepted', 0)}",
            f"  Rejected: {counts.get('rejected', 0)}",
            f"  Modified: {counts.get('modified', 0)}",
            f"  Promoted candidate → active: {len(promoted)}",
            f"  Demoted active → low_confidence: {len(demoted)}",
        ]
        if promoted:
            lines.append(f"  Promoted rules: {', '.join(r['id'] for r in promoted)}")
        if demoted:
            lines.append(f"  Demoted rules: {', '.join(r['id'] for r in demoted)}")
        return "\n".join(lines)

    def _find_rule(self, rule_id: str) -> dict | None:
        for rule in self._dm.get("rules", []):
            if rule.get("id") == rule_id:
                return rule
        return None

    def _handle_new_rule_candidate(self, event: dict) -> None:
        """Event references an unknown rule — might be a user-proposed candidate."""
        pass  # Future: look up in proposed_rules section

    def _propose_new_rule(
        self,
        data_structure: str,
        message_type: str,
        chart_type: str,
        enforce: dict,
        source_event: str,
    ) -> None:
        """Add a candidate rule to the matrix for future promotion."""
        if not data_structure or not message_type or not chart_type:
            return

        # Check if we already have a candidate for this (data_structure, message_type)
        for rule in self._dm.get("rules", []):
            if (rule.get("data_structure") == data_structure
                    and rule.get("message_type") == message_type
                    and rule.get("chart_type") == chart_type
                    and rule.get("status") == "candidate"):
                # Increment acceptance on the existing candidate
                rule["observations"] = rule.get("observations", 0) + 1
                rule["acceptance_count"] = rule.get("acceptance_count", 0) + 1
                log.info("Updated candidate rule for (%s, %s) → %s",
                         data_structure, message_type, chart_type)
                return

        # Create new candidate
        candidate_id = f"DM-C{len(self._dm.get('rules', [])) + 1:03d}"
        candidate = {
            "id": candidate_id,
            "data_structure": data_structure,
            "message_type": message_type,
            "density": "any",
            "chart_type": chart_type,
            "enforce": enforce,
            "confidence": 0.50,
            "observations": 1,
            "acceptance_count": 1,
            "source": [f"user_feedback:{source_event}"],
            "status": "candidate",
        }
        if "rules" not in self._dm:
            self._dm["rules"] = []
        self._dm["rules"].append(candidate)
        log.info("New candidate rule %s: (%s, %s) → %s",
                 candidate_id, data_structure, message_type, chart_type)

    def _promotion_pass(self) -> list[dict]:
        """Promote candidate rules that meet thresholds. Returns list of promoted rules."""
        promoted = []
        for rule in self._dm.get("rules", []):
            if rule.get("status") != "candidate":
                continue
            obs = rule.get("observations", 0)
            accepted = rule.get("acceptance_count", 0)
            if obs >= PROMOTE_MIN_OBS and (accepted / obs) >= PROMOTE_MIN_RATE:
                rule["status"] = "active"
                rule["confidence"] = min(0.99, accepted / obs)
                promoted.append(rule)
                log.info("Promoted rule %s to active (obs=%d, rate=%.0f%%)",
                         rule["id"], obs, 100 * accepted / obs)
        return promoted

    def _demotion_pass(self) -> list[dict]:
        """Demote active rules with too-low confidence. Returns list of demoted rules."""
        demoted = []
        for rule in self._dm.get("rules", []):
            if rule.get("status") != "active":
                continue
            obs = rule.get("observations", 0)
            conf = rule.get("confidence", 1.0)
            if obs >= DEMOTE_MIN_OBS and conf < DEMOTE_MAX_CONF:
                rule["status"] = "low_confidence"
                demoted.append(rule)
                log.warning("Demoted rule %s to low_confidence (obs=%d, conf=%.2f)",
                            rule["id"], obs, conf)
        return demoted
