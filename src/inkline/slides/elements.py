"""Low-level Google Slides API request builders.

Each function returns one or more batchUpdate request dicts.
The SlideBuilder collects these and sends them in a single API call.
"""

from __future__ import annotations

import uuid
from typing import Any

from inkline.utils import inches_to_emu, pt_to_emu, hex_to_rgb


def _object_id() -> str:
    """Generate a unique object ID for Slides API elements."""
    return f"inkline_{uuid.uuid4().hex[:12]}"


def _rgb_color(hex_color: str) -> dict:
    """Convert hex color to Slides API rgbColor dict (0-1 floats)."""
    r, g, b = hex_to_rgb(hex_color)
    return {"red": r / 255.0, "green": g / 255.0, "blue": b / 255.0}


def _solid_fill(hex_color: str) -> dict:
    """Slides API solidFill property."""
    return {"solidFill": {"color": {"rgbColor": _rgb_color(hex_color)}}}


def _text_style(
    *,
    font: str = "",
    size_pt: float = 0,
    bold: bool = False,
    italic: bool = False,
    color: str = "",
    underline: bool = False,
) -> dict:
    """Build a TextStyle dict with only the specified fields."""
    style: dict[str, Any] = {}
    fields: list[str] = []

    if font:
        style["fontFamily"] = font
        fields.append("fontFamily")
    if size_pt:
        style["fontSize"] = {"magnitude": size_pt, "unit": "PT"}
        fields.append("fontSize")
    if bold:
        style["bold"] = True
        fields.append("bold")
    if italic:
        style["italic"] = True
        fields.append("italic")
    if underline:
        style["underline"] = True
        fields.append("underline")
    if color:
        style["foregroundColor"] = {"opaqueColor": {"rgbColor": _rgb_color(color)}}
        fields.append("foregroundColor")

    return style, ",".join(fields)


# ── Slide creation ──────────────────────────────────────────────────────


def create_slide(*, layout: str = "BLANK", insertion_index: int | None = None) -> tuple[str, dict]:
    """Create a new blank slide. Returns (slide_id, request)."""
    slide_id = _object_id()
    req: dict[str, Any] = {
        "createSlide": {
            "objectId": slide_id,
            "slideLayoutReference": {"predefinedLayout": layout},
        }
    }
    if insertion_index is not None:
        req["createSlide"]["insertionIndex"] = insertion_index
    return slide_id, req


# ── Text box ────────────────────────────────────────────────────────────


def create_text_box(
    slide_id: str,
    text: str,
    *,
    x: float = 0.5,
    y: float = 0.5,
    w: float = 9.0,
    h: float = 1.0,
    font: str = "",
    size_pt: float = 0,
    bold: bool = False,
    italic: bool = False,
    color: str = "",
    alignment: str = "START",
    bg_color: str = "",
) -> tuple[str, list[dict]]:
    """Create a text box with styled text. Returns (element_id, [requests])."""
    elem_id = _object_id()
    requests = [
        {
            "createShape": {
                "objectId": elem_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": inches_to_emu(w), "unit": "EMU"},
                        "height": {"magnitude": inches_to_emu(h), "unit": "EMU"},
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": inches_to_emu(x),
                        "translateY": inches_to_emu(y),
                        "unit": "EMU",
                    },
                },
            }
        },
        {
            "insertText": {
                "objectId": elem_id,
                "text": text,
                "insertionIndex": 0,
            }
        },
    ]

    # Apply text style
    style, fields = _text_style(
        font=font, size_pt=size_pt, bold=bold, italic=italic, color=color,
    )
    if fields:
        requests.append({
            "updateTextStyle": {
                "objectId": elem_id,
                "style": style,
                "textRange": {"type": "ALL"},
                "fields": fields,
            }
        })

    # Paragraph alignment
    if alignment != "START":
        requests.append({
            "updateParagraphStyle": {
                "objectId": elem_id,
                "style": {"alignment": alignment},
                "textRange": {"type": "ALL"},
                "fields": "alignment",
            }
        })

    # Background fill
    if bg_color:
        requests.append({
            "updateShapeProperties": {
                "objectId": elem_id,
                "shapeProperties": {"shapeBackgroundFill": _solid_fill(bg_color)},
                "fields": "shapeBackgroundFill",
            }
        })

    return elem_id, requests


# ── Shape (rectangle, rounded rect, etc.) ───────────────────────────────


def create_shape(
    slide_id: str,
    shape_type: str = "RECTANGLE",
    *,
    x: float = 0,
    y: float = 0,
    w: float = 10.0,
    h: float = 1.0,
    fill_color: str = "",
    border_color: str = "",
    border_weight_pt: float = 0,
) -> tuple[str, list[dict]]:
    """Create a shape. Returns (element_id, [requests])."""
    elem_id = _object_id()
    requests = [
        {
            "createShape": {
                "objectId": elem_id,
                "shapeType": shape_type,
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": inches_to_emu(w), "unit": "EMU"},
                        "height": {"magnitude": inches_to_emu(h), "unit": "EMU"},
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": inches_to_emu(x),
                        "translateY": inches_to_emu(y),
                        "unit": "EMU",
                    },
                },
            }
        }
    ]

    props: dict[str, Any] = {}
    fields: list[str] = []

    if fill_color:
        props["shapeBackgroundFill"] = _solid_fill(fill_color)
        fields.append("shapeBackgroundFill")
    if border_color or border_weight_pt:
        outline: dict[str, Any] = {}
        if border_color:
            outline["outlineFill"] = _solid_fill(border_color)
        if border_weight_pt:
            outline["weight"] = {"magnitude": border_weight_pt, "unit": "PT"}
        props["outline"] = outline
        fields.append("outline")

    if props:
        requests.append({
            "updateShapeProperties": {
                "objectId": elem_id,
                "shapeProperties": props,
                "fields": ",".join(fields),
            }
        })

    return elem_id, requests


# ── Image ───────────────────────────────────────────────────────────────


def create_image(
    slide_id: str,
    image_url: str,
    *,
    x: float = 0.5,
    y: float = 0.5,
    w: float = 4.0,
    h: float = 3.0,
) -> tuple[str, dict]:
    """Create an image from URL. Returns (element_id, request)."""
    elem_id = _object_id()
    req = {
        "createImage": {
            "objectId": elem_id,
            "url": image_url,
            "elementProperties": {
                "pageObjectId": slide_id,
                "size": {
                    "width": {"magnitude": inches_to_emu(w), "unit": "EMU"},
                    "height": {"magnitude": inches_to_emu(h), "unit": "EMU"},
                },
                "transform": {
                    "scaleX": 1,
                    "scaleY": 1,
                    "translateX": inches_to_emu(x),
                    "translateY": inches_to_emu(y),
                    "unit": "EMU",
                },
            },
        }
    }
    return elem_id, req


# ── Table ───────────────────────────────────────────────────────────────


def create_table(
    slide_id: str,
    headers: list[str],
    rows: list[list[str]],
    *,
    x: float = 0.5,
    y: float = 1.5,
    w: float = 9.0,
    h: float = 4.0,
    header_bg: str = "",
    header_color: str = "#FFFFFF",
    font: str = "",
    header_size_pt: float = 11,
    body_size_pt: float = 10,
) -> tuple[str, list[dict]]:
    """Create a table with headers and data rows. Returns (table_id, [requests])."""
    table_id = _object_id()
    num_rows = len(rows) + 1  # +1 for header
    num_cols = len(headers)

    requests: list[dict] = [
        {
            "createTable": {
                "objectId": table_id,
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": inches_to_emu(w), "unit": "EMU"},
                        "height": {"magnitude": inches_to_emu(h), "unit": "EMU"},
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": inches_to_emu(x),
                        "translateY": inches_to_emu(y),
                        "unit": "EMU",
                    },
                },
                "rows": num_rows,
                "columns": num_cols,
            }
        }
    ]

    # Populate header cells
    for col_idx, header in enumerate(headers):
        requests.append({
            "insertText": {
                "objectId": table_id,
                "cellLocation": {"rowIndex": 0, "columnIndex": col_idx},
                "text": header,
                "insertionIndex": 0,
            }
        })
        style, fields = _text_style(
            font=font, size_pt=header_size_pt, bold=True, color=header_color,
        )
        if fields:
            requests.append({
                "updateTextStyle": {
                    "objectId": table_id,
                    "cellLocation": {"rowIndex": 0, "columnIndex": col_idx},
                    "style": style,
                    "textRange": {"type": "ALL"},
                    "fields": fields,
                }
            })

    # Header row background
    if header_bg:
        for col_idx in range(num_cols):
            requests.append({
                "updateTableCellProperties": {
                    "objectId": table_id,
                    "tableRange": {
                        "location": {"rowIndex": 0, "columnIndex": col_idx},
                        "rowSpan": 1,
                        "columnSpan": 1,
                    },
                    "tableCellProperties": {
                        "tableCellBackgroundFill": _solid_fill(header_bg),
                    },
                    "fields": "tableCellBackgroundFill",
                }
            })

    # Populate data rows
    for row_idx, row in enumerate(rows, start=1):
        for col_idx, cell in enumerate(row):
            if col_idx >= num_cols:
                break
            requests.append({
                "insertText": {
                    "objectId": table_id,
                    "cellLocation": {"rowIndex": row_idx, "columnIndex": col_idx},
                    "text": str(cell),
                    "insertionIndex": 0,
                }
            })
            style, fields = _text_style(font=font, size_pt=body_size_pt)
            if fields:
                requests.append({
                    "updateTextStyle": {
                        "objectId": table_id,
                        "cellLocation": {"rowIndex": row_idx, "columnIndex": col_idx},
                        "style": style,
                        "textRange": {"type": "ALL"},
                        "fields": fields,
                    }
                })

    return table_id, requests


# ── Line ────────────────────────────────────────────────────────────────


def create_line(
    slide_id: str,
    *,
    x1: float = 0.5,
    y1: float = 1.0,
    x2: float = 9.5,
    y2: float = 1.0,
    color: str = "#D1D5DB",
    weight_pt: float = 1.0,
) -> tuple[str, list[dict]]:
    """Create a straight line. Returns (line_id, [requests])."""
    line_id = _object_id()
    w = abs(x2 - x1) or 0.01
    h = abs(y2 - y1) or 0.01
    requests: list[dict] = [
        {
            "createLine": {
                "objectId": line_id,
                "lineCategory": "STRAIGHT",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": inches_to_emu(w), "unit": "EMU"},
                        "height": {"magnitude": inches_to_emu(h), "unit": "EMU"},
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": inches_to_emu(min(x1, x2)),
                        "translateY": inches_to_emu(min(y1, y2)),
                        "unit": "EMU",
                    },
                },
            }
        }
    ]

    if color or weight_pt:
        props: dict[str, Any] = {}
        fields_list: list[str] = []
        if color:
            props["lineFill"] = {
                "solidFill": {"color": {"rgbColor": _rgb_color(color)}}
            }
            fields_list.append("lineFill")
        if weight_pt:
            props["weight"] = {"magnitude": weight_pt, "unit": "PT"}
            fields_list.append("weight")
        requests.append({
            "updateLineProperties": {
                "objectId": line_id,
                "lineProperties": props,
                "fields": ",".join(fields_list),
            }
        })

    return line_id, requests


# ── Slide background ────────────────────────────────────────────────────


def set_slide_background(slide_id: str, color: str) -> dict:
    """Set slide background color. Returns a single request."""
    return {
        "updatePageProperties": {
            "objectId": slide_id,
            "pageProperties": {
                "pageBackgroundFill": {
                    "solidFill": {
                        "color": {"rgbColor": _rgb_color(color)},
                    }
                }
            },
            "fields": "pageBackgroundFill",
        }
    }
