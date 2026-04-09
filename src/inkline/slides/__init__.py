"""Inkline Slides — Google Slides generation with brand support.

Usage::

    from inkline.slides import SlideBuilder

    deck = (
        SlideBuilder(title="Project Report", brand="minimal")
        .authenticate(refresh_token="...", client_id="...", client_secret="...")
        .slide()
            .title("Executive Summary")
            .bullet_list(["Point 1", "Point 2"])
        .slide()
            .title("Financial Overview")
            .table(headers=["Metric", "Value"], rows=[["NPV", "$32M"]])
        .build()
    )
    print(deck.url)

Templates::

    deck = (
        SlideBuilder(title="Q1 Report", brand="minimal", template="newspaper")
        .authenticate(...)
        .slide().title("Breaking News").text("...")
        .build()
    )

Available templates: newspaper, minimalism, executive
"""

from inkline.slides.builder import SlideBuilder, DeckResult

__all__ = ["SlideBuilder", "DeckResult"]
