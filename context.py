"""
PipelineContext — single typed dataclass that flows through every pipeline stage.

Each stage reads what it needs from ctx and writes its output back.
This is the MathWizz pure-Python dict pattern made type-safe.

All pipeline state lives here. Stages are not allowed to maintain their own
state between calls — everything goes through PipelineContext.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PipelineContext:
    """
    Typed container for all pipeline state.

    Fields are populated incrementally as stages execute.
    Use final_content to get the most-processed article available.
    """

    # ---- Input ----
    topic: str
    profile: Optional[str] = None

    # ---- Stage 1: Strategy (MathWizz) ----
    strategy: Optional[Dict[str, Any]] = None
    # Keys: target_audience, competitive_landscape, content_angles,
    #       market_opportunities, strategic_positioning

    # ---- Stage 2: SEO Brief (MathWizz upstream SEO) ----
    seo_brief: Optional[Dict[str, Any]] = None
    # Keys: primary_keyword, cluster_keywords, lsi_keywords,
    #       h2_structure, meta_title, meta_description,
    #       internal_link_targets, seo_recommendations

    # ---- Stage 3: Research (Chris + 3-tier credibility) ----
    research: Optional[str] = None                   # Synthesised research report
    research_sources: Optional[List[Dict]] = None    # [{url, tier}]

    # ---- Stage 4: Writer (Chris behavioral contracts) ----
    draft: Optional[str] = None                      # Raw 3500-word article

    # ---- Stage 5: Editor (Chris reviewer + semanticpipe banned-phrases) ----
    edited: Optional[str] = None                     # Polished article
    banned_phrases_removed: int = 0                  # Count of phrases cleaned

    # ---- Stage 6: Optimizer (on-page SEO) ----
    optimized: Optional[str] = None                  # SEO-optimised article
    seo_score: Optional[float] = None                # 0–100

    # ---- Stage 7: Linker (internal-linker-worker) ----
    linked: Optional[str] = None                     # Article with internal links
    links_inserted: int = 0                          # Count of links added

    # ---- Stage 8: Publisher (Chris Ghost CMS) ----
    publish_result: Optional[Dict[str, Any]] = None
    # Keys: status, post_id, post_url, draft_url

    # ---- Stage 9: Auditor (semanticpipe evaluate-article + 30/60/90) ----
    audit_report: Optional[Dict[str, Any]] = None
    # Keys: score, issues, recommendations, stats,
    #       checklist_30d, checklist_60d, checklist_90d

    # ---- Metadata ----
    pipeline_path: str = "manual"          # "crewai" | "manual" | "demo"
    stage_timings: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------

    @property
    def final_content(self) -> Optional[str]:
        """Return the most-processed article available."""
        return self.linked or self.optimized or self.edited or self.draft

    @property
    def meta_title(self) -> str:
        if self.seo_brief:
            return self.seo_brief.get("meta_title") or self.topic
        return self.topic

    @property
    def meta_description(self) -> str:
        if self.seo_brief:
            return self.seo_brief.get("meta_description", "")
        return ""

    @property
    def tags(self) -> List[str]:
        if not self.seo_brief:
            return []
        kw = self.seo_brief.get("primary_keyword", "")
        cluster = self.seo_brief.get("cluster_keywords", []) or []
        all_tags = ([kw] if kw else []) + cluster
        return [t for t in all_tags if t][:5]

    def record_error(self, stage_name: str, message: str) -> None:
        """Append a structured error record. Stages call this instead of raising."""
        self.errors.append(f"[{stage_name}] {message}")
