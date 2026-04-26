"""Tests for playbook front-matter metadata — every playbook has required fields."""

from __future__ import annotations

from pathlib import Path

import pytest

_PLAYBOOKS_DIR = Path(__file__).parent.parent.parent / "src" / "inkline" / "intelligence" / "playbooks"

REQUIRED_FIELDS = {"domain", "audience", "slide_type_relevance", "last_updated", "version"}


def _get_playbook_files():
    return [
        f for f in sorted(_PLAYBOOKS_DIR.glob("*.md"))
        if not f.name.startswith("_")
    ]


def _parse_front_matter(content: str) -> dict:
    """Extract YAML front-matter from a markdown file (minimal parser)."""
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    fm_text = content[3:end].strip()
    result = {}
    for line in fm_text.splitlines():
        if ":" in line and not line.startswith(" ") and not line.startswith("-"):
            k, _, v = line.partition(":")
            result[k.strip()] = v.strip()
    return result


@pytest.mark.parametrize("playbook_file", _get_playbook_files(), ids=lambda f: f.stem)
def test_playbook_has_front_matter(playbook_file):
    """Every playbook should start with YAML front-matter."""
    content = playbook_file.read_text(encoding="utf-8")
    assert content.startswith("---"), (
        f"Playbook {playbook_file.name} missing YAML front-matter. "
        f"Add --- block with domain, audience, slide_type_relevance, last_updated, version."
    )


@pytest.mark.parametrize("playbook_file", _get_playbook_files(), ids=lambda f: f.stem)
def test_playbook_has_required_fields(playbook_file):
    """Every playbook must have the required front-matter fields."""
    content = playbook_file.read_text(encoding="utf-8")
    fm = _parse_front_matter(content)
    missing = REQUIRED_FIELDS - set(fm.keys())
    assert not missing, (
        f"Playbook {playbook_file.name} missing front-matter fields: {missing}"
    )


@pytest.mark.parametrize("playbook_file", _get_playbook_files(), ids=lambda f: f.stem)
def test_playbook_version_is_semver(playbook_file):
    """Version field should look like semver (e.g. '1.0.0')."""
    content = playbook_file.read_text(encoding="utf-8")
    fm = _parse_front_matter(content)
    version = fm.get("version", "")
    # Strip quotes
    version = version.strip('"\'')
    parts = version.split(".")
    assert len(parts) == 3, (
        f"Playbook {playbook_file.name}: version {version!r} is not semver (expected X.Y.Z)"
    )
    for part in parts:
        assert part.isdigit(), (
            f"Playbook {playbook_file.name}: version {version!r} has non-numeric part {part!r}"
        )
