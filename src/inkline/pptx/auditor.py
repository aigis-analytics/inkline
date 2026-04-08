"""DeckAuditor -- Archon visual audit layer for PPTX decks.

Opens a generated PPTX in PowerPoint via COM automation, exports each slide
as a PNG image, then runs automated visual quality checks using Pillow.

Checks performed per slide:
  - Empty slide detection (>95% single color)
  - Title visibility (contrast in top 20%)
  - Content balance (left/right density)
  - Text overlap detection (high-contrast boundary clusters)
  - Card spacing validation (rectangular boundary detection)
  - Font rendering check (glyph presence in text regions)

Usage:
    auditor = DeckAuditor()
    report = auditor.audit("output/deck.pptx")
    print(report.summary())
"""

from __future__ import annotations

import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    """Result of a single visual check on one slide."""
    name: str
    passed: bool
    detail: str = ""
    severity: str = "warning"  # "warning" | "error"


@dataclass
class SlideReport:
    """Audit results for a single slide."""
    slide_number: int
    image_path: Path | None = None
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def errors(self) -> list[CheckResult]:
        return [c for c in self.checks if not c.passed and c.severity == "error"]

    @property
    def warnings(self) -> list[CheckResult]:
        return [c for c in self.checks if not c.passed and c.severity == "warning"]


@dataclass
class AuditReport:
    """Full deck audit report."""
    pptx_path: Path
    slides: list[SlideReport] = field(default_factory=list)
    export_dir: Path | None = None

    @property
    def total_checks(self) -> int:
        return sum(len(s.checks) for s in self.slides)

    @property
    def passed_checks(self) -> int:
        return sum(1 for s in self.slides for c in s.checks if c.passed)

    @property
    def score(self) -> float:
        """Quality score 0-100."""
        if self.total_checks == 0:
            return 100.0
        return round(100.0 * self.passed_checks / self.total_checks, 1)

    @property
    def failing_slides(self) -> list[SlideReport]:
        return [s for s in self.slides if not s.passed]

    def summary(self) -> str:
        lines = [
            f"Deck Audit: {self.pptx_path.name}",
            f"  Slides: {len(self.slides)}",
            f"  Score:  {self.score}/100  ({self.passed_checks}/{self.total_checks} checks passed)",
        ]
        for sr in self.slides:
            issues = [c for c in sr.checks if not c.passed]
            if issues:
                lines.append(f"  Slide {sr.slide_number}:")
                for c in issues:
                    tag = "ERROR" if c.severity == "error" else "WARN"
                    lines.append(f"    [{tag}] {c.name}: {c.detail}")
        if not self.failing_slides:
            lines.append("  All checks passed.")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# COM slide exporter
# ---------------------------------------------------------------------------

def export_slides_via_com(
    pptx_path: Path,
    output_dir: Path,
    width: int = 1920,
    height: int = 1080,
) -> list[Path]:
    """Open PPTX in PowerPoint via COM and export each slide as PNG.

    Returns list of PNG paths in slide order.
    Requires Windows with PowerPoint installed and comtypes available.
    """
    import comtypes
    import comtypes.client

    pptx_abs = str(pptx_path.resolve())
    output_dir.mkdir(parents=True, exist_ok=True)

    ppt = comtypes.client.CreateObject("PowerPoint.Application")
    ppt.Visible = 1  # Must be visible for reliable export

    try:
        presentation = ppt.Presentations.Open(pptx_abs, WithWindow=False)
        slides_out: list[Path] = []

        for i, slide in enumerate(presentation.Slides, 1):
            out_path = output_dir / f"slide_{i:03d}.png"
            slide.Export(str(out_path.resolve()), "PNG", width, height)
            slides_out.append(out_path)
            log.debug("Exported slide %d -> %s", i, out_path)

        presentation.Close()
        return slides_out
    finally:
        ppt.Quit()


# ---------------------------------------------------------------------------
# Visual checks (all use PIL/Pillow)
# ---------------------------------------------------------------------------

def _load_image(path: Path):
    """Load image, return PIL Image in RGB mode."""
    from PIL import Image
    return Image.open(path).convert("RGB")


def _pixel_array(img):
    """Get numpy array from PIL image."""
    import numpy as np
    return np.array(img)


def check_empty_slide(img_path: Path, threshold: float = 0.95) -> CheckResult:
    """Flag slides where >threshold fraction is a single color."""
    from PIL import Image
    import numpy as np

    img = _load_image(img_path)
    arr = _pixel_array(img)
    total_pixels = arr.shape[0] * arr.shape[1]

    # Find most common color by quantizing to reduce near-duplicates
    quantized = (arr // 8) * 8  # reduce to ~32 levels per channel
    flat = quantized.reshape(-1, 3)
    # Pack RGB into single int for fast counting
    packed = flat[:, 0].astype(np.int64) * 65536 + flat[:, 1].astype(np.int64) * 256 + flat[:, 2].astype(np.int64)
    unique, counts = np.unique(packed, return_counts=True)
    max_frac = counts.max() / total_pixels

    if max_frac > threshold:
        return CheckResult("empty_slide", False,
                           f"{max_frac:.1%} of pixels are the same color",
                           severity="error")
    return CheckResult("empty_slide", True,
                       f"dominant color covers {max_frac:.1%}")


def check_title_visibility(img_path: Path) -> CheckResult:
    """Check top 20% of slide has sufficient contrast (text vs background)."""
    import numpy as np

    img = _load_image(img_path)
    arr = _pixel_array(img)
    h = arr.shape[0]
    top_region = arr[:int(h * 0.2), :, :]

    # Measure standard deviation of luminance as proxy for contrast
    lum = 0.299 * top_region[:, :, 0] + 0.587 * top_region[:, :, 1] + 0.114 * top_region[:, :, 2]
    std = float(np.std(lum))

    if std < 8.0:
        return CheckResult("title_visibility", False,
                           f"Low contrast in title area (std={std:.1f})",
                           severity="warning")
    return CheckResult("title_visibility", True, f"Title contrast OK (std={std:.1f})")


def check_content_balance(img_path: Path, tolerance: float = 3.0) -> CheckResult:
    """Check left/right halves have roughly equal content density."""
    import numpy as np

    img = _load_image(img_path)
    arr = _pixel_array(img)
    w = arr.shape[1]
    mid = w // 2

    # Content density = stddev of luminance (high = more content)
    lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    left_std = float(np.std(lum[:, :mid]))
    right_std = float(np.std(lum[:, mid:]))

    ratio = max(left_std, right_std) / max(min(left_std, right_std), 0.1)
    if ratio > tolerance:
        return CheckResult("content_balance", False,
                           f"Left/right imbalance: ratio {ratio:.2f}x "
                           f"(L={left_std:.1f}, R={right_std:.1f})",
                           severity="warning")
    return CheckResult("content_balance", True,
                       f"Balanced (ratio {ratio:.2f}x)")


def check_text_overlap(img_path: Path) -> CheckResult:
    """Detect potential text overlap by looking for unusually dense high-contrast edges.

    Uses Sobel edge detection on the luminance channel. Areas with very high
    edge density may indicate overlapping text regions.
    """
    import numpy as np

    img = _load_image(img_path)
    arr = _pixel_array(img)
    lum = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]).astype(np.float32)

    # Simple Sobel-like horizontal gradient
    gx = np.abs(np.diff(lum, axis=1))
    gy = np.abs(np.diff(lum, axis=0))

    # Threshold to find strong edges
    edge_thresh = 30.0
    h_edges = (gx > edge_thresh).astype(np.float32)
    v_edges = (gy > edge_thresh).astype(np.float32)

    # Look for regions with very high edge density (sliding window)
    # Split into 8x8 grid blocks and check edge density per block
    bh, bw = h_edges.shape[0] // 8, h_edges.shape[1] // 8
    overlap_blocks = 0
    total_blocks = 0

    for r in range(8):
        for c in range(8):
            block = h_edges[r*bh:(r+1)*bh, c*bw:(c+1)*bw]
            density = float(block.mean())
            total_blocks += 1
            if density > 0.35:  # >35% pixels are edges = very dense
                overlap_blocks += 1

    if overlap_blocks > 2:
        return CheckResult("text_overlap", False,
                           f"{overlap_blocks} blocks with very high edge density "
                           f"(possible text overlap)",
                           severity="warning")
    return CheckResult("text_overlap", True, "No dense overlap regions detected")


def check_card_spacing(img_path: Path, min_gap_px: int = 20) -> CheckResult:
    """Detect card boundaries and check spacing between them.

    Looks for rectangular regions bounded by edges or color transitions.
    Checks that gaps between detected cards are consistent and adequate.
    """
    import numpy as np

    img = _load_image(img_path)
    arr = _pixel_array(img)
    lum = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]).astype(np.float32)

    h, w = lum.shape

    # Project vertical edges onto x-axis to find card boundaries
    gx = np.abs(np.diff(lum, axis=1))
    edge_proj = (gx > 20.0).sum(axis=0).astype(np.float32)

    # Normalize projection
    edge_proj = edge_proj / h

    # Find peaks in projection (card edges)
    threshold = 0.08  # at least 8% of rows have an edge at this x
    peaks: list[int] = []
    in_peak = False
    for x_pos in range(len(edge_proj)):
        if edge_proj[x_pos] > threshold:
            if not in_peak:
                peaks.append(x_pos)
                in_peak = True
        else:
            in_peak = False

    # Check gaps between consecutive peaks
    if len(peaks) < 2:
        return CheckResult("card_spacing", True, "Fewer than 2 card edges detected")

    gaps = [peaks[i+1] - peaks[i] for i in range(len(peaks) - 1)]
    small_gaps = [g for g in gaps if g < min_gap_px]

    if small_gaps:
        return CheckResult("card_spacing", False,
                           f"Cards too close: {len(small_gaps)} gaps under "
                           f"{min_gap_px}px (smallest: {min(small_gaps)}px)",
                           severity="warning")
    return CheckResult("card_spacing", True,
                       f"Card spacing OK ({len(peaks)} edges, min gap {min(gaps)}px)")


def check_font_rendering(img_path: Path) -> CheckResult:
    """Check that text areas contain rendered glyphs, not empty boxes.

    Text regions should have varied mid-frequency detail. If the slide has
    edge content but very low mid-frequency variation, fonts may be missing.
    """
    import numpy as np

    img = _load_image(img_path)
    arr = _pixel_array(img)
    lum = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]).astype(np.float32)

    # Check mid-frequency energy via downsampled variance
    # Downsample 4x, then compute local variance in 16x16 blocks
    small = lum[::4, ::4]
    bh, bw = 16, 16
    rows, cols = small.shape[0] // bh, small.shape[1] // bw

    active_blocks = 0
    total_blocks = 0
    for r in range(rows):
        for c in range(cols):
            block = small[r*bh:(r+1)*bh, c*bw:(c+1)*bw]
            var = float(np.var(block))
            total_blocks += 1
            if var > 50:  # Block has meaningful variation
                active_blocks += 1

    if total_blocks == 0:
        return CheckResult("font_rendering", True, "No blocks to analyze")

    active_frac = active_blocks / total_blocks

    # A mostly-empty slide might also trigger this, so only flag if
    # there ARE edges but no mid-frequency detail (suggesting tofu boxes)
    gx = np.abs(np.diff(lum, axis=1))
    edge_frac = float((gx > 30).mean())

    if edge_frac > 0.01 and active_frac < 0.02:
        return CheckResult("font_rendering", False,
                           f"Edges present ({edge_frac:.3f}) but very low text detail "
                           f"({active_frac:.3f}) -- possible missing font rendering",
                           severity="error")
    return CheckResult("font_rendering", True,
                       f"Font rendering OK (active={active_frac:.3f}, edges={edge_frac:.3f})")


# ---------------------------------------------------------------------------
# All checks registry
# ---------------------------------------------------------------------------

ALL_CHECKS = [
    check_empty_slide,
    check_title_visibility,
    check_content_balance,
    check_text_overlap,
    check_card_spacing,
    check_font_rendering,
]


# ---------------------------------------------------------------------------
# DeckAuditor
# ---------------------------------------------------------------------------

class DeckAuditor:
    """Automated visual quality auditor for PPTX decks.

    Parameters
    ----------
    export_width : int
        Pixel width for exported slide images.
    export_height : int
        Pixel height for exported slide images.
    checks : list | None
        List of check functions. Defaults to ALL_CHECKS.
    keep_images : bool
        If True, don't delete exported images after audit.
    """

    def __init__(
        self,
        export_width: int = 1920,
        export_height: int = 1080,
        checks: list | None = None,
        keep_images: bool = False,
    ):
        self.export_width = export_width
        self.export_height = export_height
        self.checks = checks or list(ALL_CHECKS)
        self.keep_images = keep_images

    def audit(self, pptx_path: str | Path) -> AuditReport:
        """Run full visual audit on a PPTX file.

        Exports slides via PowerPoint COM, then runs all visual checks.
        Returns an AuditReport with per-slide results.
        """
        pptx_path = Path(pptx_path)
        if not pptx_path.exists():
            raise FileNotFoundError(f"PPTX not found: {pptx_path}")

        # Create temp directory for slide images
        export_dir = Path(tempfile.mkdtemp(prefix="inkline_audit_"))
        report = AuditReport(pptx_path=pptx_path, export_dir=export_dir)

        try:
            # Export slides
            log.info("Exporting slides from %s via PowerPoint COM...", pptx_path.name)
            slide_images = export_slides_via_com(
                pptx_path, export_dir,
                width=self.export_width, height=self.export_height,
            )
            log.info("Exported %d slides to %s", len(slide_images), export_dir)

            # Run checks on each slide
            for i, img_path in enumerate(slide_images, 1):
                sr = SlideReport(slide_number=i, image_path=img_path)
                for check_fn in self.checks:
                    try:
                        result = check_fn(img_path)
                        sr.checks.append(result)
                    except Exception as exc:
                        log.warning("Check %s failed on slide %d: %s",
                                    check_fn.__name__, i, exc)
                        sr.checks.append(CheckResult(
                            check_fn.__name__, False,
                            f"Check error: {exc}", severity="error"))
                report.slides.append(sr)

        except ImportError as exc:
            log.error("COM export unavailable: %s", exc)
            raise RuntimeError(
                "PowerPoint COM automation requires Windows with comtypes installed. "
                f"Import error: {exc}"
            ) from exc
        finally:
            if not self.keep_images:
                shutil.rmtree(export_dir, ignore_errors=True)
                report.export_dir = None

        log.info("Audit complete: %s (score: %.1f/100)", pptx_path.name, report.score)
        return report

    def audit_images(self, image_dir: str | Path) -> AuditReport:
        """Run visual checks on pre-exported slide images.

        Use this when PowerPoint COM is unavailable -- export images manually
        or via another tool, then point this at the directory.

        Images should be named in slide order (e.g., slide_001.png).
        """
        image_dir = Path(image_dir)
        if not image_dir.is_dir():
            raise FileNotFoundError(f"Image directory not found: {image_dir}")

        images = sorted(image_dir.glob("*.png"))
        if not images:
            raise FileNotFoundError(f"No PNG files found in {image_dir}")

        report = AuditReport(
            pptx_path=Path("(pre-exported images)"),
            export_dir=image_dir,
        )

        for i, img_path in enumerate(images, 1):
            sr = SlideReport(slide_number=i, image_path=img_path)
            for check_fn in self.checks:
                try:
                    result = check_fn(img_path)
                    sr.checks.append(result)
                except Exception as exc:
                    log.warning("Check %s failed on slide %d: %s",
                                check_fn.__name__, i, exc)
                    sr.checks.append(CheckResult(
                        check_fn.__name__, False,
                        f"Check error: {exc}", severity="error"))
            report.slides.append(sr)

        log.info("Image audit complete: %d slides (score: %.1f/100)",
                 len(images), report.score)
        return report
