"""Google Sheets → Slides chart embedding.

Charts in Google Slides require a Google Sheets intermediary:
1. Create a temporary spreadsheet with the data
2. Create a chart in the spreadsheet
3. Embed the chart in the slide
"""

from __future__ import annotations

import logging
from typing import Any

from inkline.utils import inches_to_emu

log = logging.getLogger(__name__)


def create_chart_in_sheets(
    sheets_service: Any,
    title: str,
    headers: list[str],
    rows: list[list[Any]],
    *,
    chart_type: str = "COLUMN",
    colors: list[str] | None = None,
) -> tuple[str, int]:
    """Create a spreadsheet with data and a chart.

    Args:
        sheets_service: Google Sheets API service object.
        title: Spreadsheet title.
        headers: Column headers.
        rows: Data rows.
        chart_type: One of COLUMN, BAR, LINE, PIE, AREA, SCATTER.
        colors: Optional list of hex colors for data series.

    Returns:
        (spreadsheet_id, chart_id) tuple.
    """
    # Create spreadsheet with data
    num_rows = len(rows) + 1
    num_cols = len(headers)
    sheet_id = 0

    spreadsheet = sheets_service.spreadsheets().create(
        body={
            "properties": {"title": title},
            "sheets": [{"properties": {"sheetId": sheet_id, "title": "Data"}}],
        }
    ).execute()
    spreadsheet_id = spreadsheet["spreadsheetId"]

    # Write data
    values = [headers] + rows
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Data!A1",
        valueInputOption="RAW",
        body={"values": values},
    ).execute()

    # Build chart spec
    series = []
    for col_idx in range(1, num_cols):
        s: dict[str, Any] = {
            "series": {
                "sourceRange": {
                    "sources": [{
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": num_rows,
                        "startColumnIndex": col_idx,
                        "endColumnIndex": col_idx + 1,
                    }]
                }
            },
            "targetAxis": "LEFT_AXIS",
        }
        if colors and col_idx - 1 < len(colors):
            from inkline.utils import hex_to_rgb
            r, g, b = hex_to_rgb(colors[col_idx - 1])
            s["colorStyle"] = {
                "rgbColor": {"red": r / 255, "green": g / 255, "blue": b / 255}
            }
        series.append(s)

    domain = {
        "domain": {
            "sourceRange": {
                "sources": [{
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": num_rows,
                    "startColumnIndex": 0,
                    "endColumnIndex": 1,
                }]
            }
        }
    }

    chart_type_map = {
        "COLUMN": "basicChart",
        "BAR": "basicChart",
        "LINE": "basicChart",
        "AREA": "basicChart",
        "SCATTER": "basicChart",
        "PIE": "pieChart",
    }
    spec_key = chart_type_map.get(chart_type, "basicChart")

    if spec_key == "pieChart":
        chart_spec = {
            "pieChart": {
                "legendPosition": "RIGHT_LEGEND",
                "domain": domain["domain"],
                "series": series[0]["series"] if series else {},
            }
        }
    else:
        chart_spec = {
            "basicChart": {
                "chartType": chart_type,
                "legendPosition": "BOTTOM_LEGEND",
                "domains": [domain],
                "series": series,
                "headerCount": 1,
            }
        }

    # Add chart to sheet
    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [{
                "addChart": {
                    "chart": {
                        "spec": chart_spec,
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": sheet_id,
                                    "rowIndex": num_rows + 1,
                                    "columnIndex": 0,
                                }
                            }
                        },
                    }
                }
            }]
        },
    ).execute()

    chart_id = result["replies"][0]["addChart"]["chart"]["chartId"]
    log.info("Created chart %d in spreadsheet %s", chart_id, spreadsheet_id)
    return spreadsheet_id, chart_id


def embed_chart_in_slide(
    slide_id: str,
    spreadsheet_id: str,
    chart_id: int,
    *,
    x: float = 0.5,
    y: float = 1.5,
    w: float = 9.0,
    h: float = 4.5,
    linking_mode: str = "NOT_LINKED_IMAGE",
) -> tuple[str, dict]:
    """Create a Slides API request to embed a Sheets chart.

    Args:
        linking_mode: LINKED (updates with sheet) or NOT_LINKED_IMAGE (static snapshot).

    Returns:
        (element_id, request) tuple.
    """
    from inkline.slides.elements import _object_id

    elem_id = _object_id()
    req = {
        "createSheetsChart": {
            "objectId": elem_id,
            "spreadsheetId": spreadsheet_id,
            "chartId": chart_id,
            "linkingMode": linking_mode,
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
