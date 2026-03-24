"""
Stage 7: Internal Linker

Source: poolboy17/internal-linker-worker — Cloudflare Worker + KV store.

Two modes — the real one first, fallback second:

  Mode 1 — Worker API (primary): queries the live internal-linker-worker at
    INTERNAL_LINKER_URL/suggest, receives anchor→URL suggestions from the
    Cloudflare KV store, inserts real Markdown links [anchor](url).

  Mode 2 — SEO brief placeholders (fallback): inserts [[LINK: anchor → /url]]
    placeholder syntax from ctx.seo_brief.internal_link_targets. Used when no
    Worker endpoint is configured. Placeholders are resolved at publish time.

Worker API contract (poolboy17/internal-linker-worker):
  POST {INTERNAL_LINKER_URL}/suggest
  Body: {"text": "...", "topic": "..."}
  Response: {"links": [{"anchor": "...", "url": "...", "score": 0.9}]}

Environment variables:
  INTERNAL_LINKER_URL       — Worker endpoint (enables Mode 1 when set)
  INTERNAL_LINKER_MAX_LINKS — Max links to insert (default: 5)

Output written to: ctx.linked (str), ctx.links_inserted (int)
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

import requests

from interfaces import PipelineStage

if TYPE_CHECKING:
    from context import PipelineContext


class LinkerStage(PipelineStage):
    """
    Internal link insertion: Cloudflare Worker API (real) or SEO brief (fallback).

    Source: poolboy17/internal-linker-worker.
    """

    name = "linker"

    def __init__(self, llm=None, config: Optional[Dict] = None):
        # llm is optional — linker is deterministic, no LLM calls needed
        self._config = config or {}
        self._worker_url = os.getenv("INTERNAL_LINKER_URL", "").rstrip("/")
        self._max_links = int(os.getenv("INTERNAL_LINKER_MAX_LINKS", "5"))

    def run(self, ctx: "PipelineContext") -> "PipelineContext":
        article = ctx.optimized or ctx.edited or ctx.draft or ""

        if not article:
            ctx.record_error(self.name, "no article to link")
            return ctx

        if self._worker_url:
            linked, count = self._link_via_worker(article, ctx.topic)
        else:
            seo = ctx.seo_brief or {}
            linked, count = self._link_via_seo_brief(article, seo)

        ctx.linked = linked
        ctx.links_inserted = count
        return ctx

    def quality_gate(self, ctx: "PipelineContext") -> None:
        assert ctx.linked, "linked must not be empty"

    # ------------------------------------------------------------------
    # Mode 1: Cloudflare Worker API (poolboy17/internal-linker-worker)
    # ------------------------------------------------------------------

    def _link_via_worker(self, article: str, topic: str) -> Tuple[str, int]:
        """
        Query the internal-linker-worker for URL suggestions from KV store.
        Falls back to placeholder mode if the Worker is unreachable.
        """
        try:
            resp = requests.post(
                f"{self._worker_url}/suggest",
                json={"text": article[:4000], "topic": topic},
                timeout=10,
            )
            if resp.status_code != 200:
                return self._link_via_seo_brief(article, {})

            suggestions = resp.json().get("links", [])
            return self._insert_links(article, suggestions, use_placeholder=False)
        except Exception:
            # Worker unreachable — degrade gracefully to placeholder mode
            return self._link_via_seo_brief(article, {})

    # ------------------------------------------------------------------
    # Mode 2: SEO brief placeholders
    # ------------------------------------------------------------------

    def _link_via_seo_brief(self, article: str, seo: Dict) -> Tuple[str, int]:
        """
        Insert [[LINK: anchor → /url]] placeholders from SEO brief.
        Mirrors main.py _manual_internal_links() — now a proper stage.
        """
        targets = seo.get("internal_link_targets", []) or []
        suggestions = [
            {"anchor": t.get("anchor", ""), "url": t.get("url", "")}
            for t in targets
            if t.get("anchor") and t.get("url")
        ]
        if not suggestions:
            return article, 0
        return self._insert_links(article, suggestions, use_placeholder=True)

    # ------------------------------------------------------------------
    # Shared insertion logic
    # ------------------------------------------------------------------

    def _insert_links(
        self,
        article: str,
        suggestions: List[Dict],
        use_placeholder: bool,
    ) -> Tuple[str, int]:
        """
        Insert links at natural anchor positions.
        Skips headings, lines that already have links, and forced placements.
        """
        lines = article.split("\n")
        insertions = 0

        for suggestion in suggestions:
            if insertions >= self._max_links:
                break

            anchor = suggestion.get("anchor", "")
            url = suggestion.get("url", "")
            if not anchor or not url:
                continue

            pattern = re.compile(re.escape(anchor), re.IGNORECASE)

            for i, line in enumerate(lines):
                # Skip headings, existing links, existing placeholders
                if (
                    line.startswith("#")
                    or "[[LINK:" in line
                    or "](http" in line
                    or "](/)" in line
                    or not pattern.search(line)
                ):
                    continue

                if use_placeholder:
                    replacement = f"[[LINK: {anchor} → {url}]]"
                else:
                    replacement = f"[{anchor}]({url})"

                lines[i] = pattern.sub(replacement, line, count=1)
                insertions += 1
                break

        return "\n".join(lines), insertions
