from __future__ import annotations

import json

from inkline.app.stream_events import normalize_stream_line


def test_normalize_claude_tool_call():
    line = json.dumps({
        "type": "assistant",
        "message": {
            "content": [{
                "type": "tool_use",
                "name": "Bash",
                "input": {"command": "echo hi"},
            }],
        },
    })

    events = normalize_stream_line("claude", line)

    assert events[0].kind == "tool_call"
    assert events[0].tool_name == "Bash"
    assert events[0].tool_input["command"] == "echo hi"


def test_normalize_gemini_top_level_tool_call():
    line = json.dumps({
        "event": "tool_call",
        "tool_call": {
            "name": "write_file",
            "args": {"path": "deck.md"},
        },
    })

    events = normalize_stream_line("gemini", line)

    assert any(event.kind == "tool_call" for event in events)
    tool = next(event for event in events if event.kind == "tool_call")
    assert tool.tool_name == "write_file"
    assert tool.tool_input["path"] == "deck.md"


def test_normalize_tool_result_text():
    line = json.dumps({"type": "tool_result", "content": "[ARCHON] Phase: parse_markdown"})

    events = normalize_stream_line("gemini", line)

    assert events[0].kind == "phase"
    assert events[0].phase == "parse_markdown"
    assert "parse_markdown" in events[0].text


def test_archon_observes_normalized_phase_event(tmp_path):
    from inkline.intelligence.archon import Archon

    archon = Archon(report_path=tmp_path / "report.md", verbose=False)
    try:
        event = normalize_stream_line(
            "gemini",
            json.dumps({"type": "tool_result", "content": "[ARCHON] Phase: design_advisor_llm"}),
        )[0]
        archon.observe_stream_event(event)

        assert archon.current_phase == "design_advisor_llm"
    finally:
        archon.detach()
