"""LLM CLI backend adapters for the Inkline bridge."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


BackendName = Literal["claude", "gemini"]


@dataclass(frozen=True)
class BackendInvocation:
    cmd: list[str]
    stdin_text: str
    source_label: str


@dataclass(frozen=True)
class BackendCapabilities:
    context_window: int
    multimodal: bool
    tool_streaming: bool
    context_caching: bool
    reasoning_profile: str
    vision_profile: str


@dataclass(frozen=True)
class CLIBackend:
    name: BackendName
    executable: str

    @property
    def model(self) -> str:
        if self.name == "gemini":
            return os.environ.get("INKLINE_GEMINI_MODEL", "gemini-2.5-pro")
        return os.environ.get("INKLINE_CLAUDE_MODEL", "claude-cli-default")

    def capabilities(self) -> BackendCapabilities:
        if self.name == "gemini":
            return BackendCapabilities(
                context_window=1_000_000,
                multimodal=True,
                tool_streaming=True,
                context_caching=True,
                reasoning_profile="long-context-design-reasoning",
                vision_profile="native-image-understanding",
            )
        return BackendCapabilities(
            context_window=200_000,
            multimodal=True,
            tool_streaming=True,
            context_caching=False,
            reasoning_profile="agentic-code-and-design-reasoning",
            vision_profile="image-read-tool",
        )

    def available(self) -> bool:
        return shutil.which(self.executable) is not None

    def version_cmd(self) -> list[str]:
        return [self.executable, "--version"]

    def prepare_env(self, env: dict[str, str]) -> dict[str, str]:
        env = dict(env)
        if self.name == "claude":
            env.pop("CLAUDECODE", None)
            env.pop("CLAUDE_CODE_ENTRYPOINT", None)
        if self.name == "gemini":
            env.pop("GEMINI_API_KEY", None)
            env.pop("GOOGLE_API_KEY", None)
            env.pop("GOOGLE_GENAI_USE_VERTEXAI", None)
        return env

    def prompt_invocation(self, *, system: str, prompt: str, max_turns: int) -> BackendInvocation:
        if self.name == "claude":
            return BackendInvocation(
                cmd=[
                    "claude", "-p",
                    "--output-format", "stream-json",
                    "--verbose",
                    "--dangerously-skip-permissions",
                    "--max-turns", str(max_turns),
                    "--system-prompt", system,
                ],
                stdin_text=prompt,
                source_label="claude_max",
            )
        merged = (
            "System instructions:\n"
            f"{system}\n\n"
            "User request:\n"
            f"{prompt}"
        )
        return BackendInvocation(
            cmd=[
                "gemini",
                "--prompt", merged,
                "--output-format", "stream-json",
                "--sandbox", "true",
                "--approval-mode", "auto_edit",
                "--policy", str(_policy_path()),
                "--include-directories", str(_project_root()),
                "--model", self.model,
            ],
            stdin_text="",
            source_label="gemini_cli",
        )

    def vision_invocation(self, *, system: str, prompt: str, image_path: str) -> BackendInvocation:
        image_dir = str(Path(image_path).expanduser().resolve().parent)
        vision_prompt = (
            f"{prompt}\n\n"
            "Use the local file below as the image to inspect:\n"
            f"{image_path}\n"
        )
        if self.name == "claude":
            return BackendInvocation(
                cmd=[
                    "claude", "-p",
                    "--output-format", "stream-json",
                    "--verbose",
                    "--dangerously-skip-permissions",
                    "--max-turns", "5",
                    "--system-prompt", system,
                ],
                stdin_text=(
                    f"Please use the Read tool to read this image file:\n{image_path}\n\n"
                    f"Then answer the following:\n{prompt}"
                ),
                source_label="claude_max",
            )
        merged = (
            "System instructions:\n"
            f"{system}\n\n"
            "User request:\n"
            f"{vision_prompt}"
        )
        return BackendInvocation(
            cmd=[
                "gemini",
                "--prompt", merged,
                "--output-format", "stream-json",
                "--sandbox", "true",
                "--approval-mode", "auto_edit",
                "--policy", str(_policy_path()),
                "--include-directories", str(_project_root()),
                "--include-directories", image_dir,
                "--model", self.model,
            ],
            stdin_text="",
            source_label="gemini_cli",
        )


CLAUDE_BACKEND = CLIBackend(name="claude", executable="claude")
GEMINI_BACKEND = CLIBackend(name="gemini", executable="gemini")
KNOWN_BACKENDS = {
    "claude": CLAUDE_BACKEND,
    "gemini": GEMINI_BACKEND,
}


def available_backend_names() -> list[str]:
    return [name for name, backend in KNOWN_BACKENDS.items() if backend.available()]


def _project_root() -> Path:
    return Path(os.environ.get("INKLINE_PROJECT_ROOT", Path.cwd())).expanduser().resolve()


def _policy_path() -> Path:
    return Path(os.environ.get(
        "INKLINE_BRIDGE_POLICY",
        Path(__file__).with_name("inkline_bridge_policy.toml"),
    )).expanduser().resolve()


def resolve_backend(name: str | None) -> CLIBackend:
    requested_arg = (name or "auto").lower()
    requested = (
        os.environ.get("INKLINE_LLM_BACKEND", "auto").lower()
        if requested_arg == "auto"
        else requested_arg
    )
    if requested == "auto":
        for candidate in ("claude", "gemini"):
            backend = KNOWN_BACKENDS[candidate]
            if backend.available():
                return backend
        return CLAUDE_BACKEND
    if requested not in KNOWN_BACKENDS:
        raise ValueError(f"Unknown backend: {requested}")
    return KNOWN_BACKENDS[requested]
