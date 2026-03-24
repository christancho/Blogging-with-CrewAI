"""
Stage 1: Strategy Analysis

Source: MissMathWizz/Multi-Agent-Blog-Generator — competitive positioning.
Adapted: Chris-style behavioral backstory folded into the prompt.

Runs first so keyword research (Stage 2) is informed by market gaps, not
guessed in a vacuum. MathWizz's key contribution: strategy-first sequencing.

Output written to: ctx.strategy (Dict)
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional, TYPE_CHECKING

from interfaces import PipelineStage
from tools import sanitize_output

if TYPE_CHECKING:
    from context import PipelineContext


class StrategyStage(PipelineStage):
    """
    Analyze competitive landscape → structured content strategy JSON.

    Source: MissMathWizz/Multi-Agent-Blog-Generator.
    """

    name = "strategy"

    def __init__(self, llm, config: Optional[Dict] = None):
        self._llm = llm
        self._config = config or {}

    def run(self, ctx: "PipelineContext") -> "PipelineContext":
        topic = ctx.topic

        prompt = f"""As a Strategic Content Analyst, analyze the competitive landscape for:
"{topic}"

Return a JSON dict ONLY (no markdown fences) with these keys:
{{
    "target_audience": {{"primary": "...", "pain_points": ["..."], "preferences": "..."}},
    "competitive_landscape": {{"gaps": ["..."], "opportunities": ["..."]}},
    "content_angles": ["angle1", "angle2", "angle3"],
    "market_opportunities": ["opportunity1", "opportunity2"],
    "strategic_positioning": {{"unique_value": "...", "key_messages": ["..."], "tone": "..."}}
}}

Analysis must cover:
1. TARGET AUDIENCE — demographics, pain points, content preferences
2. COMPETITIVE LANDSCAPE — what competitors publish, what they miss
3. UNIQUE CONTENT ANGLES — 3 distinct approaches that differentiate
4. MARKET OPPORTUNITIES — underserved subtopics, trending angles
5. STRATEGIC POSITIONING — unique value proposition, recommended tone

Return JSON dict ONLY — no preamble, no markdown fences."""

        raw = self._llm.run(prompt, max_tokens=1024)
        raw = sanitize_output(raw)

        if not raw:
            ctx.strategy = self._fallback(topic)
            return ctx

        try:
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            ctx.strategy = json.loads(m.group()) if m else json.loads(raw)
        except Exception:
            ctx.strategy = self._fallback(topic)
            ctx.record_error(self.name, "JSON parse failed — using fallback strategy")

        return ctx

    def quality_gate(self, ctx: "PipelineContext") -> None:
        assert ctx.strategy is not None, "strategy must not be None"
        assert "content_angles" in ctx.strategy, "strategy must contain content_angles"
        assert ctx.strategy["content_angles"], "content_angles must not be empty"

    def _fallback(self, topic: str) -> Dict[str, Any]:
        return {
            "target_audience": {
                "primary": "general audience",
                "pain_points": [],
                "preferences": "",
            },
            "competitive_landscape": {"gaps": [], "opportunities": []},
            "content_angles": [f"Comprehensive guide to {topic}"],
            "market_opportunities": [],
            "strategic_positioning": {
                "unique_value": f"Expert insights on {topic}",
                "key_messages": [],
                "tone": "informative",
            },
        }
