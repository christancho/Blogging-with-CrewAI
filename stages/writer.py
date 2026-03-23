"""
Stage 4: Content Writer

Source: christancho/Blogging-with-CrewAI — behavioral contracts, 3500-word
structure, 10+ inline hyperlinks mandate, H2-guided sections.

The writer receives the SEO brief and research brief as context. It does NOT
decide headings or keywords — those come from Stage 2. This separation ensures
SEO intent (Stage 2) drives content shape, not the other way around.

Output written to: ctx.draft (str)
"""

from __future__ import annotations

import re
from typing import Dict, Optional, TYPE_CHECKING

from interfaces import PipelineStage
from tools import sanitize_output

if TYPE_CHECKING:
    from context import PipelineContext


class WriterStage(PipelineStage):
    """
    Write the full 3500-word article guided by SEO brief and research.

    Source: christancho/Blogging-with-CrewAI.
    """

    name = "writer"

    def __init__(self, llm, config: Optional[Dict] = None):
        self._llm = llm
        self._config = config or {}

    def run(self, ctx: "PipelineContext") -> "PipelineContext":
        topic = ctx.topic
        seo = ctx.seo_brief or {}
        research = ctx.research or f"(No research available for {topic})"

        h2s = seo.get("h2_structure", [])
        primary = seo.get("primary_keyword", topic)
        lsi = ", ".join(seo.get("lsi_keywords", []) or [])
        headings_block = "\n".join(f"  ## {h}" for h in h2s) if h2s else ""

        prompt = f"""Write a COMPLETE 3500-word article on "{topic}".

SEO BRIEF:
- Primary keyword: {primary}
- LSI keywords: {lsi}
- Use these H2 headings in order:
{headings_block if headings_block else "  (generate 4 appropriate H2 headings)"}

RESEARCH BRIEF:
{research[:4000]}

ARTICLE STRUCTURE:
1. Introduction (400–500 words): Hook, context, overview of what readers will learn
2. Section 1 (600–700 words): Foundational concepts with explanations and examples
3. Section 2 (600–700 words): Deeper dive — methodologies, practical applications
4. Section 3 (600–700 words): Advanced concepts, best practices, case studies
5. Section 4 (500–600 words): Future trends, challenges, actionable insights
6. Conclusion (300–400 words): Key takeaways and next steps

CRITICAL — MANDATORY INLINE HYPERLINKS (minimum 10):
- Add links NATURALLY where you mention tools, frameworks, studies, companies
- DO NOT save all links for the References section — embed them in the text
- Distribution: 2–3 in intro, 2–3 per main section
- Format: [anchor text](https://url.com)
- Use URLs from the research brief above

EXAMPLES:
- "According to [OpenAI's documentation](https://platform.openai.com/docs), the API..."
- "Tools like [Docker](https://docker.com) and [Kubernetes](https://kubernetes.io)..."

## References section at end (5–10 numbered sources).

Return the complete article in Markdown format."""

        article = self._llm.run(prompt, max_tokens=8192)
        article = sanitize_output(article)

        ctx.draft = article if article else f"# {topic}\n\n(Article generation failed.)"
        return ctx

    def quality_gate(self, ctx: "PipelineContext") -> None:
        assert ctx.draft, "draft must not be empty"
        word_count = len(ctx.draft.split())
        assert word_count >= 1500, (
            f"draft too short: {word_count} words (minimum 1500 at writer stage)"
        )
        link_count = len(re.findall(r"\[.+?\]\(https?://", ctx.draft))
        assert link_count >= 5, (
            f"draft has only {link_count} inline links (minimum 5 at writer stage)"
        )
