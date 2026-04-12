"""Brand identity system — one definition drives all output formats.

The public Inkline package ships with a single built-in brand (``minimal``).
Personal / proprietary brands live **outside** the repository and are loaded
at runtime from a user-controlled directory. This keeps logos, colours,
confidentiality strings, and other identity material private.

User brand discovery
--------------------
On import, Inkline scans the following locations (in order) for ``.py``
files and registers any ``BaseBrand`` instances they define:

1. Every path in the ``INKLINE_BRANDS_DIR`` environment variable
   (colon-separated, like ``$PATH``).
2. ``$XDG_CONFIG_HOME/inkline/brands/`` (default: ``~/.config/inkline/brands/``).
3. ``./inkline_brands/`` in the current working directory.

Asset lookup (logo files, fonts) walks a parallel list:

1. Every path in ``INKLINE_ASSETS_DIR`` (colon-separated).
2. ``~/.config/inkline/assets/``.
3. ``./inkline_assets/`` in the current working directory.
4. The package's bundled ``src/inkline/assets/`` directory (for shipped fonts).

Creating a user brand
---------------------
Drop a Python file in ``~/.config/inkline/brands/`` containing::

    from inkline.brands import BaseBrand

    MyBrand = BaseBrand(
        name="mycorp",
        display_name="My Corporation",
        primary="#0B5FFF", secondary="#00C2A8",
        background="#FFFFFF", surface="#0A2540",
        text="#111827", muted="#6B7280",
        border="#E5E7EB", light_bg="#F8FAFC",
        heading_font="Inter", body_font="Inter",
        logo_dark_path="mycorp_logo_white.png",
        logo_light_path="mycorp_logo_dark.png",
    )

Any top-level ``BaseBrand`` instance in the module will be auto-registered.
"""

from __future__ import annotations

import importlib.util
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

# Bundled asset directory (shipped with the package — fonts, example assets)
_PACKAGE_ASSETS_DIR = Path(__file__).parent.parent / "assets"


def _resolve_dirs(env_var: str, defaults: list[Path]) -> list[Path]:
    """Build an ordered list of existing directories to search."""
    dirs: list[Path] = []
    env_val = os.environ.get(env_var, "")
    if env_val:
        for chunk in env_val.split(os.pathsep):
            if chunk:
                dirs.append(Path(chunk).expanduser())
    dirs.extend(defaults)
    return [d for d in dirs if d.is_dir()]


def _user_brand_dirs() -> list[Path]:
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    defaults = [
        Path(xdg).expanduser() / "inkline" / "brands" if xdg else Path.home() / ".config" / "inkline" / "brands",
        Path.cwd() / "inkline_brands",
    ]
    return _resolve_dirs("INKLINE_BRANDS_DIR", defaults)


def _user_asset_dirs() -> list[Path]:
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    defaults = [
        Path(xdg).expanduser() / "inkline" / "assets" if xdg else Path.home() / ".config" / "inkline" / "assets",
        Path.cwd() / "inkline_assets",
        _PACKAGE_ASSETS_DIR,
    ]
    return _resolve_dirs("INKLINE_ASSETS_DIR", defaults)


def _find_asset(relpath: str) -> Path:
    """Locate an asset file by name, searching all configured asset dirs."""
    if not relpath:
        return Path()
    # Absolute path — trust it
    p = Path(relpath).expanduser()
    if p.is_absolute() and p.exists():
        return p
    for base in _user_asset_dirs():
        candidate = base / relpath
        if candidate.exists():
            return candidate
    return Path()


@dataclass
class BaseBrand:
    """Brand identity definition.

    A single brand instance drives consistent styling across HTML, PDF,
    PPTX, Google Slides, and Typst outputs.
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

    # ── Assets (resolved via user asset dirs + package assets) ───────
    logo_dark_path: str = ""    # Logo for dark backgrounds
    logo_light_path: str = ""   # Logo for light backgrounds
    shield_path: str = ""       # Icon/shield for corner placement (optional)
    font_files: list[str] = field(default_factory=list)

    # ── Document metadata ────────────────────────────────────────────
    confidentiality: str = "Confidential"
    footer_text: str = ""
    tagline: str = ""

    # ── Slide-specific ───────────────────────────────────────────────
    logo_position: tuple[float, float, float, float] = (8.5, 0.3, 1.2, 0.4)

    # ── Header style ─────────────────────────────────────────────────
    header_style: str = "bar"   # "bar" or "document"

    # ── Chart colors ─────────────────────────────────────────────────
    chart_colors: list[str] = field(default_factory=lambda: [
        "#3fb950", "#58a6ff", "#f0883e", "#d2a8ff", "#e6c069", "#79c0ff",
    ])

    @property
    def logo_dark(self) -> Path:
        """Absolute path to dark-background logo."""
        return _find_asset(self.logo_dark_path)

    @property
    def logo_light(self) -> Path:
        """Absolute path to light-background logo."""
        return _find_asset(self.logo_light_path)

    def logo_for_bg(self, bg_color: str) -> Path:
        """Return the appropriate logo variant for a given background color."""
        from inkline.utils import luminance
        if luminance(bg_color) < 0.5:
            return self.logo_dark
        return self.logo_light

    def font_path(self, index: int = 0) -> Path:
        """Return absolute path to an embedded font file."""
        if index < len(self.font_files):
            return _find_asset(self.font_files[index])
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
            f"Unknown brand '{name}'. Available: {', '.join(sorted(_BRANDS.keys()))}"
        )
    return _BRANDS[name]


def list_brands() -> list[str]:
    """Return names of all registered brands."""
    return sorted(_BRANDS.keys())


def brand_search_paths() -> list[Path]:
    """Return the ordered list of directories searched for user brands."""
    return _user_brand_dirs()


def asset_search_paths() -> list[Path]:
    """Return the ordered list of directories searched for assets."""
    return _user_asset_dirs()


# ── Built-in brand (public, open-source example) ────────────────────────

from inkline.brands.minimal import MinimalBrand  # noqa: E402

register_brand(MinimalBrand)


# ── User brand discovery (loads brands from outside the repo) ───────────

def _load_user_brands() -> None:
    """Scan user brand directories and register any BaseBrand instances found."""
    for base in _user_brand_dirs():
        for py_file in sorted(base.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            module_name = f"inkline._user_brands.{py_file.stem}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec is None or spec.loader is None:
                    continue
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
            except Exception as e:
                log.warning("Failed to load user brand %s: %s", py_file, e)
                continue
            # Register any BaseBrand instances defined at module level
            for attr_name in dir(mod):
                if attr_name.startswith("_"):
                    continue
                attr = getattr(mod, attr_name)
                if isinstance(attr, BaseBrand):
                    register_brand(attr)
                    log.debug("Registered user brand: %s (from %s)", attr.name, py_file)


_load_user_brands()
