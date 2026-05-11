"""Provider-neutral stream-json event normalization."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Literal


EventKind = Literal["text", "tool_call", "tool_result", "phase", "result", "error", "unknown"]


@dataclass(frozen=True)
class NormalizedStreamEvent:
    provider: str
    kind: EventKind
    text: str = ""
    tool_name: str = ""
    tool_input: dict[str, str] = field(default_factory=dict)
    phase: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


def _stringify_input(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        str(k): (str(v)[:500] + "..." if len(str(v)) > 500 else str(v))
        for k, v in value.items()
    }


_PHASE_START_RE = re.compile(r"\[ARCHON\] Phase: (\S+)")
_PHASE_END_RE = re.compile(r"\[ARCHON\] (\S+) \u2192 (OK|FAILED)")


def _append_text_event(
    out: list[NormalizedStreamEvent],
    *,
    provider: str,
    text: str,
    raw: dict[str, Any],
    fallback_kind: EventKind,
) -> None:
    phase_start = _PHASE_START_RE.search(text)
    phase_end = _PHASE_END_RE.search(text)
    if phase_start:
        out.append(NormalizedStreamEvent(
            provider=provider,
            kind="phase",
            text=text,
            phase=phase_start.group(1),
            raw=raw,
        ))
        return
    if phase_end:
        out.append(NormalizedStreamEvent(
            provider=provider,
            kind="phase",
            text=text,
            phase=phase_end.group(1),
            raw=raw,
        ))
        return
    out.append(NormalizedStreamEvent(provider=provider, kind=fallback_kind, text=text, raw=raw))


def normalize_stream_line(provider: str, line: str) -> list[NormalizedStreamEvent]:
    """Normalize Claude/Gemini stream-json events into bridge events."""
    try:
        event = json.loads(line.strip())
    except Exception:
        return []
    if not isinstance(event, dict):
        return []

    out: list[NormalizedStreamEvent] = []
    etype = str(event.get("type") or event.get("event") or "")

    if etype == "result":
        _append_text_event(
            out,
            provider=provider,
            text=str(event.get("result", "")),
            raw=event,
            fallback_kind="result",
        )
        return out

    if etype in {"error", "fatal"}:
        out.append(NormalizedStreamEvent(
            provider=provider,
            kind="error",
            text=str(event.get("error") or event.get("message") or ""),
            raw=event,
        ))
        return out

    blocks = event.get("message", {}).get("content", [])
    if not isinstance(blocks, list):
        blocks = event.get("content", [])
    if not isinstance(blocks, list):
        blocks = []

    for block in blocks:
        if not isinstance(block, dict):
            continue
        btype = block.get("type") or block.get("kind")
        if btype in {"text", "output_text"}:
            text = str(block.get("text") or block.get("content") or "")
            _append_text_event(out, provider=provider, text=text, raw=event, fallback_kind="text")
        elif btype in {"tool_use", "tool_call", "function_call"}:
            out.append(NormalizedStreamEvent(
                provider=provider,
                kind="tool_call",
                tool_name=str(block.get("name") or block.get("tool") or block.get("function_name") or "unknown"),
                tool_input=_stringify_input(block.get("input") or block.get("args") or {}),
                raw=event,
            ))
        elif btype in {"tool_result", "function_response"}:
            content = block.get("content", "")
            if isinstance(content, list):
                text = "\n".join(
                    str(item.get("text", ""))
                    for item in content
                    if isinstance(item, dict) and item.get("type") == "text"
                )
            else:
                text = str(content)
            _append_text_event(out, provider=provider, text=text, raw=event, fallback_kind="tool_result")

    # Gemini CLI variants often expose tool calls at the top level.
    top_tool = event.get("tool_call") or event.get("function_call")
    if isinstance(top_tool, dict):
        out.append(NormalizedStreamEvent(
            provider=provider,
            kind="tool_call",
            tool_name=str(top_tool.get("name") or top_tool.get("tool") or "unknown"),
            tool_input=_stringify_input(top_tool.get("input") or top_tool.get("args") or {}),
            raw=event,
        ))

    if etype == "tool_result":
        content = event.get("content", "")
        _append_text_event(
            out,
            provider=provider,
            text=str(content),
            raw=event,
            fallback_kind="tool_result",
        )

    if not out:
        out.append(NormalizedStreamEvent(provider=provider, kind="unknown", raw=event))
    return out
