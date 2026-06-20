"""Managed Inkline knowledge bundle for long-context LLM backends."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from inkline.app.mcp_resources import read_resource


KNOWLEDGE_ALLOWLIST: tuple[str, ...] = (
    "inkline://playbooks/index",
    "inkline://layouts",
    "inkline://anti-patterns",
    "inkline://archetypes",
    "inkline://brands",
    "inkline://themes",
    "inkline://typography",
    "inkline://templates",
    "inkline://playbooks/chart_selection",
    "inkline://playbooks/color_theory",
    "inkline://playbooks/document_design",
    "inkline://playbooks/narrative_frameworks",
    "inkline://playbooks/one_pager_design",
    "inkline://playbooks/professional_exhibit_design",
    "inkline://playbooks/slide_layouts",
    "inkline://playbooks/full_slide_archetypes",
    "inkline://playbooks/storyboard_and_message_design",
    "inkline://playbooks/reference_deck_ingestion",
    "inkline://playbooks/typography",
    "inkline://slide_roles",
    "inkline://archetypes/full_slide",
    "inkline://storyboard_rules",
)


@dataclass(frozen=True)
class BundleResource:
    uri: str
    sha256: str
    token_count: int


@dataclass(frozen=True)
class ManagedBundle:
    bundle_hash: str
    token_count: int
    resources: list[BundleResource]
    trust_level: str
    last_rebuilt_at: str
    bundle_path: str
    manifest_path: str
    max_tokens: int
    rebuilt: bool

    def diagnostics(self) -> dict:
        data = asdict(self)
        data["resources"] = [asdict(item) for item in self.resources]
        return data


def _cache_dir(cache_dir: Path | None = None) -> Path:
    return (cache_dir or Path("~/.cache/inkline/knowledge_bundle")).expanduser().resolve()


def _token_count(text: str) -> int:
    return max(1, len(text) // 4)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_sources(allowlist: Iterable[str]) -> list[tuple[str, str]]:
    sources: list[tuple[str, str]] = []
    for uri in allowlist:
        try:
            sources.append((uri, read_resource(uri)))
        except Exception:
            continue
    return sources


def build_or_load_bundle(*, context_window: int, cache_dir: Path | None = None) -> ManagedBundle:
    """Build a hash-tracked bundle capped at 50% context or 500k tokens."""
    root = _cache_dir(cache_dir)
    root.mkdir(parents=True, exist_ok=True)
    bundle_path = root / "bundle.md"
    manifest_path = root / "manifest.json"
    max_tokens = min(context_window // 2, 500_000)

    selected: list[tuple[str, str]] = []
    resources: list[BundleResource] = []
    total_tokens = 0
    for uri, content in _load_sources(KNOWLEDGE_ALLOWLIST):
        tokens = _token_count(content)
        if total_tokens + tokens > max_tokens:
            continue
        selected.append((uri, content))
        resources.append(BundleResource(uri=uri, sha256=_hash_text(content), token_count=tokens))
        total_tokens += tokens

    source_fingerprint = _hash_text(json.dumps(
        [asdict(item) for item in resources],
        sort_keys=True,
    ))

    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
            if (
                existing.get("source_fingerprint") == source_fingerprint
                and bundle_path.exists()
            ):
                loaded_resources = [
                    BundleResource(**item) for item in existing.get("resources", [])
                ]
                return ManagedBundle(
                    bundle_hash=existing.get("bundle_hash", ""),
                    token_count=int(existing.get("token_count", 0)),
                    resources=loaded_resources,
                    trust_level=existing.get("trust_level", "inkline_allowlist"),
                    last_rebuilt_at=existing.get("last_rebuilt_at", ""),
                    bundle_path=str(bundle_path),
                    manifest_path=str(manifest_path),
                    max_tokens=max_tokens,
                    rebuilt=False,
                )
        except Exception:
            pass

    parts = [
        "# Inkline Managed Knowledge Bundle",
        "",
        "Trust level: inkline_allowlist",
        "",
    ]
    for uri, content in selected:
        parts.extend([f"## {uri}", "", content.strip(), ""])
    bundle_text = "\n".join(parts).strip() + "\n"
    bundle_hash = _hash_text(bundle_text)
    bundle_path.write_text(bundle_text, encoding="utf-8")
    rebuilt_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "bundle_hash": bundle_hash,
        "source_fingerprint": source_fingerprint,
        "token_count": total_tokens,
        "resources": [asdict(item) for item in resources],
        "trust_level": "inkline_allowlist",
        "last_rebuilt_at": rebuilt_at,
        "max_tokens": max_tokens,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return ManagedBundle(
        bundle_hash=bundle_hash,
        token_count=total_tokens,
        resources=resources,
        trust_level="inkline_allowlist",
        last_rebuilt_at=rebuilt_at,
        bundle_path=str(bundle_path),
        manifest_path=str(manifest_path),
        max_tokens=max_tokens,
        rebuilt=True,
    )
