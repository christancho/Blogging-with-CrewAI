"""
Stage 5: Editor

Source: christancho/Blogging-with-CrewAI — quality review, must return FULL article.
        semanticpipe — banned-phrases filter (removes AI-tell phrases that signal
        generated content to search engines and dilute E-E-A-T signals).

Two-pass editing:
  Pass 1 — LLM polish: accuracy check, link audit (≥10), clarity edits.
  Pass 2 — Banned-phrase sweep: deterministic regex removal of flagged phrases.

Output written to: ctx.edited (str), ctx.banned_phrases_removed (int)
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from interfaces import PipelineStage
from tools import sanitize_output

if TYPE_CHECKING:
    from context import PipelineContext


# semanticpipe banned-phrases list — AI-tell phrases that search engines penalise
# and that reduce perceived authoritativeness (E-E-A-T signal).
_DEFAULT_BANNED_PHRASES: List[str] = [
    "as an ai language model",
    "as an ai",
    "i cannot",
    "i'm not able to",
    "i don't have the ability",
    "it's important to note that",
    "it is important to note that",
    "it's worth noting that",
    "certainly! here",
    "sure! here",
    "absolutely! here",
    "in today's digital age",
    "in today's fast-paced world",
    "revolutionizing the way",
    "game-changer",
    "paradigm shift",
    "in the ever-evolving landscape",
    "delve into",
    "let's dive into",
    "leverage",
    "synergies",
    "cutting-edge",
    "state-of-the-art",
    "seamless",
    "holistic approach",
    "robust solution",
    "best-in-class",
    "world-class",
    "at the end of the day",
    "needless to say",
    "it goes without saying",
    "in conclusion, it's clear that",
]


class EditorStage(PipelineStage):
    """
    Two-pass editing: LLM quality review + banned-phrase sweep.

    Sources: christancho/Blogging-with-CrewAI + semanticpipe.
    """

    name = "editor"

    def __init__(
        self,
        llm,
        config: Optional[Dict] = None,
        banned_phrases: Optional[List[str]] = None,
    ):
        self._llm = llm
        self._config = config or {}
        self._banned = (
            banned_phrases if banned_phrases is not None else _DEFAULT_BANNED_PHRASES
        )

    def run(self, ctx: "PipelineContext") -> "PipelineContext":
        article = ctx.draft or ""
        topic = ctx.topic

        if not article:
            ctx.record_error(self.name, "no draft to edit")
            return ctx

        # Pass 1: LLM quality review (Chris pattern — must return FULL article)
        reviewed = self._llm_review(article, topic)

        # Pass 2: Banned-phrase sweep (semanticpipe pattern)
        cleaned, count = self._sweep_banned_phrases(reviewed)

        ctx.edited = cleaned
        ctx.banned_phrases_removed = count
        return ctx

    def quality_gate(self, ctx: "PipelineContext") -> None:
        assert ctx.edited, "edited must not be empty"
        word_count = len(ctx.edited.split())
        assert word_count >= 1500, (
            f"edited article too short: {word_count} words"
        )
        link_count = len(re.findall(r"\[.+?\]\(https?://", ctx.edited))
        assert link_count >= 10, (
            f"edited article has only {link_count} inline links (need ≥10)"
        )

    def _llm_review(self, article: str, topic: str) -> str:
        """
        LLM quality polish — accuracy, link audit, clarity.
        Returns FULL article (Chris pattern: reviewer outputs article, not report).
        """
        prompt = f"""Review and polish this article on "{topic}".

MANDATORY CHECKS:
1. Count inline hyperlinks in the article body — must be at least 10
2. If fewer than 10 links, ADD MORE now using official docs or authoritative sources
3. Verify all links use [anchor text](url) format
4. Check technical accuracy and logical flow
5. Fix grammar or clarity issues

CRITICAL: Return the COMPLETE article — all sections, all paragraphs.
Do NOT return a review report, summary, or list of changes.

ARTICLE:
{article[:12000]}"""

        result = self._llm.run(prompt, max_tokens=8192)
        result = sanitize_output(result)
        return result if result else article

    def _sweep_banned_phrases(self, article: str) -> Tuple[str, int]:
        """
        Deterministic regex removal of banned phrases.
        Returns (cleaned_article, count_of_removals).
        """
        count = 0
        for phrase in self._banned:
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            article, n = pattern.subn("", article)
            count += n

        # Tidy up artifacts left by removals
        article = re.sub(r"  +", " ", article)
        article = re.sub(r"\n{3,}", "\n\n", article)
        return article.strip(), count
