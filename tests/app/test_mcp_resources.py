"""Tests for inkline.app.mcp_resources — every URI returns valid content."""

from __future__ import annotations

import pytest

from inkline.app.mcp_resources import (
    list_resources,
    read_resource,
    ResourceNotFoundError,
    _build_playbook_index,
)


# ---------------------------------------------------------------------------
# list_resources
# ---------------------------------------------------------------------------

class TestListResources:
    def test_returns_list(self):
        resources = list_resources()
        assert isinstance(resources, list)
        assert len(resources) > 0

    def test_each_resource_has_required_fields(self):
        resources = list_resources()
        for r in resources:
            assert "uri" in r, f"Missing 'uri' in {r}"
            assert "name" in r, f"Missing 'name' in {r}"
            assert "mimeType" in r, f"Missing 'mimeType' in {r}"

    def test_all_uris_start_with_inkline_scheme(self):
        resources = list_resources()
        for r in resources:
            assert r["uri"].startswith("inkline://"), f"Bad URI: {r['uri']}"

    def test_includes_core_resources(self):
        uris = {r["uri"] for r in list_resources()}
        assert "inkline://playbooks/index" in uris
        assert "inkline://layouts" in uris
        assert "inkline://anti-patterns" in uris
        assert "inkline://archetypes" in uris
        assert "inkline://brands" in uris
        assert "inkline://themes" in uris
        assert "inkline://typography" in uris
        assert "inkline://templates" in uris

    def test_includes_playbook_resources(self):
        uris = {r["uri"] for r in list_resources()}
        # Should have at least one inkline://playbooks/<name> resource
        playbook_uris = [u for u in uris if u.startswith("inkline://playbooks/") and u != "inkline://playbooks/index"]
        assert len(playbook_uris) > 0


# ---------------------------------------------------------------------------
# read_resource — core URIs
# ---------------------------------------------------------------------------

class TestReadResourceCore:
    def test_playbooks_index_returns_content(self):
        content = read_resource("inkline://playbooks/index")
        assert isinstance(content, str)
        assert len(content) > 100
        assert "inkline://playbooks/" in content

    def test_layouts_returns_catalogue(self):
        content = read_resource("inkline://layouts")
        assert isinstance(content, str)
        assert "three_card" in content
        assert "split" in content
        assert "freeform" in content

    def test_anti_patterns_returns_content(self):
        content = read_resource("inkline://anti-patterns")
        assert isinstance(content, str)
        assert len(content) > 10

    def test_archetypes_returns_content(self):
        content = read_resource("inkline://archetypes")
        assert isinstance(content, str)
        assert len(content) > 10

    def test_brands_returns_list(self):
        content = read_resource("inkline://brands")
        assert isinstance(content, str)
        assert len(content) > 0

    def test_themes_returns_list(self):
        content = read_resource("inkline://themes")
        assert isinstance(content, str)
        # May fail gracefully if theme registry not available

    def test_typography_returns_playbook(self):
        content = read_resource("inkline://typography")
        assert isinstance(content, str)
        assert len(content) > 100

    def test_templates_returns_list(self):
        content = read_resource("inkline://templates")
        assert isinstance(content, str)

    def test_unknown_uri_raises(self):
        with pytest.raises(ResourceNotFoundError):
            read_resource("inkline://nonexistent/resource")


# ---------------------------------------------------------------------------
# read_resource — layouts/<slide_type>
# ---------------------------------------------------------------------------

class TestReadLayoutResource:
    def test_three_card_layout(self):
        content = read_resource("inkline://layouts/three_card")
        assert "three_card" in content
        assert isinstance(content, str)

    def test_freeform_layout(self):
        content = read_resource("inkline://layouts/freeform")
        assert "freeform" in content

    def test_unknown_layout_raises(self):
        with pytest.raises(ResourceNotFoundError):
            read_resource("inkline://layouts/totally_fake_layout_xyz")


# ---------------------------------------------------------------------------
# read_resource — playbooks/<name>
# ---------------------------------------------------------------------------

class TestReadPlaybookResource:
    def test_slide_layouts_playbook(self):
        content = read_resource("inkline://playbooks/slide_layouts")
        assert isinstance(content, str)
        assert len(content) > 100
        # Should contain front-matter
        assert "domain:" in content or "layout" in content.lower()

    def test_typography_playbook(self):
        content = read_resource("inkline://playbooks/typography")
        assert isinstance(content, str)
        assert len(content) > 100

    def test_nonexistent_playbook_raises(self):
        with pytest.raises(ResourceNotFoundError):
            read_resource("inkline://playbooks/totally_fake_playbook_xyz")


# ---------------------------------------------------------------------------
# Playbook index — front-matter
# ---------------------------------------------------------------------------

class TestPlaybookIndex:
    def test_index_has_all_playbooks(self):
        index = _build_playbook_index()
        assert isinstance(index, dict)
        assert len(index) > 0

    def test_each_entry_has_required_fields(self):
        index = _build_playbook_index()
        for name, meta in index.items():
            assert "name" in meta, f"Missing 'name' in playbook {name}"
            assert "uri" in meta, f"Missing 'uri' in playbook {name}"
            assert "domain" in meta, f"Missing 'domain' in playbook {name}"
            assert "version" in meta, f"Missing 'version' in playbook {name}"

    def test_slide_layouts_has_domain(self):
        index = _build_playbook_index()
        assert "slide_layouts" in index
        assert index["slide_layouts"]["domain"] == "layout"

    def test_typography_has_domain(self):
        index = _build_playbook_index()
        assert "typography" in index
        assert index["typography"]["domain"] == "typography"
