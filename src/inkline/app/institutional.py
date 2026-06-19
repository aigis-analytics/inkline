"""Institutional fixture helpers for editable PPTX sign-off workflows.

This module adds a small execution surface for the weekend vertical slice:

- load YAML / JSON slide specs
- render PDF and PPTX artifacts from those specs
- inspect PPTX editability / fallback heuristics
- render PPTX to PDF via soffice
- audit rendered PPTX artifacts
- compare rendered PDF outputs for parity
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_ROOT = Path("~/.local/share/inkline/output").expanduser()
FIXTURE_PAGE_MAP = {
    "cover": 1,
    "team_grid": 4,
    "institutional_kpi_cards": 5,
    "institutional_timeline": 6,
    "appendix_matrix": 7,
}


@dataclass
class RenderArtifacts:
    pdf_path: Path | None = None
    pptx_path: Path | None = None
    export_metadata_path: Path | None = None


def load_spec_file(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError(
                "YAML spec support requires PyYAML. Install it or use JSON fixtures instead."
            ) from exc
        data = yaml.safe_load(text) or {}
    elif suffix == ".json":
        data = json.loads(text)
    else:
        raise ValueError(f"Unsupported spec file type: {path.suffix}")
    if not isinstance(data, dict):
        raise ValueError("Spec root must be a mapping")
    data.setdefault("slides", [])
    return data


def render_spec_file(
    spec_path: str | Path,
    *,
    formats: list[str],
    output_dir: str | Path | None = None,
    editable_institutional: bool = False,
) -> RenderArtifacts:
    from inkline.pptx import export_pptx_slides
    from inkline.typst import export_typst_slides

    spec = load_spec_file(spec_path)
    slides = spec.get("slides", [])
    title = str(spec.get("title", Path(spec_path).stem))
    brand = str(spec.get("brand", "minimal"))
    template = str(spec.get("template", "consulting"))

    out_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_ROOT / Path(spec_path).stem
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(spec_path).stem

    artifacts = RenderArtifacts()

    if "pdf" in formats:
        artifacts.pdf_path = out_dir / f"{stem}.pdf"
        export_typst_slides(
            slides=slides,
            output_path=str(artifacts.pdf_path),
            brand=brand,
            template=template,
        )

    if "pptx" in formats:
        artifacts.pptx_path = out_dir / f"{stem}.pptx"
        artifacts.export_metadata_path = out_dir / f"{stem}.export_metadata.json"
        export_pptx_slides(
            slides=slides,
            output_path=artifacts.pptx_path,
            brand=brand,
            title=title,
            source_root=Path(spec_path).parent,
            metadata_path=artifacts.export_metadata_path,
            editable_institutional=editable_institutional,
        )

    return artifacts


def inspect_pptx(pptx_path: str | Path) -> dict[str, Any]:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    pptx_path = Path(pptx_path)
    prs = Presentation(str(pptx_path))
    slide_entries: list[dict[str, Any]] = []
    native_count = 0
    fallback_count = 0

    slide_width = prs.slide_width
    slide_height = prs.slide_height

    for idx, slide in enumerate(prs.slides, start=1):
        picture_like = 0
        full_slide_picture = False
        shape_count = len(slide.shapes)
        text_shapes = 0

        for shape in slide.shapes:
            if getattr(shape, "has_text_frame", False):
                text_shapes += 1
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                picture_like += 1
                if (
                    abs(shape.left) < 1000
                    and abs(shape.top) < 1000
                    and abs(shape.width - slide_width) < 2000
                    and abs(shape.height - slide_height) < 2000
                ):
                    full_slide_picture = True

        status = "native"
        fallback_reason = ""
        if full_slide_picture and shape_count <= 2:
            status = "fallback"
            fallback_reason = "full_slide_picture"
            fallback_count += 1
        else:
            native_count += 1

        slide_entries.append(
            {
                "slide_number": idx,
                "shape_count": shape_count,
                "text_shape_count": text_shapes,
                "picture_count": picture_like,
                "status": status,
                "fallback_reason": fallback_reason,
            }
        )

    total = len(slide_entries) or 1
    return {
        "pptx_path": str(pptx_path),
        "slide_count": len(slide_entries),
        "editable_native_ratio": native_count / total,
        "slides_with_image_fallback": [
            s["slide_number"] for s in slide_entries if s["status"] == "fallback"
        ],
        "fallback_reasons": {
            str(s["slide_number"]): s["fallback_reason"]
            for s in slide_entries
            if s["fallback_reason"]
        },
        "slide_statuses": {
            str(s["slide_number"]): s["status"] for s in slide_entries
        },
        "slides": slide_entries,
    }


def render_pptx_via_soffice(
    pptx_path: str | Path,
    *,
    output_dir: str | Path | None = None,
    timeout: int = 90,
) -> Path:
    pptx_path = Path(pptx_path)
    soffice = shutil.which("soffice")
    if not soffice:
        raise RuntimeError("soffice not found on PATH")
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="inkline_soffice_"))
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        soffice,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(out_dir),
        str(pptx_path),
    ]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )
    soffice_pdf = out_dir / f"{pptx_path.stem}.pdf"
    if proc.returncode != 0 or not soffice_pdf.exists():
        raise RuntimeError(
            f"soffice conversion failed rc={proc.returncode}: "
            f"{proc.stdout[-300:]} {proc.stderr[-300:]}"
        )
    rendered = out_dir / f"{pptx_path.stem}.rendered.pdf"
    if rendered.exists():
        rendered.unlink()
    soffice_pdf.rename(rendered)
    return rendered


def audit_pptx(
    pptx_path: str | Path,
    *,
    rubric: str = "institutional",
    brand: str = "",
    output_path: str | Path | None = None,
    rendered_pdf_path: str | Path | None = None,
) -> dict[str, Any]:
    from inkline.intelligence.vishwakarma import critique_pdf

    pptx_path = Path(pptx_path)
    if rendered_pdf_path:
        rendered_pdf = Path(rendered_pdf_path)
    else:
        rendered_tmp = render_pptx_via_soffice(pptx_path)
        rendered_pdf = pptx_path.with_suffix(".rendered.pdf")
        rendered_pdf.write_bytes(rendered_tmp.read_bytes())

    os.environ.setdefault("INKLINE_VISION_PROVIDER", "codex_cli")
    result = critique_pdf(str(rendered_pdf), rubric=rubric, brand=brand).to_dict()
    result["artifact_type"] = "pptx_render"
    result["pptx_path"] = str(pptx_path)
    result["rendered_pdf_path"] = str(rendered_pdf)
    result["provider_trace"] = [{"provider": "codex_cli", "source": "env/default"}]

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def compare_rendered_pdfs(
    baseline_pdf: str | Path,
    rendered_pdf: str | Path,
    *,
    slide_tokens: list[str],
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("pdftoppm not found on PATH")

    with tempfile.TemporaryDirectory(prefix="inkline_compare_") as tmp:
        tmpdir = Path(tmp)
        base_prefix = tmpdir / "base"
        render_prefix = tmpdir / "render"
        subprocess.run([pdftoppm, "-r", "144", "-png", str(baseline_pdf), str(base_prefix)], check=True)
        subprocess.run([pdftoppm, "-r", "144", "-png", str(rendered_pdf), str(render_prefix)], check=True)

        base_images = sorted(tmpdir.glob("base-*.png"))
        render_images = sorted(tmpdir.glob("render-*.png"))

        page_indices = _resolve_slide_tokens(slide_tokens, base_images, render_images)
        slide_scores: list[dict[str, Any]] = []
        for label, page_index in page_indices:
            score = _compare_images(base_images[page_index - 1], render_images[page_index - 1])
            slide_scores.append({"slide": label, "page_index": page_index, "score": score})

    parity_score = sum(item["score"] for item in slide_scores) / max(len(slide_scores), 1)
    report = {
        "baseline_pdf": str(baseline_pdf),
        "rendered_pdf": str(rendered_pdf),
        "parity_diff_score": parity_score,
        "slides": slide_scores,
    }
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _resolve_slide_tokens(
    tokens: list[str],
    base_images: list[Path],
    render_images: list[Path],
) -> list[tuple[str, int]]:
    if len(base_images) != len(render_images):
        raise RuntimeError("baseline and rendered PDFs produced different page counts")
    resolved: list[tuple[str, int]] = []
    for token in tokens:
        raw = token.strip()
        if not raw:
            continue
        if raw.isdigit():
            idx = int(raw)
        else:
            idx = FIXTURE_PAGE_MAP.get(raw)
            if idx is None:
                raise RuntimeError(f"Unknown slide token for parity compare: {raw}")
        if idx < 1 or idx > len(base_images):
            raise RuntimeError(f"Slide/page index out of range for parity compare: {raw} -> {idx}")
        resolved.append((raw, idx))
    return resolved


def _compare_images(lhs: Path, rhs: Path) -> float:
    from PIL import Image, ImageChops

    a = Image.open(lhs).convert("RGB")
    b = Image.open(rhs).convert("RGB")
    if a.size != b.size:
        b = b.resize(a.size)
    diff = ImageChops.difference(a, b)
    hist = diff.histogram()
    total = 0
    max_diff = a.size[0] * a.size[1] * 255 * 3
    for value, count in enumerate(hist):
        channel_value = value % 256
        total += channel_value * count
    return total / max_diff


def dump_json(path: str | Path, payload: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
