"""
Pipeline orchestrator — dependency injection, quality gates, per-stage timing.

Pattern: MathWizz pure-Python method-chain made explicit as a class,
wrapped with Nimish-style error isolation (stages never abort the pipeline).

Usage:
    from orchestrator import build_pipeline

    # Default 9-stage pipeline with Anthropic LLM
    pipeline = build_pipeline()
    ctx = pipeline.run("Ghost tours in New Orleans")

    # Custom LLM, no publisher (dry run)
    from llm import AnthropicLLM
    pipeline = build_pipeline(llm=AnthropicLLM(), include_publisher=False)
    ctx = pipeline.run("Biblical archaeology")

    # Inspect results
    print(ctx.final_content)
    print(ctx.audit_report)
    print(ctx.stage_timings)
"""

from __future__ import annotations

import time
from typing import List, Optional

from context import PipelineContext
from interfaces import PipelineStage


class Orchestrator:
    """
    Run pipeline stages sequentially, passing PipelineContext through each.

    Execution model (Nimish dual-path distilled):
    - Each stage is self-contained and isolated
    - Exceptions inside a stage are caught, logged to ctx.errors, and the
      pipeline continues with the next stage
    - Quality gate failures are soft — logged but not fatal
    - All stage timings recorded in ctx.stage_timings

    Stages are injected at construction time (DI pattern) so they are
    swappable without touching orchestrator code.
    """

    def __init__(self, stages: List[PipelineStage]):
        self.stages = stages

    def run(self, topic: str, profile: Optional[str] = None) -> PipelineContext:
        """
        Execute all stages for the given topic.
        Returns the fully-populated PipelineContext.
        """
        ctx = PipelineContext(topic=topic, profile=profile)

        stage_names = " → ".join(s.name for s in self.stages)
        print(f"\n[Orchestrator] Pipeline: '{topic}'")
        print(f"[Orchestrator] {len(self.stages)} stages: {stage_names}")
        print("-" * 60)

        for stage in self.stages:
            t0 = time.time()
            try:
                print(f"\n[{stage.name}] Running...")
                ctx = stage.run(ctx)

                # Soft quality gate — log failures but continue
                try:
                    stage.quality_gate(ctx)
                    print(f"[{stage.name}] Quality gate: PASS")
                except AssertionError as gate_err:
                    msg = str(gate_err)
                    print(f"[{stage.name}] Quality gate: FAIL — {msg}")
                    ctx.record_error(stage.name, f"quality gate: {msg}")

            except Exception as exc:
                msg = f"stage crashed: {exc}"
                print(f"[{stage.name}] ERROR: {msg}")
                ctx.record_error(stage.name, msg)
            finally:
                elapsed = time.time() - t0
                ctx.stage_timings[stage.name] = elapsed
                print(f"[{stage.name}] {elapsed:.1f}s")

        total = time.time() - ctx.started_at
        print(f"\n[Orchestrator] Complete in {total:.1f}s")

        if ctx.errors:
            print(f"[Orchestrator] {len(ctx.errors)} issue(s):")
            for err in ctx.errors:
                print(f"  {err}")

        return ctx


def build_pipeline(
    llm=None,
    include_publisher: bool = True,
    include_auditor: bool = True,
) -> Orchestrator:
    """
    Build the default pipeline with all stages and dependency injection.

    Stage order (MathWizz sequencing standard):
      1. strategy   — competitive positioning (MathWizz)
      2. seo_brief  — keyword brief upstream, before research (MathWizz)
      3. research   — Brave Search + 3-tier credibility (Chris + semanticpipe)
      4. writer     — 3500-word draft, 10+ hyperlinks (Chris)
      5. editor     — LLM polish + banned-phrase sweep (Chris + semanticpipe)
      6. optimizer  — on-page SEO checks + deterministic patches (ours)
      7. linker     — internal links: Worker API or placeholders (ours)
      8. publisher  — Ghost CMS draft via JWT (Chris) [optional]
      9. auditor    — 30/60/90 audit checklist (semanticpipe + astro-seo-forge) [optional]

    Args:
        llm:               AnthropicLLM instance (created if None)
        include_publisher: Set False for dry-run / testing (skips Ghost CMS call)
        include_auditor:   Set False to skip audit report generation
    """
    if llm is None:
        from llm import AnthropicLLM
        llm = AnthropicLLM()

    from stages.strategy import StrategyStage
    from stages.seo_brief import SEOBriefStage
    from stages.research import ResearchStage
    from stages.writer import WriterStage
    from stages.editor import EditorStage
    from stages.optimizer import OptimizerStage
    from stages.linker import LinkerStage
    from stages.publisher import PublisherStage
    from stages.auditor import AuditorStage

    stages: List[PipelineStage] = [
        StrategyStage(llm=llm),
        SEOBriefStage(llm=llm),
        ResearchStage(llm=llm),
        WriterStage(llm=llm),
        EditorStage(llm=llm),
        OptimizerStage(llm=llm),
        LinkerStage(llm=llm),
    ]

    if include_publisher:
        stages.append(PublisherStage(llm=llm))

    if include_auditor:
        stages.append(AuditorStage(llm=llm))

    return Orchestrator(stages)
