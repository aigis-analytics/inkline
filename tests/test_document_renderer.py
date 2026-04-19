"""Phase 1 tests for TypstDocumentRenderer.

All tests assert on the generated Typst string — no PDF compilation required.
"""

import pytest
from inkline.typst.document_renderer import DocumentSpec, TypstDocumentRenderer

MINIMAL_THEME = {
    "heading_font": "Inter",
    "body_font": "Inter",
    "body_size": 11,
    "accent": "#1a3a5c",
    "accent2": "#39d3bb",
    "muted": "#6B7280",
    "border": "#D1D5DB",
    "text": "#1A1A1A",
    "surface": "#F4F6F8",
    "secondary": "#B8960C",
    "confidentiality": "Confidential",
    "footer_text": "Test Document",
}


def make_renderer():
    return TypstDocumentRenderer(theme=MINIMAL_THEME)


# Test 1: Cover page omits panel block when cover_panel is None
def test_cover_page_no_panel():
    spec = DocumentSpec(title="Test", cover_panel=None)
    renderer = make_renderer()
    result = renderer.render_document(spec)
    assert "DEAL AT A GLANCE" not in result
    assert "HIGHLIGHTS" not in result


# Test 2: Cover page renders panel entries when cover_panel is provided
def test_cover_page_with_panel():
    spec = DocumentSpec(
        title="Test",
        cover_panel={"Total target": "£80m", "Blended cost": "~9.5%"},
    )
    renderer = make_renderer()
    result = renderer.render_document(spec)
    assert "£80m" in result
    assert "~9.5%" in result
    assert "Total target" in result


# Test 3: Exhibit counter definitions are emitted
def test_exhibit_counter_defs():
    spec = DocumentSpec(title="Test")
    renderer = make_renderer()
    result = renderer.render_document(spec)
    assert 'counter("figures")' in result
    assert 'counter("tables")' in result
    assert "#let fig(" in result
    assert "#let tbl(" in result


# Test 4: Section with exhibit emits fig/tbl wrapper
def test_section_figure_exhibit():
    spec = DocumentSpec(
        title="Test",
        sections=[
            {
                "heading": "Analysis",
                "level": 1,
                "content": "See the chart below.",
                "exhibits": [
                    {
                        "type": "figure",
                        "content": '#image("chart.png")',
                        "caption": "Revenue trend",
                        "source": "Internal",
                    }
                ],
            }
        ],
    )
    renderer = make_renderer()
    result = renderer.render_document(spec)
    assert "#fig(" in result
    assert "Revenue trend" in result
    assert "Source: Internal" in result or "source: " in result


# Test 5: par leading is 1.5em not 0.8em
def test_par_leading_not_tight():
    spec = DocumentSpec(title="Test")
    renderer = make_renderer()
    result = renderer.render_document(spec)
    assert "leading: 0.8em" not in result
    assert "leading: 1.5em" in result


# Test 6: cover_panel truncates at 6 entries
def test_cover_panel_max_six_entries():
    spec = DocumentSpec(
        title="Test",
        cover_panel={f"Key {i}": f"Val {i}" for i in range(10)},
    )
    renderer = make_renderer()
    result = renderer.render_document(spec)
    # Keys 0-5 should appear, Keys 6-9 should not
    assert "Key 0" in result
    assert "Key 5" in result
    assert "Key 6" not in result


# --- Phase 2 tests ---


# Test 7: Running header is suppressed on cover and TOC (pg > 2 guard)
def test_running_header_suppressed_on_cover():
    spec = DocumentSpec(title="Test")
    renderer = make_renderer()
    result = renderer.render_document(spec)
    assert "pg > 2" in result


# Test 8: OpenType figure variants are present in preamble show rules
def test_opentype_features_in_preamble():
    spec = DocumentSpec(title="Test")
    renderer = make_renderer()
    result = renderer.render_document(spec)
    assert '"tnum"' in result
    assert '"onum"' in result


# Test 9: tracking: 0.08em appears at least twice in component defs
def test_label_text_tracking():
    renderer = make_renderer()
    result = renderer._component_defs()
    assert result.count("tracking: 0.08em") >= 2


# Test 10: 4 level-1 sections with section_dividers=True → 4 divider pages
def test_section_dividers_inserted():
    spec = DocumentSpec(
        title="Test",
        section_dividers=True,
        sections=[
            {"heading": f"Section {i}", "level": 1, "content": "Body."}
            for i in range(1, 5)
        ],
    )
    renderer = make_renderer()
    result = renderer.render_document(spec)
    assert result.count("// Section divider —") == 4


# Test 11: 2 level-1 sections with section_dividers=True → no dividers
def test_section_dividers_not_inserted_below_threshold():
    spec = DocumentSpec(
        title="Test",
        section_dividers=True,
        sections=[
            {"heading": f"Section {i}", "level": 1, "content": "Body."}
            for i in range(1, 3)
        ],
    )
    renderer = make_renderer()
    result = renderer.render_document(spec)
    assert "// Section divider —" not in result
