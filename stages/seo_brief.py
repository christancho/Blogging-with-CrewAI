"""
Stage 2: Upstream SEO Brief

Source: MissMathWizz/Multi-Agent-Blog-Generator — SEO runs BEFORE research so
keyword targets shape what the researcher searches for.

GSC integration (astro-seo-forge pattern): when GOOGLE_SEARCH_CONSOLE_SITE and
GSC_TOP_QUERIES are set, real search-console queries are injected as keyword
signals. This replaces guesswork with actual user search data.

Output written to: ctx.seo_brief (Dict)
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional, TYPE_CHECKING

from interfaces import PipelineStage
from tools import sanitize_output

if TYPE_CHECKING:
    from context import PipelineContext


class SEOBriefStage(PipelineStage):
    """
    Produce the full SEO brief (keywords, headings, meta, internal links).

    Sources: MissMathWizz upstream SEO pattern + astro-seo-forge GSC signals.
    """

    name = "seo_brief"

    def __init__(self, llm, config: Optional[Dict] = None):
        self._llm = llm
        self._config = config or {}
        self._gsc_site = os.getenv("GOOGLE_SEARCH_CONSOLE_SITE", "")

    def run(self, ctx: "PipelineContext") -> "PipelineContext":
        topic = ctx.topic
        strategy = ctx.strategy or {}

        angles = strategy.get("content_angles", [topic])
        audience = strategy.get("target_audience", {}).get("primary", "general audience")
        gsc_block = self._get_gsc_signals()

        prompt = f"""As an SEO Specialist, produce a complete SEO brief for: "{topic}"

Context:
- Target audience: {audience}
- Content angles: {', '.join(str(a) for a in angles[:3])}
{gsc_block}

Return a JSON dict ONLY (no markdown fences) with these keys:
{{
    "primary_keyword": "...",
    "cluster_keywords": ["...", "..."],
    "lsi_keywords": ["...", "...", "...", "...", "..."],
    "h2_structure": ["H2 heading 1", "H2 heading 2", "H2 heading 3", "H2 heading 4"],
    "meta_title": "50-60 char title",
    "meta_description": "150-160 char description",
    "internal_link_targets": [{{"anchor": "...", "url": "/..."}}],
    "seo_recommendations": ["tip1", "tip2", "tip3"]
}}

Requirements:
1. PRIMARY KEYWORD — single highest-value keyword for this topic
2. CLUSTER KEYWORDS — 2–3 supporting keywords that form a topical cluster
3. LSI KEYWORDS — 5 latent semantic terms that signal topical authority
4. H2 STRUCTURE — 4 headings reflecting the SEO-optimized content outline
5. META TITLE — 50–60 chars using the primary keyword
6. META DESCRIPTION — 150–160 chars that improve click-through
7. INTERNAL LINK TARGETS — pages on the same site this article should link to
8. SEO RECOMMENDATIONS — 3 specific optimization tips

Return JSON dict ONLY — no preamble, no markdown fences."""

        raw = self._llm.run(prompt, max_tokens=1024)
        raw = sanitize_output(raw)

        if not raw:
            ctx.seo_brief = self._fallback(topic)
            return ctx

        try:
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            ctx.seo_brief = json.loads(m.group()) if m else json.loads(raw)
        except Exception:
            ctx.seo_brief = self._fallback(topic)
            ctx.record_error(self.name, "JSON parse failed — using fallback SEO brief")

        return ctx

    def quality_gate(self, ctx: "PipelineContext") -> None:
        assert ctx.seo_brief is not None, "seo_brief must not be None"
        assert ctx.seo_brief.get("primary_keyword"), "seo_brief must have primary_keyword"
        assert ctx.seo_brief.get("h2_structure"), "seo_brief must have h2_structure"
        assert ctx.seo_brief.get("meta_title"), "seo_brief must have meta_title"

    def _get_gsc_signals(self) -> str:
        """
        Inject real Google Search Console top queries as keyword signals.
        astro-seo-forge pattern: real search data over guessed keywords.

        Reads GSC_TOP_QUERIES env var (comma-separated real queries for the site).
        Returns empty string if not configured.
        """
        if not self._gsc_site:
            return ""
        top_queries = os.getenv("GSC_TOP_QUERIES", "")
        if not top_queries:
            return ""
        return f"- Real GSC top queries for {self._gsc_site}: {top_queries}\n"

    def _fallback(self, topic: str) -> Dict[str, Any]:
        return {
            "primary_keyword": topic,
            "cluster_keywords": [],
            "lsi_keywords": [],
            "h2_structure": [
                f"Understanding {topic}",
                f"How {topic} Works",
                f"Best Practices for {topic}",
                f"Getting Started with {topic}",
            ],
            "meta_title": topic[:60],
            "meta_description": f"A comprehensive guide to {topic}."[:160],
            "internal_link_targets": [],
            "seo_recommendations": [],
        }
