"""
Stage 6: On-Page SEO Optimizer

Source: ARCHITECTURE.md spec (our codebase design).
        semanticpipe — keyword density analysis pattern.

Three-step optimization:
  Step 1 — Structural audit: score the article on SEO dimensions.
  Step 2 — Deterministic patches: H1 = meta_title, meta_description embed.
  Step 3 — LLM keyword pass: only triggered if score < 60 AND issues exist,
            to avoid burning tokens when the article is already well-optimized.

Does NOT change article structure or add/remove links — those are Editor's job.
This stage only adjusts keyword integration and meta embedding.

Output written to: ctx.optimized (str), ctx.seo_score (float, 0–100)
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from interfaces import PipelineStage
from tools import sanitize_output

if TYPE_CHECKING:
    from context import PipelineContext


class OptimizerStage(PipelineStage):
    """
    On-page SEO optimization: keyword density, heading audit, meta embedding.

    Source: ARCHITECTURE.md spec + semanticpipe density analysis.
    """

    name = "optimizer"

    def __init__(self, llm, config: Optional[Dict] = None):
        self._llm = llm
        self._config = config or {}

    def run(self, ctx: "PipelineContext") -> "PipelineContext":
        article = ctx.edited or ctx.draft or ""
        seo = ctx.seo_brief or {}

        if not article:
            ctx.record_error(self.name, "no article to optimize")
            return ctx

        # Step 1: structural audit
        score, issues = self._audit(article, seo)

        # Step 2: deterministic patches (no LLM)
        patched = self._patch(article, seo)

        # Step 3: LLM keyword integration pass (only if score is low)
        if score < 60 and issues:
            patched = self._llm_keyword_pass(patched, ctx.topic, seo, issues)

        # Re-score after patching
        final_score, _ = self._audit(patched, seo)
        ctx.optimized = patched
        ctx.seo_score = final_score
        return ctx

    def quality_gate(self, ctx: "PipelineContext") -> None:
        assert ctx.optimized, "optimized must not be empty"
        assert ctx.seo_score is not None, "seo_score must be set"

    def _audit(self, article: str, seo: Dict) -> Tuple[float, List[str]]:
        """Score the article and return (score_0_100, list_of_issues)."""
        issues: List[str] = []
        score = 100.0
        words = article.split()
        word_count = len(words)

        # Word count
        if word_count < 2000:
            issues.append(f"word count too low: {word_count} (target 3500)")
            score -= 20

        # Primary keyword presence and density
        primary = seo.get("primary_keyword", "")
        if primary:
            kw_count = article.lower().count(primary.lower())
            density = kw_count / max(word_count, 1) * 100
            if density < 0.5:
                issues.append(
                    f"primary keyword density too low: {density:.2f}% (target 0.5–3%)"
                )
                score -= 15
            elif density > 4.0:
                issues.append(
                    f"keyword stuffing detected: {density:.2f}% (cap at 4%)"
                )
                score -= 10

        # H2 headings present
        article_h2s = re.findall(r"^## .+$", article, re.MULTILINE)
        if not article_h2s:
            issues.append("no H2 headings found")
            score -= 15

        # Inline link count
        link_count = len(re.findall(r"\[.+?\]\(https?://", article))
        if link_count < 10:
            issues.append(f"only {link_count} inline links (need ≥10)")
            score -= 10

        # Meta description embedded
        meta = seo.get("meta_description", "")
        if meta and meta not in article:
            issues.append("meta description not embedded in article")
            score -= 5

        return max(0.0, score), issues

    def _patch(self, article: str, seo: Dict) -> str:
        """Apply deterministic structural patches without LLM."""
        meta_title = seo.get("meta_title", "")
        meta_desc = seo.get("meta_description", "")

        # Ensure H1 is the meta title
        if meta_title:
            if not article.startswith("#"):
                article = f"# {meta_title}\n\n{article}"
            else:
                article = re.sub(
                    r"^# .+$",
                    f"# {meta_title}",
                    article,
                    count=1,
                    flags=re.MULTILINE,
                )

        # Embed meta description as italic line below H1 (Ghost CMS convention)
        if meta_desc and meta_desc not in article:
            article = re.sub(
                r"(^# .+\n)",
                f"\\1\n*{meta_desc}*\n",
                article,
                count=1,
                flags=re.MULTILINE,
            )

        article = re.sub(r"\n{3,}", "\n\n", article)
        return article.strip()

    def _llm_keyword_pass(
        self,
        article: str,
        topic: str,
        seo: Dict,
        issues: List[str],
    ) -> str:
        """
        LLM pass to improve keyword integration when score is below threshold.
        Only triggered when score < 60 to avoid unnecessary token spend.
        """
        primary = seo.get("primary_keyword", topic)
        lsi = ", ".join(seo.get("lsi_keywords", []) or [])
        issues_text = "\n".join(f"- {i}" for i in issues)

        prompt = f"""This article on "{topic}" has SEO issues. Fix them while preserving all content.

ISSUES TO FIX:
{issues_text}

SEO TARGETS:
- Primary keyword: {primary}
- LSI keywords: {lsi}

RULES:
1. Integrate the primary keyword naturally in the intro and at least 2 body sections
2. Weave LSI terms naturally — never force them
3. Do NOT change headings, remove links, or alter facts
4. Return the COMPLETE article

ARTICLE:
{article[:10000]}"""

        result = self._llm.run(prompt, max_tokens=8192)
        result = sanitize_output(result)
        return result if result else article
