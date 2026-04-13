"""Claude Code subprocess caller — drive Inkline's DesignAdvisor through a
local Claude Code session, using the user's logged-in subscription instead of
a paid Anthropic API key.

This is the integration point for users on a Claude Max / Pro plan who want
Inkline's intelligence layer to use their subscription rather than a separate
API key. It shells out to the ``claude`` CLI in print mode.

Usage::

    from inkline.intelligence import DesignAdvisor
    from inkline.intelligence.claude_code import build_claude_code_caller

    caller = build_claude_code_caller(model="sonnet")
    advisor = DesignAdvisor(brand="minimal", llm_caller=caller, mode="llm")
    slides = advisor.design_deck(title="Q1 review", sections=[...])

The caller is a plain ``Callable[[system, user], str]`` so it satisfies the
``inkline.intelligence.design_advisor.LLMCaller`` type and works as a drop-in
replacement for the public Anthropic SDK path. No API key is consumed.

This module also exposes :func:`ensure_bridge_running`, which checks whether
the Claude bridge HTTP server is up at a given URL and, if not, attempts to
start it automatically from ``~/.config/inkline/claude_bridge.py`` (the
personal brands private config directory). This is called automatically by
:class:`~inkline.intelligence.design_advisor.DesignAdvisor` before every LLM
call so that API credits are never consumed when a bridge can be started.

Requirements
------------
- ``claude`` CLI on $PATH (Claude Code must be installed and authenticated).
  Run ``claude /login`` once on the host to log into your subscription.
- The ``--bare`` flag is used so hooks, plugins, MCP servers, and CLAUDE.md
  auto-discovery are all skipped — Inkline supplies the entire prompt itself.

This module adds zero new dependencies — only ``subprocess`` from the stdlib.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable

log = logging.getLogger(__name__)


class ClaudeCodeNotInstalled(RuntimeError):
    """Raised when the ``claude`` CLI is not on $PATH."""


def claude_code_available() -> bool:
    """Return True if the ``claude`` CLI is on $PATH and runnable."""
    return shutil.which("claude") is not None


def build_claude_code_caller(
    *,
    model: str = "sonnet",
    timeout: int = 300,
    extra_args: list[str] | None = None,
) -> Callable[[str, str], str]:
    """Construct an ``LLMCaller`` that routes prompts through ``claude --print``.

    Parameters
    ----------
    model : str
        Model alias or full ID accepted by ``claude --model``. Defaults to
        ``"sonnet"`` (resolved by Claude Code to the current Sonnet release).
        Use ``"opus"`` for the most capable model on the subscription.
    timeout : int
        Subprocess timeout in seconds. Defaults to 5 minutes — design planning
        on long playbooks can exceed the standard 60-second default.
    extra_args : list[str], optional
        Additional flags forwarded to the ``claude`` CLI (e.g.
        ``["--max-budget-usd", "0"]`` to enforce zero spend on API fallback).

    Returns
    -------
    Callable[[system, user], str]
        A function suitable for ``DesignAdvisor(llm_caller=...)``.

    Raises
    ------
    ClaudeCodeNotInstalled
        If the ``claude`` CLI is not on $PATH at construction time. Detect this
        eagerly so misconfiguration doesn't surface mid-render.
    """
    if not claude_code_available():
        raise ClaudeCodeNotInstalled(
            "The 'claude' CLI is not on $PATH. Install Claude Code from "
            "https://docs.claude.com/claude-code and run 'claude /login' to "
            "authenticate with your subscription."
        )

    base_args = [
        "claude",
        "--print",
        "--bare",                  # skip hooks/plugins/auto-discovery
        "--model", model,
        "--no-session-persistence",
        "--output-format", "text",
    ]
    if extra_args:
        base_args.extend(extra_args)

    def caller(system_prompt: str, user_prompt: str) -> str:
        """Route a (system, user) prompt pair through the local Claude Code CLI."""
        # Inkline's playbook + slide-type guide goes into the system prompt;
        # the content brief goes into the user prompt (passed via stdin).
        args = base_args + ["--append-system-prompt", system_prompt]
        log.debug(
            "claude_code caller: invoking %s with %d-char system + %d-char user",
            args[0], len(system_prompt), len(user_prompt),
        )
        try:
            result = subprocess.run(
                args,
                input=user_prompt,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"claude_code caller timed out after {timeout}s"
            ) from exc

        if result.returncode != 0:
            raise RuntimeError(
                f"claude_code caller failed (rc={result.returncode}): "
                f"{result.stderr.strip()[:500]}"
            )

        text = result.stdout.strip()
        if not text:
            raise RuntimeError("claude_code caller returned empty output")
        return text

    return caller


def ensure_bridge_running(
    bridge_url: str = "http://localhost:8082",
    startup_wait: float = 4.0,
) -> bool:
    """Ensure the Claude bridge HTTP server is reachable.

    1. Checks the bridge health endpoint.  If healthy → returns ``True``.
    2. If not reachable, looks for a bridge script at
       ``~/.config/inkline/claude_bridge.py`` (the personal brands private
       config directory) and starts it as a detached background process.
    3. Waits up to ``startup_wait`` seconds for it to become healthy.
    4. Returns ``True`` if the bridge is reachable after these steps, else ``False``.

    This is called automatically by ``DesignAdvisor._call_llm`` before every
    LLM request so that API credits are never consumed when a bridge is
    available.

    Parameters
    ----------
    bridge_url:
        Base URL of the bridge server (default: ``http://localhost:8082``).
    startup_wait:
        Seconds to wait after launching the bridge process before giving up.
    """
    try:
        import requests as _req
        r = _req.get(f"{bridge_url}/health", timeout=1)
        if r.status_code == 200 and r.json().get("status") == "ok":
            log.debug("ensure_bridge_running: bridge already healthy at %s", bridge_url)
            return True
    except Exception:
        pass

    # Not reachable — try to start from personal config
    bridge_script = Path.home() / ".config" / "inkline" / "claude_bridge.py"
    if not bridge_script.exists():
        log.info(
            "ensure_bridge_running: bridge not running and no script found at %s",
            bridge_script,
        )
        return False

    log.info(
        "ensure_bridge_running: bridge not running — starting %s", bridge_script
    )
    try:
        subprocess.Popen(
            ["python3", str(bridge_script)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as exc:
        log.warning("ensure_bridge_running: failed to start bridge: %s", exc)
        return False

    # Poll for healthy status
    deadline = time.monotonic() + startup_wait
    while time.monotonic() < deadline:
        time.sleep(0.5)
        try:
            import requests as _req
            r = _req.get(f"{bridge_url}/health", timeout=1)
            if r.status_code == 200 and r.json().get("status") == "ok":
                log.info("ensure_bridge_running: bridge started and healthy at %s", bridge_url)
                return True
        except Exception:
            pass

    log.warning(
        "ensure_bridge_running: bridge started but did not become healthy within %.1fs",
        startup_wait,
    )
    return False


__all__ = [
    "ClaudeCodeNotInstalled",
    "build_claude_code_caller",
    "claude_code_available",
    "ensure_bridge_running",
]
