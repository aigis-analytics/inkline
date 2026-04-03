"""SlideBuilder — fluent API for constructing Google Slides presentations.

Usage::

    from inkline.slides import SlideBuilder

    deck = (
        SlideBuilder(title="Q1 Report", brand="aigis")
        .authenticate(refresh_token="...", client_id="...", client_secret="...")
        .slide()
            .title("Executive Summary")
            .subtitle("Q1 2026 Performance Review")
        .slide()
            .title("Revenue Breakdown")
            .bullet_list(["Oil: $14.2M", "Gas: $8.1M", "NGL: $2.3M"])
        .slide()
            .title("Financial Overview")
            .table(
                headers=["Metric", "Value", "YoY"],
                rows=[["NPV", "$32M", "+12%"], ["IRR", "18.5%", "+2.1pp"]],
            )
        .build()
    )
    print(deck.url)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from inkline.brands import get_brand, BaseBrand
from inkline.slides import elements as el

log = logging.getLogger(__name__)


@dataclass
class DeckResult:
    """Result of a successful build()."""
    presentation_id: str
    url: str
    slide_ids: list[str]
    title: str
    temp_spreadsheet_ids: list[str] = field(default_factory=list)

    def cleanup_temp_sheets(self, drive_service: Any) -> None:
        """Delete temporary spreadsheets created for charts."""
        for sid in self.temp_spreadsheet_ids:
            try:
                drive_service.files().delete(fileId=sid).execute()
            except Exception as exc:
                log.warning("Failed to delete temp spreadsheet %s: %s", sid, exc)


class SlideContext:
    """Context for building a single slide. Returned by SlideBuilder.slide()."""

    def __init__(self, builder: SlideBuilder, slide_index: int):
        self._builder = builder
        self._slide_index = slide_index
        self._elements: list[dict] = []  # Serialized element specs

    # ── Fluent element methods ──────────────────────────────────────────

    def title(
        self, text: str, *, size_pt: float = 0, color: str = "", y: float = 0.4,
    ) -> SlideContext:
        """Add a title text box."""
        brand = self._builder._brand
        self._elements.append({
            "type": "title",
            "text": text,
            "size_pt": size_pt or brand.heading_size,
            "color": color or brand.surface,
            "y": y,
        })
        return self

    def subtitle(
        self, text: str, *, size_pt: float = 0, color: str = "",
    ) -> SlideContext:
        """Add a subtitle text box below the title."""
        brand = self._builder._brand
        self._elements.append({
            "type": "subtitle",
            "text": text,
            "size_pt": size_pt or brand.body_size + 2,
            "color": color or brand.muted,
        })
        return self

    def text(
        self,
        text: str,
        *,
        x: float = 0.5,
        y: float = 1.5,
        w: float = 9.0,
        h: float = 1.0,
        size_pt: float = 0,
        bold: bool = False,
        italic: bool = False,
        color: str = "",
        alignment: str = "START",
    ) -> SlideContext:
        """Add a free-positioned text box."""
        brand = self._builder._brand
        self._elements.append({
            "type": "text",
            "text": text,
            "x": x, "y": y, "w": w, "h": h,
            "size_pt": size_pt or brand.body_size,
            "bold": bold, "italic": italic,
            "color": color or brand.text,
            "alignment": alignment,
        })
        return self

    def bullet_list(
        self,
        items: list[str],
        *,
        x: float = 0.5,
        y: float = 1.5,
        w: float = 9.0,
        h: float = 4.5,
        size_pt: float = 0,
        color: str = "",
    ) -> SlideContext:
        """Add a bulleted list."""
        brand = self._builder._brand
        self._elements.append({
            "type": "bullets",
            "items": items,
            "x": x, "y": y, "w": w, "h": h,
            "size_pt": size_pt or brand.body_size,
            "color": color or brand.text,
        })
        return self

    def table(
        self,
        headers: list[str],
        rows: list[list[str]],
        *,
        x: float = 0.5,
        y: float = 1.5,
        w: float = 9.0,
        h: float = 4.0,
    ) -> SlideContext:
        """Add a data table."""
        self._elements.append({
            "type": "table",
            "headers": headers,
            "rows": rows,
            "x": x, "y": y, "w": w, "h": h,
        })
        return self

    def image(
        self,
        url: str,
        *,
        x: float = 0.5,
        y: float = 1.5,
        w: float = 9.0,
        h: float = 5.0,
    ) -> SlideContext:
        """Add an image from URL."""
        self._elements.append({
            "type": "image", "url": url,
            "x": x, "y": y, "w": w, "h": h,
        })
        return self

    def chart(
        self,
        headers: list[str],
        rows: list[list[Any]],
        *,
        chart_type: str = "COLUMN",
        x: float = 0.5,
        y: float = 1.5,
        w: float = 9.0,
        h: float = 4.5,
    ) -> SlideContext:
        """Add a chart (creates a temporary Google Sheet)."""
        self._elements.append({
            "type": "chart",
            "headers": headers,
            "rows": rows,
            "chart_type": chart_type,
            "x": x, "y": y, "w": w, "h": h,
        })
        return self

    def divider(
        self, *, y: float = 1.2, color: str = "",
    ) -> SlideContext:
        """Add a horizontal divider line."""
        brand = self._builder._brand
        self._elements.append({
            "type": "divider",
            "y": y,
            "color": color or brand.border,
        })
        return self

    def background(self, color: str) -> SlideContext:
        """Set slide background color."""
        self._elements.append({"type": "background", "color": color})
        return self

    def shape(
        self,
        shape_type: str = "RECTANGLE",
        *,
        x: float = 0, y: float = 0, w: float = 10.0, h: float = 1.0,
        fill_color: str = "",
    ) -> SlideContext:
        """Add a shape (rectangle, rounded rect, etc.)."""
        self._elements.append({
            "type": "shape", "shape_type": shape_type,
            "x": x, "y": y, "w": w, "h": h, "fill_color": fill_color,
        })
        return self

    # ── Navigation ──────────────────────────────────────────────────────

    def slide(self) -> SlideContext:
        """Start a new slide (delegates back to builder)."""
        return self._builder.slide()

    def build(self) -> DeckResult:
        """Build the presentation (delegates back to builder)."""
        return self._builder.build()


class SlideBuilder:
    """Fluent API for constructing Google Slides presentations."""

    def __init__(
        self,
        title: str = "Untitled",
        brand: str | BaseBrand = "aigis",
        *,
        template: str | None = None,
    ):
        self._title = title
        self._brand = get_brand(brand)
        self._template_name = template
        self._slides: list[SlideContext] = []
        self._credentials: Any = None
        self._slides_service: Any = None
        self._sheets_service: Any = None
        self._drive_service: Any = None

    # ── Authentication ──────────────────────────────────────────────────

    def authenticate(
        self,
        *,
        service_account_file: str | Path | None = None,
        token_file: str | Path | None = None,
        refresh_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        client_secrets_file: str | Path | None = None,
        credentials: Any = None,
    ) -> SlideBuilder:
        """Set authentication credentials. Call before build()."""
        if credentials:
            self._credentials = credentials
        else:
            from inkline.slides.auth import get_credentials
            self._credentials = get_credentials(
                service_account_file=service_account_file,
                token_file=token_file,
                refresh_token=refresh_token,
                client_id=client_id,
                client_secret=client_secret,
                client_secrets_file=client_secrets_file,
            )
        return self

    # ── Slide creation ──────────────────────────────────────────────────

    def slide(self) -> SlideContext:
        """Add a new slide and return its context for chaining."""
        ctx = SlideContext(self, len(self._slides))
        self._slides.append(ctx)
        return ctx

    # ── Build ───────────────────────────────────────────────────────────

    def build(self) -> DeckResult:
        """Create the presentation in Google Slides.

        Requires authenticate() to have been called first.
        """
        if not self._credentials:
            raise RuntimeError(
                "Call .authenticate() before .build(). "
                "Provide credentials via service account, OAuth token, or refresh token."
            )

        from inkline.slides.auth import (
            build_slides_service, build_sheets_service, build_drive_service,
        )

        self._slides_service = build_slides_service(self._credentials)
        self._sheets_service = build_sheets_service(self._credentials)
        self._drive_service = build_drive_service(self._credentials)

        # Create empty presentation
        presentation = self._slides_service.presentations().create(
            body={"title": self._title}
        ).execute()
        pres_id = presentation["presentationId"]

        # Collect all batchUpdate requests
        all_requests: list[dict] = []
        slide_ids: list[str] = []
        temp_spreadsheets: list[str] = []

        # Apply template (defaults to DEFAULT_TEMPLATE if none specified)
        template_func = None
        effective_template = self._template_name
        if effective_template is None:
            from inkline.slides.templates import DEFAULT_TEMPLATE
            effective_template = DEFAULT_TEMPLATE
        if effective_template:
            template_func = _get_template(effective_template)

        for idx, slide_ctx in enumerate(self._slides):
            slide_id, create_req = el.create_slide(insertion_index=idx)
            all_requests.append(create_req)
            slide_ids.append(slide_id)

        # First batch: create all slides
        if all_requests:
            self._slides_service.presentations().batchUpdate(
                presentationId=pres_id,
                body={"requests": all_requests},
            ).execute()

        # Delete the default blank slide (it's always at index 0)
        try:
            pres = self._slides_service.presentations().get(
                presentationId=pres_id
            ).execute()
            default_slide_id = pres["slides"][0]["objectId"]
            if default_slide_id not in slide_ids:
                self._slides_service.presentations().batchUpdate(
                    presentationId=pres_id,
                    body={"requests": [{"deleteObject": {"objectId": default_slide_id}}]},
                ).execute()
        except Exception:
            pass

        # Second batch: populate each slide
        for idx, (slide_id, slide_ctx) in enumerate(zip(slide_ids, self._slides)):
            slide_requests: list[dict] = []

            # Apply template base styling if present
            if template_func:
                slide_requests.extend(
                    template_func(slide_id, self._brand, idx, len(self._slides))
                )

            # Process user-defined elements
            for elem in slide_ctx._elements:
                reqs, temp_ids = self._render_element(slide_id, elem)
                slide_requests.extend(reqs)
                temp_spreadsheets.extend(temp_ids)

            # Add branded logo to every slide — pick variant based on actual slide bg
            slide_bg = self._extract_slide_bg(slide_requests)
            logo_reqs = self._add_logo(slide_id, bg_color=slide_bg)
            slide_requests.extend(logo_reqs)

            if slide_requests:
                self._slides_service.presentations().batchUpdate(
                    presentationId=pres_id,
                    body={"requests": slide_requests},
                ).execute()

        url = f"https://docs.google.com/presentation/d/{pres_id}/edit"
        log.info("Created presentation: %s", url)

        return DeckResult(
            presentation_id=pres_id,
            url=url,
            slide_ids=slide_ids,
            title=self._title,
            temp_spreadsheet_ids=temp_spreadsheets,
        )

    # ── Internal rendering ──────────────────────────────────────────────

    def _render_element(
        self, slide_id: str, elem: dict,
    ) -> tuple[list[dict], list[str]]:
        """Convert an element spec dict to batchUpdate requests.

        Returns (requests, temp_spreadsheet_ids).
        """
        requests: list[dict] = []
        temp_sheets: list[str] = []
        brand = self._brand
        etype = elem["type"]

        if etype == "background":
            requests.append(el.set_slide_background(slide_id, elem["color"]))

        elif etype == "title":
            _, reqs = el.create_text_box(
                slide_id, elem["text"],
                x=0.5, y=elem.get("y", 0.4), w=9.0, h=0.8,
                font=brand.heading_font,
                size_pt=elem["size_pt"],
                bold=True,
                color=elem["color"],
            )
            requests.extend(reqs)

        elif etype == "subtitle":
            _, reqs = el.create_text_box(
                slide_id, elem["text"],
                x=0.5, y=1.0, w=9.0, h=0.5,
                font=brand.body_font,
                size_pt=elem["size_pt"],
                color=elem["color"],
            )
            requests.extend(reqs)

        elif etype == "text":
            _, reqs = el.create_text_box(
                slide_id, elem["text"],
                x=elem["x"], y=elem["y"], w=elem["w"], h=elem["h"],
                font=brand.body_font,
                size_pt=elem["size_pt"],
                bold=elem.get("bold", False),
                italic=elem.get("italic", False),
                color=elem["color"],
                alignment=elem.get("alignment", "START"),
            )
            requests.extend(reqs)

        elif etype == "bullets":
            bullet_text = "\n".join(f"\u2022 {item}" for item in elem["items"])
            _, reqs = el.create_text_box(
                slide_id, bullet_text,
                x=elem["x"], y=elem["y"], w=elem["w"], h=elem["h"],
                font=brand.body_font,
                size_pt=elem["size_pt"],
                color=elem["color"],
            )
            requests.extend(reqs)

        elif etype == "table":
            _, reqs = el.create_table(
                slide_id, elem["headers"], elem["rows"],
                x=elem["x"], y=elem["y"], w=elem["w"], h=elem["h"],
                header_bg=brand.surface,
                header_color="#FFFFFF",
                font=brand.body_font,
            )
            requests.extend(reqs)

        elif etype == "image":
            _, req = el.create_image(
                slide_id, elem["url"],
                x=elem["x"], y=elem["y"], w=elem["w"], h=elem["h"],
            )
            requests.append(req)

        elif etype == "chart":
            from inkline.slides.charts import create_chart_in_sheets, embed_chart_in_slide
            ss_id, chart_id = create_chart_in_sheets(
                self._sheets_service,
                f"{self._title} - Chart",
                elem["headers"],
                elem["rows"],
                chart_type=elem["chart_type"],
                colors=brand.chart_colors,
            )
            temp_sheets.append(ss_id)
            _, req = embed_chart_in_slide(
                slide_id, ss_id, chart_id,
                x=elem["x"], y=elem["y"], w=elem["w"], h=elem["h"],
            )
            requests.append(req)

        elif etype == "divider":
            _, reqs = el.create_line(
                slide_id,
                x1=0.5, y1=elem["y"], x2=9.5, y2=elem["y"],
                color=elem["color"], weight_pt=1.0,
            )
            requests.extend(reqs)

        elif etype == "shape":
            _, reqs = el.create_shape(
                slide_id, elem["shape_type"],
                x=elem["x"], y=elem["y"], w=elem["w"], h=elem["h"],
                fill_color=elem.get("fill_color", ""),
            )
            requests.extend(reqs)

        return requests, temp_sheets

    @staticmethod
    def _extract_slide_bg(requests: list[dict]) -> str | None:
        """Extract the background color hex from batchUpdate requests, if set."""
        for req in requests:
            page_props = req.get("updatePageProperties", {})
            bg_fill = (
                page_props
                .get("pageProperties", {})
                .get("pageBackgroundFill", {})
                .get("solidFill", {})
                .get("color", {})
                .get("rgbColor")
            )
            if bg_fill:
                r = int(bg_fill.get("red", 0) * 255)
                g = int(bg_fill.get("green", 0) * 255)
                b = int(bg_fill.get("blue", 0) * 255)
                return f"#{r:02x}{g:02x}{b:02x}"
        return None

    def _add_logo(self, slide_id: str, *, bg_color: str | None = None) -> list[dict]:
        """Add brand logo to a slide (if available)."""
        brand = self._brand
        logo_path = brand.logo_for_bg(bg_color or brand.background)
        if not logo_path or not logo_path.is_file():
            return []

        # Upload logo via Google Drive, then embed
        try:
            from googleapiclient.http import MediaFileUpload

            media = MediaFileUpload(str(logo_path), mimetype="image/png")
            file_meta = {"name": f"inkline_logo_{brand.name}.png"}
            uploaded = self._drive_service.files().create(
                body=file_meta, media_body=media, fields="id,webContentLink",
            ).execute()

            # Make publicly accessible for Slides API
            self._drive_service.permissions().create(
                fileId=uploaded["id"],
                body={"role": "reader", "type": "anyone"},
            ).execute()

            image_url = f"https://drive.google.com/uc?id={uploaded['id']}"

            x, y, w, h = brand.logo_position
            _, req = el.create_image(
                slide_id, image_url, x=x, y=y, w=w, h=h,
            )
            return [req]
        except Exception as exc:
            log.warning("Failed to add logo to slide (non-blocking): %s", exc)
            return []


def _get_template(name: str):
    """Load a template function by name."""
    from inkline.slides.templates import get_template
    return get_template(name)
