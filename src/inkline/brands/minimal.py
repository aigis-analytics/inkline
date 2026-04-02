"""Minimal brand — clean, unbranded default."""

from inkline.brands import BaseBrand

MinimalBrand = BaseBrand(
    name="minimal",
    display_name="",

    primary="#1F2328",
    secondary="#0969DA",
    background="#FFFFFF",
    surface="#F6F8FA",
    text="#1F2328",
    muted="#57606A",
    light_bg="#F6F8FA",
    border="#D0D7DE",

    heading_font="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif",
    body_font="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif",

    confidentiality="",
    footer_text="",
)
