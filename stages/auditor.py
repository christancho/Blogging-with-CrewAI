"""
Stage 9: Content Auditor

Source: semanticpipe evaluate-article pattern.
        astro-seo-forge 30/60/90 day audit workflow.

Post-publish quality scoring and actionable audit checklist. This stage does
NOT modify the article — it only produces a report in ctx.audit_report.

Scoring dimensions (semanticpipe evaluate-article):
- Word count vs. target
- Primary keyword presence and density
- Inline link count (external)
- Internal link count (Worker or placeholder)
- Meta title / meta description presence
- Publish success status

30/60/90 day checklist (astro-seo-forge audit workflow):
- 30 days: indexing, ranking baseline, internal link resolution
- 60 days: ranking comparison, long-tail discoveries, content freshness
- 90 days: full refresh decision, ROI assessment, promotion or archive

Output written to: ctx.audit_report (Dict)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from interfaces import PipelineStage

if TYPE_CHECKING:
    from context import PipelineContext


class AuditorStage(PipelineStage):
    """
    Post-publish content audit with 30/60/90 day checklist.

    Sources: semanticpipe evaluate-article + astro-seo-forge audit model.
    """

    name = "auditor"

    def __init__(self, llm=None, config: Optional[Dict] = None):
        # llm is not used — auditing is deterministic scoring
        self._config = config or {}

    def run(self, ctx: "PipelineContext") -> "PipelineContext":
        article = ctx.final_content or ""
        seo = ctx.seo_brief or {}

        score, issues, recommendations = self._evaluate(article, seo, ctx)
        checklist = self._build_checklist(ctx)

        ctx.audit_report = {
            "score": score,
            "issues": issues,
            "recommendations": recommendations,
            "stats": self._stats(article),
            "checklist_30d": checklist["30d"],
            "checklist_60d": checklist["60d"],
            "checklist_90d": checklist["90d"],
        }
        return ctx

    def quality_gate(self, ctx: "PipelineContext") -> None:
        assert ctx.audit_report is not None, "audit_report must not be None"
        assert "score" in ctx.audit_report, "audit_report must contain score"
        assert 0 <= ctx.audit_report["score"] <= 100, "score must be 0–100"

    def _evaluate(
        self,
        article: str,
        seo: Dict,
        ctx: "PipelineContext",
    ) -> Tuple[float, List[str], List[str]]:
        """Score the final article across multiple SEO dimensions."""
        score = 100.0
        issues: List[str] = []
        recommendations: List[str] = []

        words = article.split()
        word_count = len(words)

        # Word count
        if word_count < 2000:
            score -= 20
            issues.append(f"Article too short: {word_count} words (target 3500)")
            recommendations.append("Expand thin sections to reach 3500-word target")

        # Primary keyword
        primary = seo.get("primary_keyword", "")
        if primary:
            kw_count = article.lower().count(primary.lower())
            density = kw_count / max(word_count, 1) * 100
            if kw_count == 0:
                score -= 20
                issues.append(f"Primary keyword '{primary}' not found in article")
                recommendations.append(f'Weave "{primary}" naturally into the article')
            elif density > 4.0:
                score -= 10
                issues.append(f"Keyword stuffing: {density:.1f}% density for '{primary}'")
                recommendations.append("Reduce primary keyword frequency")

        # Inline external links
        link_count = len(re.findall(r"\[.+?\]\(https?://", article))
        if link_count < 10:
            score -= 15
            issues.append(f"Only {link_count} inline links (minimum 10)")
            recommendations.append("Add more inline hyperlinks from authoritative sources")

        # Internal links (placeholders or resolved)
        internal_count = (
            article.count("[[LINK:")
            + len(re.findall(r"\[.+?\]\(/[^)]+\)", article))
        )
        if internal_count == 0 and ctx.links_inserted == 0:
            score -= 5
            issues.append("No internal links found")
            recommendations.append("Add internal links to related hub pages")

        # Meta elements
        if not seo.get("meta_title"):
            score -= 5
            issues.append("No meta title in SEO brief")
        if not seo.get("meta_description"):
            score -= 5
            issues.append("No meta description in SEO brief")

        # Publish status
        if ctx.publish_result and ctx.publish_result.get("status") != "success":
            score -= 10
            issues.append(
                f"Ghost CMS publish failed: {ctx.publish_result.get('message', '?')}"
            )
            recommendations.append("Retry publish or check Ghost CMS configuration")

        return max(0.0, score), issues, recommendations

    def _stats(self, article: str) -> Dict[str, Any]:
        """
        Basic content statistics — semanticpipe evaluate-article pattern.
        """
        words = article.split()
        sentences = [s for s in re.split(r"[.!?]+", article) if s.strip()]
        h2s = re.findall(r"^## .+$", article, re.MULTILINE)
        external_links = re.findall(r"\[.+?\]\(https?://", article)
        internal_links = re.findall(r"\[.+?\]\(/[^)]+\)", article)
        placeholders = re.findall(r"\[\[LINK:.+?\]\]", article)

        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "h2_count": len(h2s),
            "external_link_count": len(external_links),
            "internal_link_count": len(internal_links) + len(placeholders),
            "avg_words_per_sentence": round(
                len(words) / max(len(sentences), 1), 1
            ),
        }

    def _build_checklist(self, ctx: "PipelineContext") -> Dict[str, List[str]]:
        """
        30/60/90 day post-publish checklist.
        Pattern: astro-seo-forge audit workflow.
        """
        topic = ctx.topic
        primary = (ctx.seo_brief or {}).get("primary_keyword", topic)

        return {
            "30d": [
                f"Check GSC for '{primary}' impressions and initial position",
                "Verify Ghost draft was published and is publicly accessible",
                "Resolve any [[LINK:]] placeholders to real internal URLs",
                "Confirm Brave Search / Google is indexing the new article",
                "Review first-week engagement metrics (time-on-page, scroll depth)",
            ],
            "60d": [
                f"Compare ranking position for '{primary}' vs. Day 1 baseline",
                "Identify long-tail keywords the article is ranking for (GSC)",
                "Update any statistics or data points that may have changed",
                "Add new internal links from recently published hub pages",
                "Review competitor content changes — fill any new gaps",
            ],
            "90d": [
                "Full content refresh if ranking has not materially improved",
                "Assess ROI: organic traffic + affiliate clicks (Viator if applicable)",
                "Promote via email/social if article is performing well",
                "Consider splitting into sub-articles if topic scope is too broad",
                "Archive or redirect if topic relevance has declined",
            ],
        }
