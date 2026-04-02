"""Brand identity system — one definition drives all output formats."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

_ASSETS_DIR = Path(__file__).parent.parent / "assets"


@dataclass
class BaseBrand:
    """Brand identity definition.

    A single brand instance drives consistent styling across HTML, PDF,
    and Google Slides outputs.
    """
    name: str
    display_name: str

    # ── Palette ──────────────────────────────────────────────────────
    primary: str          # Main brand color (headings, accents)
    secondary: str        # Secondary accent
    background: str       # Page/slide background
    surface: str          # Card/table header background
    text: str             # Body text
    muted: str            # Captions, footer text
    light_bg: str         # Alternating rows, code blocks
    border: str           # Borders, rules

    # ── Typography ───────────────────────────────────────────────────
    heading_font: str = "Inter"
    body_font: str = "Inter"
    mono_font: str = "Roboto Mono"
    heading_size: int = 28      # Slide heading size (pt)
    body_size: int = 14         # Slide body size (pt)

    # ── Assets ───────────────────────────────────────────────────────
    logo_dark_path: str = ""    # Logo for dark backgrounds (white/light text)
    logo_light_path: str = ""   # Logo for light backgrounds (dark text)
    font_files: list[str] = field(default_factory=list)

    # ── Document metadata ────────────────────────────────────────────
    confidentiality: str = "Confidential"
    footer_text: str = ""
    tagline: str = ""

    # ── Slide-specific ───────────────────────────────────────────────
    logo_position: tuple[float, float, float, float] = (8.5, 0.3, 1.2, 0.4)

    # ── Chart colors ─────────────────────────────────────────────────
    chart_colors: list[str] = field(default_factory=lambda: [
        "#3fb950", "#58a6ff", "#f0883e", "#d2a8ff", "#e6c069", "#79c0ff",
    ])

    @property
    def logo_dark(self) -> Path:
        """Absolute path to dark-background logo."""
        if self.logo_dark_path:
            p = _ASSETS_DIR / self.logo_dark_path
            if p.exists():
                return p
        return Path()

    @property
    def logo_light(self) -> Path:
        """Absolute path to light-background logo."""
        if self.logo_light_path:
            p = _ASSETS_DIR / self.logo_light_path
            if p.exists():
                return p
        return Path()

    def logo_for_bg(self, bg_color: str) -> Path:
        """Return the appropriate logo variant for a given background color."""
        from inkline.utils import luminance
        if luminance(bg_color) < 0.5:
            return self.logo_dark  # Dark bg → light logo
        return self.logo_light     # Light bg → dark logo

    def font_path(self, index: int = 0) -> Path:
        """Return absolute path to an embedded font file."""
        if index < len(self.font_files):
            p = _ASSETS_DIR / self.font_files[index]
            if p.exists():
                return p
        return Path()


# ── Brand registry ───────────────────────────────────────────────────────

_BRANDS: dict[str, BaseBrand] = {}


def register_brand(brand: BaseBrand) -> None:
    """Register a brand for lookup by name."""
    _BRANDS[brand.name] = brand


def get_brand(name: str | BaseBrand) -> BaseBrand:
    """Get a brand by name or pass through a BaseBrand instance."""
    if isinstance(name, BaseBrand):
        return name
    if name not in _BRANDS:
        raise KeyError(
            f"Unknown brand '{name}'. Available: {', '.join(_BRANDS.keys())}"
        )
    return _BRANDS[name]


def list_brands() -> list[str]:
    """Return names of all registered brands."""
    return list(_BRANDS.keys())


# ── Auto-register built-in brands on import ─────────────────────────────

from inkline.brands.aigis import AigisBrand          # noqa: E402
from inkline.brands.tvf import TvfBrand              # noqa: E402
from inkline.brands.minimal import MinimalBrand      # noqa: E402
from inkline.brands.exmachina import ExMachinaBrand  # noqa: E402
from inkline.brands.statler import StatlerBrand      # noqa: E402

register_brand(AigisBrand)
register_brand(TvfBrand)
register_brand(MinimalBrand)
register_brand(ExMachinaBrand)
register_brand(StatlerBrand)
