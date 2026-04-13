"""Archon — Inkline's pipeline supervisor and single point of user contact.

The Archon intercepts all log messages from the inkline logger tree,
records every pipeline phase with timing and issue counts, and writes a
structured issues report at completion.  The user sees the output artefact
(PDF, document) and the Archon report — nothing else.

Usage::

    from inkline.intelligence.archon import Archon, Issue

    archon = Archon(report_path=Path("run/archon_issues.md"))

    phase = archon.start_phase("design_advisor_llm")
    try:
        ...  # do work
        archon.end_phase(phase, ok=True)
    except Exception as e:
        archon.record(Issue(phase="design_advisor_llm", severity="ERROR",
                            message=str(e), detail=traceback.format_exc()))
        archon.end_phase(phase, ok=False)
        archon.write_report()
        archon.detach()
        raise

    archon.write_report()
    archon.detach()

The Archon attaches to the root ``inkline`` logger only.  All child loggers
(``inkline.intelligence``, ``inkline.typst``, etc.) propagate to root
automatically, so a single handler captures the full pipeline without
duplicate entries.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Issue:
    """A single logged issue from a pipeline phase."""
    phase: str
    severity: str     # "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL"
    message: str
    detail: str = ""  # optional traceback or extra context


@dataclass
class PhaseResult:
    """Timing and issue record for one pipeline phase."""
    name: str
    started: float = field(default_factory=time.time)
    ended: float = 0.0
    ok: bool = True
    issues: list[Issue] = field(default_factory=list)

    @property
    def elapsed(self) -> float:
        return self.ended - self.started

    def finish(self, ok: bool = True) -> None:
        self.ended = time.time()
        self.ok = ok


# ---------------------------------------------------------------------------
# Logging handler
# ---------------------------------------------------------------------------

class _ArchonHandler(logging.Handler):
    """Capture all log records from inkline modules and route to Archon."""

    def __init__(self, archon: "Archon") -> None:
        super().__init__()
        self.archon = archon

    def emit(self, record: logging.LogRecord) -> None:
        sev = record.levelname
        if sev == "DEBUG":
            return  # skip noise
        phase = self.archon.current_phase or "startup"
        self.archon.record(Issue(phase=phase, severity=sev,
                                 message=record.getMessage()))


# ---------------------------------------------------------------------------
# Archon supervisor
# ---------------------------------------------------------------------------

class Archon:
    """Pipeline supervisor: phase tracking + log interception + report writing.

    Parameters
    ----------
    report_path:
        Where to write the structured issues report (Markdown).
    title:
        Short description of the run, used in the report header.
    verbose:
        If True, print phase start/end banners to stdout.
    """

    def __init__(
        self,
        report_path: Path,
        title: str = "Inkline Pipeline",
        verbose: bool = True,
    ) -> None:
        self.report_path = Path(report_path)
        self.title = title
        self.verbose = verbose

        self.phases: list[PhaseResult] = []
        self.current_phase: str | None = None
        self._active: PhaseResult | None = None

        # Attach to root inkline logger only — child loggers propagate up,
        # so attaching to all three would create duplicate log entries.
        self._handler = _ArchonHandler(self)
        root_lg = logging.getLogger("inkline")
        root_lg.addHandler(self._handler)
        root_lg.setLevel(logging.DEBUG)

    # ------------------------------------------------------------------
    # Phase management
    # ------------------------------------------------------------------

    def start_phase(self, name: str) -> PhaseResult:
        """Begin a named pipeline phase."""
        phase = PhaseResult(name=name)
        self.phases.append(phase)
        self._active = phase
        self.current_phase = name
        if self.verbose:
            print(f"\n{'=' * 70}")
            print(f"[ARCHON] Phase: {name}")
            print(f"{'=' * 70}")
        return phase

    def end_phase(self, phase: PhaseResult, ok: bool = True) -> None:
        """Close the active phase and record its outcome."""
        phase.finish(ok)
        if self.verbose:
            status = "OK" if ok else "FAILED"
            print(
                f"[ARCHON] {phase.name} → {status} in {phase.elapsed:.1f}s "
                f"({len(phase.issues)} issues logged)"
            )
        self._active = None
        self.current_phase = None

    def record(self, issue: Issue) -> None:
        """Record an issue explicitly (outside of the log interception path)."""
        if self._active:
            self._active.issues.append(issue)
        else:
            # Before any phase starts, or between phases — attach to a
            # synthetic startup phase so nothing is lost.
            if not self.phases or self.phases[-1].name != "startup":
                startup = PhaseResult(name="startup")
                startup.finish(ok=True)
                self.phases.insert(0, startup)
            self.phases[0].issues.append(issue)

    # ------------------------------------------------------------------
    # Convenience queries
    # ------------------------------------------------------------------

    @property
    def all_ok(self) -> bool:
        return all(p.ok for p in self.phases)

    def error_count(self) -> int:
        return sum(
            1 for p in self.phases for i in p.issues
            if i.severity in ("ERROR", "CRITICAL")
        )

    def warning_count(self) -> int:
        return sum(
            1 for p in self.phases for i in p.issues
            if i.severity == "WARNING"
        )

    def info_count(self) -> int:
        return sum(
            1 for p in self.phases for i in p.issues
            if i.severity == "INFO"
        )

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    def write_report(self) -> None:
        """Write the structured issues report to ``self.report_path``."""
        lines = [
            f"# Archon Issues Report — {self.title}",
            f"**Run date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        total = sum(len(p.issues) for p in self.phases)
        errors = self.error_count()
        warnings = self.warning_count()
        infos = self.info_count()

        lines += [
            "## Summary",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total phases | {len(self.phases)} |",
            f"| Total issues | {total} |",
            f"| Errors / Criticals | {errors} |",
            f"| Warnings | {warnings} |",
            f"| Info | {infos} |",
            "",
            f"**Pipeline status:** {'✅ COMPLETE' if self.all_ok else '❌ FAILED'}",
            "",
        ]

        lines += ["## Phase Detail", ""]
        for phase in self.phases:
            status = "✅" if phase.ok else "❌"
            elapsed = f"{phase.elapsed:.1f}s" if phase.ended else "running"
            lines.append(f"### {status} {phase.name} ({elapsed})")
            if not phase.issues:
                lines.append("_No issues logged._")
            else:
                icons = {
                    "INFO": "ℹ", "WARNING": "⚠", "ERROR": "🔴", "CRITICAL": "🚨",
                }
                for iss in phase.issues:
                    icon = icons.get(iss.severity, "•")
                    lines.append(f"- {icon} **{iss.severity}** — {iss.message}")
                    if iss.detail:
                        lines.append(f"  ```\n  {iss.detail}\n  ```")
            lines.append("")

        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text("\n".join(lines), encoding="utf-8")

        if self.verbose:
            print(f"\n[ARCHON] Report: {self.report_path}")
            print(f"         {errors} errors, {warnings} warnings, {infos} info")

    def detach(self) -> None:
        """Remove the log handler from the inkline logger tree."""
        logging.getLogger("inkline").removeHandler(self._handler)


__all__ = ["Archon", "Issue", "PhaseResult"]
