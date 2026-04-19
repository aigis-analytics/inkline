"""DesignContext — explicit user intent for visual direction.

The caller (Claude Code, bridge, API consumer) must ask the user these
questions before invoking design_deck(). Do not infer from content.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DesignContext:
    """Explicit user intent that drives visual direction decisions.

    Attributes:
        audience: Who is the primary audience. e.g., "investors", "board",
            "engineering team", "customers", "internal"
        tone: Desired tone. "authoritative" | "visionary" | "approachable" |
            "data_first" | "urgent"
        focus: What you want the audience to DO after viewing. "persuade" |
            "inform" | "decide" | "inspire" | "report"
        industry: Palette/register hint. "finance" | "tech" | "healthcare" |
            "energy" | "legal" | "real_estate" | etc. (Optional)
        deck_purpose: Free-text description. "Series A pitch", "Q4 board
            review", "product launch announcement", etc. (Optional)
    """

    audience: str
    tone: str
    focus: str
    industry: str = ""
    deck_purpose: str = ""

    def to_prompt_fragment(self) -> str:
        """Formatted for LLM injection into prompts."""
        industry_line = f"- Industry: {self.industry}" if self.industry else ""
        purpose_line = (
            f"- Deck purpose: {self.deck_purpose}" if self.deck_purpose else ""
        )

        return "\n".join(
            filter(
                None,
                [
                    f"- Audience: {self.audience}",
                    f"- Tone: {self.tone}",
                    f"- Focus: {self.focus}",
                    industry_line,
                    purpose_line,
                ],
            )
        )
