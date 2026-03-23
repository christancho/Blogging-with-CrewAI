"""
Stage 3: Research

Source: christancho/Blogging-with-CrewAI — Brave Search, multi-query research.
        semanticpipe — three-tier source credibility model.

Runs 4 targeted Brave Search queries guided by the SEO brief, then synthesises
results with the LLM into a structured research brief with credibility tiers.

Three-tier credibility (semanticpipe convention):
  Tier 1 (preferred): .gov, .edu, peer-reviewed, official docs
  Tier 2 (acceptable): established industry publications, reputable news
  Tier 3 (use sparingly): expert blogs, vendor whitepapers

Output written to: ctx.research (str), ctx.research_sources (List[Dict])
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, TYPE_CHECKING

from interfaces import PipelineStage
from tools import BraveSearchTool, sanitize_output

if TYPE_CHECKING:
    from context import PipelineContext


# semanticpipe three-tier credibility heuristics
_TIER1_DOMAINS = (
    ".gov", ".edu", ".ac.", "ncbi.nlm.nih.gov", "arxiv.org", "who.int",
    "nih.gov", "cdc.gov", "ieee.org", "acm.org",
)
_TIER2_DOMAINS = (
    "techcrunch.com", "wired.com", "nature.com", "wikipedia.org",
    "reuters.com", "bbc.com", "nytimes.com", "wsj.com", "theguardian.com",
    "ahrefs.com", "moz.com", "semrush.com",
)


class ResearchStage(PipelineStage):
    """
    Multi-query Brave Search + LLM synthesis with 3-tier source credibility.

    Sources: christancho/Blogging-with-CrewAI + semanticpipe credibility model.
    """

    name = "research"

    def __init__(self, llm, config: Optional[Dict] = None):
        self._llm = llm
        self._config = config or {}
        self._search = BraveSearchTool()

    def run(self, ctx: "PipelineContext") -> "PipelineContext":
        topic = ctx.topic
        seo = ctx.seo_brief or {}

        cluster_kws = seo.get("cluster_keywords", []) or []
        queries = [topic] + cluster_kws[:2] + [
            f"{topic} best practices",
            f"{topic} 2025",
        ]

        raw_results: List[str] = []
        for q in queries[:4]:
            result = self._search._run(q, count=5)
            cleaned = sanitize_output(result)
            if cleaned:
                raw_results.append(f"### Search: {q}\n{cleaned}")

        research_text = "\n\n".join(raw_results)
        primary = seo.get("primary_keyword", topic)

        synthesis = self._synthesise(topic, primary, research_text)
        ctx.research = synthesis if synthesis else research_text
        ctx.research_sources = self._extract_sources(research_text)
        return ctx

    def quality_gate(self, ctx: "PipelineContext") -> None:
        assert ctx.research, "research must not be empty"
        assert len(ctx.research) >= 200, (
            f"research too short ({len(ctx.research)} chars) — likely an API error"
        )

    def _synthesise(self, topic: str, primary_keyword: str, raw: str) -> str:
        """LLM synthesis of raw search results into a structured research brief."""
        prompt = f"""You are a research specialist. Synthesise the following search results
into a coherent research brief for an article on "{topic}" (primary keyword: {primary_keyword}).

Include:
- Key findings grouped by subtopic
- Authoritative URLs with titles and credibility tier labels
- Relevant statistics and data points with sources

THREE-TIER SOURCE CREDIBILITY — label each source:
  Tier 1: .gov, .edu, peer-reviewed, official docs
  Tier 2: Established industry publications, reputable news
  Tier 3: Expert blogs, vendor whitepapers

SEARCH RESULTS:
{raw[:6000]}

Provide a structured research brief with source URLs and credibility tiers."""

        result = self._llm.run(prompt, max_tokens=2048)
        return sanitize_output(result)

    def _classify_tier(self, url: str) -> int:
        """Classify a URL into credibility tier 1, 2, or 3."""
        url_low = url.lower()
        if any(d in url_low for d in _TIER1_DOMAINS):
            return 1
        if any(d in url_low for d in _TIER2_DOMAINS):
            return 2
        return 3

    def _extract_sources(self, raw: str) -> List[Dict]:
        """Extract URLs from raw search results and classify credibility."""
        sources = []
        seen: set = set()
        for m in re.finditer(r"https?://[^\s\]\"'<>]+", raw):
            url = m.group().rstrip(".,)")
            if url not in seen:
                seen.add(url)
                sources.append({"url": url, "tier": self._classify_tier(url)})
        return sources[:20]
