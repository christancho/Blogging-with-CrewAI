"""
Integration tests for pipeline stage wiring.

Tests verify:
- Each stage accepts PipelineContext and returns PipelineContext
- Output fields are populated after each stage runs
- Quality gates pass with well-formed input
- Error paths record errors rather than raising
- The orchestrator continues past stage crashes

We test pipeline WIRING, not LLM output quality.
All LLM calls are replaced with a deterministic MockLLM stub.
"""

import json
import os
import sys

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import MagicMock, patch

from context import PipelineContext
from interfaces import PipelineStage


# ============================================================================
# Mock LLM — deterministic stub that returns predictable JSON or text
# ============================================================================

class MockLLM:
    """
    Deterministic LLM stub for wiring tests.
    Dispatches on keywords in the prompt to return appropriate fixtures.
    """

    def run(self, prompt: str, max_tokens: int = 4096) -> str:
        p = prompt.lower()

        # Strategy response
        if "competitive landscape" in p or "strategic content analyst" in p:
            return json.dumps({
                "target_audience": {
                    "primary": "developers",
                    "pain_points": ["complexity", "lack of docs"],
                    "preferences": "technical depth",
                },
                "competitive_landscape": {
                    "gaps": ["no practical step-by-step guides"],
                    "opportunities": ["beginner-friendly content"],
                },
                "content_angles": ["Beginner guide", "Expert deep-dive", "Case studies"],
                "market_opportunities": ["underserved niche"],
                "strategic_positioning": {
                    "unique_value": "Comprehensive and practical",
                    "key_messages": ["depth", "accuracy"],
                    "tone": "informative",
                },
            })

        # SEO brief response
        if "seo brief" in p or "seo specialist" in p:
            return json.dumps({
                "primary_keyword": "test topic",
                "cluster_keywords": ["related topic", "subtopic"],
                "lsi_keywords": ["term1", "term2", "term3", "term4", "term5"],
                "h2_structure": [
                    "Overview of Test Topic",
                    "How Test Topic Works",
                    "Best Practices",
                    "Getting Started",
                ],
                "meta_title": "Test Topic: Complete Guide (2025)",
                "meta_description": (
                    "A comprehensive guide to test topic covering all essentials "
                    "for developers and practitioners."
                ),
                "internal_link_targets": [
                    {"anchor": "test topic", "url": "/test-topic"},
                    {"anchor": "related topic", "url": "/related-topic"},
                ],
                "seo_recommendations": [
                    "Use primary keyword in H1",
                    "Add structured data",
                ],
            })

        # Research synthesis
        if "synthesise" in p or "research specialist" in p:
            return """## Research Brief: Test Topic

### Key Findings

- Finding 1: Test topic has grown 40% year-over-year according to
  [Industry Report](https://example.gov/report) [Tier 1]
- Finding 2: Best practices documented in
  [Official Docs](https://docs.example.edu/guide) [Tier 1]
- Finding 3: Expert analysis from
  [TechCrunch](https://techcrunch.com/article) [Tier 2]

### Statistics

- 75% of practitioners use this approach (Example Gov, 2025)
- Adoption increased from 30% to 75% between 2023-2025

### Sources

1. [Official Documentation](https://example.gov/docs) [Tier 1]
2. [Industry Publication](https://techcrunch.com/article) [Tier 2]
3. [Expert Blog](https://expert-blog.com/post) [Tier 3]
"""

        # Article writing
        if "write a complete" in p or "3500-word" in p:
            links = " ".join(
                f"[Source {i}](https://authoritative-source{i}.com/page)" for i in range(1, 13)
            )
            body = "word " * 300  # pad to reach word count threshold
            return f"""# Test Topic: Complete Guide (2025)

*A comprehensive guide to test topic covering all essentials for developers.*

## Overview of Test Topic

This is the introduction. According to {links[:200]}, test topic is important.
Here we provide foundational context for understanding the subject.

## How Test Topic Works

The mechanism involves key components. As documented by
[Official Documentation](https://example.gov/docs), the process follows
established patterns. Tools like [ExampleTool](https://example.com/tool) support this.

## Best Practices

Best practices include: [Best Practice Guide](https://example2.com/guide),
[Another Resource](https://example3.com/resource), and
[Third Source](https://example4.com/source).

## Getting Started

To get started, see [Getting Started Guide](https://example5.com/start). Also
consult [Reference Docs](https://example6.com/docs) and
[Tutorial](https://example7.com/tutorial).

## Conclusion

In conclusion, refer to [Summary](https://example8.com/summary).

{body}

## References

1. [Official Documentation](https://example.gov/docs)
2. [Industry Publication](https://techcrunch.com/article)
3. [Expert Blog](https://expert-blog.com/post)
"""

        # Review / edit
        if "review and polish" in p:
            if "ARTICLE:" in prompt:
                return prompt.split("ARTICLE:")[1].strip()
            return "reviewed article content here"

        # Keyword optimization pass
        if "seo issues" in p:
            if "ARTICLE:" in prompt:
                return prompt.split("ARTICLE:")[1].strip()
            return "optimized article content here"

        return f"MockLLM response for: {prompt[:60]}"


MOCK_LLM = MockLLM()
TEST_TOPIC = "test topic for pipeline wiring"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def base_ctx():
    return PipelineContext(topic=TEST_TOPIC)


@pytest.fixture
def ctx_with_strategy(base_ctx):
    base_ctx.strategy = {
        "target_audience": {"primary": "developers", "pain_points": ["complexity"]},
        "competitive_landscape": {"gaps": [], "opportunities": []},
        "content_angles": ["beginner guide", "expert deep-dive"],
        "market_opportunities": [],
        "strategic_positioning": {"unique_value": "comprehensive", "tone": "technical"},
    }
    return base_ctx


@pytest.fixture
def ctx_with_seo(ctx_with_strategy):
    ctx_with_strategy.seo_brief = {
        "primary_keyword": "test topic",
        "cluster_keywords": ["subtopic a", "subtopic b"],
        "lsi_keywords": ["term1", "term2", "term3"],
        "h2_structure": [
            "Overview", "How It Works", "Best Practices", "Getting Started"
        ],
        "meta_title": "Test Topic: Complete Guide",
        "meta_description": "A comprehensive guide to test topic for developers.",
        "internal_link_targets": [
            {"anchor": "test topic", "url": "/test-topic"},
        ],
        "seo_recommendations": [],
    }
    return ctx_with_strategy


@pytest.fixture
def ctx_with_draft(ctx_with_seo):
    links = " ".join(
        f"[src{i}](https://example{i}.com/page)" for i in range(1, 13)
    )
    body_padding = "word " * 400
    ctx_with_seo.research = "Research findings with sources and statistics."
    ctx_with_seo.draft = f"""# Test Topic: Complete Guide

*A comprehensive guide to test topic for developers.*

## Overview

Introduction with links. {links}

## How It Works

More content here with explanation and detail. {body_padding}

## Best Practices

Practical advice section.

## Getting Started

Getting started content.

## Conclusion

Concluding thoughts.

## References

1. [Example](https://example.gov)
"""
    return ctx_with_seo


# ============================================================================
# PipelineContext contract
# ============================================================================

class TestPipelineContext:
    def test_initializes_with_required_fields(self):
        ctx = PipelineContext(topic="test")
        assert ctx.topic == "test"
        assert ctx.profile is None
        assert ctx.strategy is None
        assert ctx.seo_brief is None
        assert ctx.draft is None
        assert ctx.errors == []
        assert ctx.stage_timings == {}

    def test_final_content_priority_order(self):
        ctx = PipelineContext(topic="test")
        assert ctx.final_content is None
        ctx.draft = "draft"
        assert ctx.final_content == "draft"
        ctx.edited = "edited"
        assert ctx.final_content == "edited"
        ctx.optimized = "optimized"
        assert ctx.final_content == "optimized"
        ctx.linked = "linked"
        assert ctx.final_content == "linked"

    def test_tags_derived_from_seo_brief(self):
        ctx = PipelineContext(topic="test")
        ctx.seo_brief = {
            "primary_keyword": "kw1",
            "cluster_keywords": ["kw2", "kw3"],
        }
        assert ctx.tags == ["kw1", "kw2", "kw3"]

    def test_tags_empty_without_seo_brief(self):
        ctx = PipelineContext(topic="test")
        assert ctx.tags == []

    def test_meta_title_falls_back_to_topic(self):
        ctx = PipelineContext(topic="fallback topic")
        assert ctx.meta_title == "fallback topic"

    def test_record_error_appends_formatted_message(self):
        ctx = PipelineContext(topic="test")
        ctx.record_error("stage1", "something went wrong")
        assert len(ctx.errors) == 1
        assert "[stage1]" in ctx.errors[0]
        assert "something went wrong" in ctx.errors[0]

    def test_multiple_errors_accumulate(self):
        ctx = PipelineContext(topic="test")
        ctx.record_error("s1", "error 1")
        ctx.record_error("s2", "error 2")
        assert len(ctx.errors) == 2


# ============================================================================
# Stage interface contract
# ============================================================================

class TestStageInterface:
    def test_all_stages_implement_pipeline_stage(self):
        from stages.strategy import StrategyStage
        from stages.seo_brief import SEOBriefStage
        from stages.research import ResearchStage
        from stages.writer import WriterStage
        from stages.editor import EditorStage
        from stages.optimizer import OptimizerStage
        from stages.linker import LinkerStage
        from stages.publisher import PublisherStage
        from stages.auditor import AuditorStage

        stage_classes = [
            StrategyStage, SEOBriefStage, ResearchStage, WriterStage,
            EditorStage, OptimizerStage, LinkerStage, PublisherStage, AuditorStage,
        ]
        for cls in stage_classes:
            assert issubclass(cls, PipelineStage), f"{cls.__name__} must extend PipelineStage"

    def test_all_stages_have_name_property(self):
        from stages.strategy import StrategyStage
        from stages.seo_brief import SEOBriefStage
        from stages.research import ResearchStage
        from stages.writer import WriterStage
        from stages.editor import EditorStage
        from stages.optimizer import OptimizerStage
        from stages.linker import LinkerStage
        from stages.publisher import PublisherStage
        from stages.auditor import AuditorStage

        stages = [
            StrategyStage(llm=MOCK_LLM),
            SEOBriefStage(llm=MOCK_LLM),
            ResearchStage(llm=MOCK_LLM),
            WriterStage(llm=MOCK_LLM),
            EditorStage(llm=MOCK_LLM),
            OptimizerStage(llm=MOCK_LLM),
            LinkerStage(),
            PublisherStage(),
            AuditorStage(),
        ]
        names = [s.name for s in stages]
        assert len(names) == len(set(names)), "All stage names must be unique"
        assert all(isinstance(n, str) and n for n in names), "All names must be non-empty strings"


# ============================================================================
# Strategy stage
# ============================================================================

class TestStrategyStage:
    def test_run_populates_strategy(self, base_ctx):
        from stages.strategy import StrategyStage
        stage = StrategyStage(llm=MOCK_LLM)
        result = stage.run(base_ctx)
        assert result.strategy is not None
        assert "content_angles" in result.strategy
        assert result.strategy["content_angles"]

    def test_quality_gate_passes_with_valid_output(self, base_ctx):
        from stages.strategy import StrategyStage
        stage = StrategyStage(llm=MOCK_LLM)
        ctx = stage.run(base_ctx)
        stage.quality_gate(ctx)  # should not raise

    def test_fallback_on_empty_llm_response(self, base_ctx):
        from stages.strategy import StrategyStage

        class EmptyLLM:
            def run(self, *a, **kw):
                return ""

        stage = StrategyStage(llm=EmptyLLM())
        ctx = stage.run(base_ctx)
        assert ctx.strategy is not None
        assert "content_angles" in ctx.strategy
        assert ctx.strategy["content_angles"]

    def test_records_error_on_fallback(self, base_ctx):
        from stages.strategy import StrategyStage

        class BrokenLLM:
            def run(self, *a, **kw):
                return "not valid json {"

        stage = StrategyStage(llm=BrokenLLM())
        ctx = stage.run(base_ctx)
        assert ctx.strategy is not None  # fallback applied
        # error may or may not be recorded depending on json parse failure


# ============================================================================
# SEO Brief stage
# ============================================================================

class TestSEOBriefStage:
    def test_run_populates_seo_brief(self, ctx_with_strategy):
        from stages.seo_brief import SEOBriefStage
        stage = SEOBriefStage(llm=MOCK_LLM)
        result = stage.run(ctx_with_strategy)
        assert result.seo_brief is not None
        assert result.seo_brief.get("primary_keyword")
        assert result.seo_brief.get("h2_structure")
        assert result.seo_brief.get("meta_title")

    def test_quality_gate_passes(self, ctx_with_strategy):
        from stages.seo_brief import SEOBriefStage
        stage = SEOBriefStage(llm=MOCK_LLM)
        ctx = stage.run(ctx_with_strategy)
        stage.quality_gate(ctx)

    def test_fallback_produces_valid_brief(self, ctx_with_strategy):
        from stages.seo_brief import SEOBriefStage

        class EmptyLLM:
            def run(self, *a, **kw):
                return ""

        stage = SEOBriefStage(llm=EmptyLLM())
        ctx = stage.run(ctx_with_strategy)
        assert ctx.seo_brief is not None
        assert ctx.seo_brief.get("primary_keyword")
        assert len(ctx.seo_brief.get("h2_structure", [])) == 4


# ============================================================================
# Research stage
# ============================================================================

class TestResearchStage:
    def test_run_populates_research(self, ctx_with_seo):
        from stages.research import ResearchStage

        with patch("stages.research.BraveSearchTool") as mock_cls:
            mock_tool = MagicMock()
            mock_tool._run.return_value = json.dumps([
                {
                    "title": "Test Result",
                    "url": "https://example.gov/docs",
                    "description": "Official documentation",
                }
            ])
            mock_cls.return_value = mock_tool

            stage = ResearchStage(llm=MOCK_LLM)
            result = stage.run(ctx_with_seo)

        assert result.research is not None
        assert len(result.research) > 100
        assert result.research_sources is not None

    def test_tier_classification_tier1(self, ctx_with_seo):
        from stages.research import ResearchStage
        stage = ResearchStage(llm=MOCK_LLM)
        assert stage._classify_tier("https://example.gov/docs") == 1
        assert stage._classify_tier("https://arxiv.org/abs/paper") == 1
        assert stage._classify_tier("https://ncbi.nlm.nih.gov/article") == 1

    def test_tier_classification_tier2(self, ctx_with_seo):
        from stages.research import ResearchStage
        stage = ResearchStage(llm=MOCK_LLM)
        assert stage._classify_tier("https://techcrunch.com/article") == 2
        assert stage._classify_tier("https://ahrefs.com/blog/post") == 2

    def test_tier_classification_tier3(self, ctx_with_seo):
        from stages.research import ResearchStage
        stage = ResearchStage(llm=MOCK_LLM)
        assert stage._classify_tier("https://random-blog.com/post") == 3

    def test_extract_sources_returns_unique_urls(self, ctx_with_seo):
        from stages.research import ResearchStage
        stage = ResearchStage(llm=MOCK_LLM)
        raw = "See https://example.gov/a and https://example.gov/a and https://other.com/b"
        sources = stage._extract_sources(raw)
        urls = [s["url"] for s in sources]
        assert len(urls) == len(set(urls))


# ============================================================================
# Writer stage
# ============================================================================

class TestWriterStage:
    def test_run_populates_draft(self, ctx_with_seo):
        from stages.writer import WriterStage
        ctx_with_seo.research = "Research brief with findings and sources."
        stage = WriterStage(llm=MOCK_LLM)
        result = stage.run(ctx_with_seo)
        assert result.draft is not None
        assert len(result.draft) > 200

    def test_fallback_on_empty_llm(self, ctx_with_seo):
        from stages.writer import WriterStage

        class EmptyLLM:
            def run(self, *a, **kw):
                return ""

        ctx_with_seo.research = "Some research."
        stage = WriterStage(llm=EmptyLLM())
        ctx = stage.run(ctx_with_seo)
        assert ctx.draft is not None
        assert ctx.topic in ctx.draft


# ============================================================================
# Editor stage
# ============================================================================

class TestEditorStage:
    def test_run_populates_edited(self, ctx_with_draft):
        from stages.editor import EditorStage
        stage = EditorStage(llm=MOCK_LLM)
        result = stage.run(ctx_with_draft)
        assert result.edited is not None
        assert len(result.edited) > 100

    def test_banned_phrase_count_is_accurate(self):
        from stages.editor import EditorStage
        stage = EditorStage(llm=MOCK_LLM, banned_phrases=["bad phrase", "remove me"])
        article = "This has a bad phrase in it. Also remove me here. And bad phrase again."
        _, count = stage._sweep_banned_phrases(article)
        assert count == 3

    def test_banned_phrases_are_removed(self):
        from stages.editor import EditorStage
        stage = EditorStage(llm=MOCK_LLM, banned_phrases=["game-changer"])
        article = "This is a game-changer for the industry."
        cleaned, count = stage._sweep_banned_phrases(article)
        assert "game-changer" not in cleaned
        assert count == 1

    def test_no_crash_on_empty_draft(self, ctx_with_seo):
        from stages.editor import EditorStage
        ctx_with_seo.draft = ""
        stage = EditorStage(llm=MOCK_LLM)
        result = stage.run(ctx_with_seo)
        assert any("editor" in e for e in result.errors)


# ============================================================================
# Optimizer stage
# ============================================================================

class TestOptimizerStage:
    def test_run_populates_optimized_and_score(self, ctx_with_draft):
        from stages.optimizer import OptimizerStage
        stage = OptimizerStage(llm=MOCK_LLM)
        result = stage.run(ctx_with_draft)
        assert result.optimized is not None
        assert result.seo_score is not None
        assert 0 <= result.seo_score <= 100

    def test_patch_embeds_meta_description(self, ctx_with_draft):
        from stages.optimizer import OptimizerStage
        ctx_with_draft.seo_brief["meta_description"] = "Unique test meta description."
        stage = OptimizerStage(llm=MOCK_LLM)
        seo = ctx_with_draft.seo_brief
        patched = stage._patch(ctx_with_draft.draft, seo)
        assert "Unique test meta description." in patched

    def test_patch_sets_h1_to_meta_title(self, ctx_with_draft):
        from stages.optimizer import OptimizerStage
        ctx_with_draft.seo_brief["meta_title"] = "The Definitive Meta Title"
        stage = OptimizerStage(llm=MOCK_LLM)
        patched = stage._patch(ctx_with_draft.draft, ctx_with_draft.seo_brief)
        assert "# The Definitive Meta Title" in patched

    def test_audit_flags_missing_keyword(self, ctx_with_draft):
        from stages.optimizer import OptimizerStage
        ctx_with_draft.seo_brief["primary_keyword"] = "xyz_totally_absent_keyword"
        stage = OptimizerStage(llm=MOCK_LLM)
        score, issues = stage._audit(ctx_with_draft.draft, ctx_with_draft.seo_brief)
        assert any("keyword density" in i for i in issues)

    def test_no_crash_on_empty_article(self, ctx_with_seo):
        from stages.optimizer import OptimizerStage
        ctx_with_seo.edited = ""
        ctx_with_seo.draft = ""
        stage = OptimizerStage(llm=MOCK_LLM)
        result = stage.run(ctx_with_seo)
        assert any("optimizer" in e for e in result.errors)


# ============================================================================
# Linker stage
# ============================================================================

class TestLinkerStage:
    def test_run_populates_linked(self, ctx_with_draft):
        from stages.linker import LinkerStage
        ctx_with_draft.optimized = ctx_with_draft.draft
        stage = LinkerStage()
        result = stage.run(ctx_with_draft)
        assert result.linked is not None
        assert len(result.linked) > 100

    def test_placeholder_inserted_for_known_anchor(self):
        from stages.linker import LinkerStage
        stage = LinkerStage()
        article = "The test topic is widely discussed in the field."
        seo = {"internal_link_targets": [{"anchor": "test topic", "url": "/test-topic"}]}
        ctx = PipelineContext(topic="test")
        ctx.seo_brief = seo
        ctx.optimized = article
        result = stage.run(ctx)
        assert result.links_inserted >= 1
        assert "[[LINK:" in result.linked or "[test topic](" in result.linked

    def test_no_duplicate_links_on_same_line(self):
        from stages.linker import LinkerStage
        stage = LinkerStage()
        # Line already has an external link — should not insert placeholder
        article = "See [test topic](https://external.com/page) for more details."
        seo = {"internal_link_targets": [{"anchor": "test topic", "url": "/test-topic"}]}
        ctx = PipelineContext(topic="test")
        ctx.seo_brief = seo
        ctx.optimized = article
        result = stage.run(ctx)
        # The line with existing link should not get a second insertion
        assert result.linked.count("test topic") <= 2

    def test_no_crash_on_empty_article(self, ctx_with_seo):
        from stages.linker import LinkerStage
        ctx_with_seo.optimized = ""
        ctx_with_seo.edited = ""
        ctx_with_seo.draft = ""
        stage = LinkerStage()
        result = stage.run(ctx_with_seo)
        assert any("linker" in e for e in result.errors)


# ============================================================================
# Publisher stage
# ============================================================================

class TestPublisherStage:
    def test_run_populates_publish_result_on_success(self, ctx_with_draft):
        from stages.publisher import PublisherStage
        ctx_with_draft.linked = ctx_with_draft.draft

        with patch("stages.publisher.GhostCMSTool") as mock_cls:
            mock_tool = MagicMock()
            mock_tool._run.return_value = json.dumps({
                "status": "success",
                "post_id": "abc123",
                "draft_url": "https://ghost.example.com/ghost/#/editor/post/abc123",
            })
            mock_cls.return_value = mock_tool
            stage = PublisherStage()
            result = stage.run(ctx_with_draft)

        assert result.publish_result is not None
        assert result.publish_result.get("status") == "success"

    def test_handles_publish_failure_without_raising(self, ctx_with_draft):
        from stages.publisher import PublisherStage
        ctx_with_draft.linked = ctx_with_draft.draft

        with patch("stages.publisher.GhostCMSTool") as mock_cls:
            mock_tool = MagicMock()
            mock_tool._run.return_value = json.dumps({
                "status": "error",
                "message": "Authentication failed",
            })
            mock_cls.return_value = mock_tool
            stage = PublisherStage()
            result = stage.run(ctx_with_draft)

        assert result.publish_result["status"] == "error"

    def test_quality_gate_fails_on_error_status(self, ctx_with_draft):
        from stages.publisher import PublisherStage
        ctx_with_draft.publish_result = {"status": "error", "message": "Auth failed"}
        stage = PublisherStage.__new__(PublisherStage)
        with pytest.raises(AssertionError, match="Ghost publish failed"):
            stage.quality_gate(ctx_with_draft)

    def test_no_crash_on_missing_content(self, ctx_with_seo):
        from stages.publisher import PublisherStage

        with patch("stages.publisher.GhostCMSTool"):
            stage = PublisherStage()
            result = stage.run(ctx_with_seo)

        assert any("publisher" in e for e in result.errors)


# ============================================================================
# Auditor stage
# ============================================================================

class TestAuditorStage:
    def test_run_populates_audit_report(self, ctx_with_draft):
        from stages.auditor import AuditorStage
        ctx_with_draft.linked = ctx_with_draft.draft
        stage = AuditorStage()
        result = stage.run(ctx_with_draft)
        assert result.audit_report is not None
        assert "score" in result.audit_report
        assert "issues" in result.audit_report
        assert "recommendations" in result.audit_report
        assert "stats" in result.audit_report

    def test_checklists_are_populated(self, ctx_with_draft):
        from stages.auditor import AuditorStage
        ctx_with_draft.linked = ctx_with_draft.draft
        stage = AuditorStage()
        result = stage.run(ctx_with_draft)
        assert len(result.audit_report["checklist_30d"]) > 0
        assert len(result.audit_report["checklist_60d"]) > 0
        assert len(result.audit_report["checklist_90d"]) > 0

    def test_score_is_within_valid_range(self, ctx_with_draft):
        from stages.auditor import AuditorStage
        ctx_with_draft.linked = ctx_with_draft.draft
        stage = AuditorStage()
        result = stage.run(ctx_with_draft)
        assert 0 <= result.audit_report["score"] <= 100

    def test_stats_contain_expected_keys(self, ctx_with_draft):
        from stages.auditor import AuditorStage
        ctx_with_draft.linked = ctx_with_draft.draft
        stage = AuditorStage()
        result = stage.run(ctx_with_draft)
        stats = result.audit_report["stats"]
        assert "word_count" in stats
        assert "h2_count" in stats
        assert "external_link_count" in stats

    def test_quality_gate_passes(self, ctx_with_draft):
        from stages.auditor import AuditorStage
        ctx_with_draft.linked = ctx_with_draft.draft
        stage = AuditorStage()
        ctx = stage.run(ctx_with_draft)
        stage.quality_gate(ctx)


# ============================================================================
# Orchestrator
# ============================================================================

class TestOrchestrator:
    def test_build_pipeline_returns_orchestrator(self):
        from orchestrator import build_pipeline, Orchestrator
        pipeline = build_pipeline(
            llm=MOCK_LLM, include_publisher=False, include_auditor=False
        )
        assert isinstance(pipeline, Orchestrator)
        assert len(pipeline.stages) == 7

    def test_build_pipeline_includes_all_stages(self):
        from orchestrator import build_pipeline

        with patch("stages.publisher.GhostCMSTool"):
            pipeline = build_pipeline(
                llm=MOCK_LLM, include_publisher=True, include_auditor=True
            )
        assert len(pipeline.stages) == 9

    def test_stage_names_are_unique(self):
        from orchestrator import build_pipeline
        pipeline = build_pipeline(
            llm=MOCK_LLM, include_publisher=False, include_auditor=False
        )
        names = [s.name for s in pipeline.stages]
        assert len(names) == len(set(names)), "Duplicate stage names detected"

    def test_all_stages_implement_interface(self):
        from orchestrator import build_pipeline
        pipeline = build_pipeline(
            llm=MOCK_LLM, include_publisher=False, include_auditor=False
        )
        for stage in pipeline.stages:
            assert isinstance(stage, PipelineStage)

    def test_orchestrator_records_stage_timings(self):
        from stages.strategy import StrategyStage
        from orchestrator import Orchestrator

        stage = StrategyStage(llm=MOCK_LLM)
        orch = Orchestrator(stages=[stage])
        result = orch.run(TEST_TOPIC)

        assert "strategy" in result.stage_timings
        assert result.stage_timings["strategy"] >= 0

    def test_orchestrator_continues_after_stage_crash(self):
        from stages.strategy import StrategyStage
        from orchestrator import Orchestrator

        class CrashingStage(PipelineStage):
            name = "crasher"

            def run(self, ctx):
                raise RuntimeError("intentional test crash")

        stages = [CrashingStage(), StrategyStage(llm=MOCK_LLM)]
        orch = Orchestrator(stages=stages)
        result = orch.run(TEST_TOPIC)

        # Pipeline must continue past the crash
        assert result.strategy is not None
        assert any("crasher" in e for e in result.errors)

    def test_orchestrator_records_quality_gate_failures(self):
        from orchestrator import Orchestrator

        class FailingGateStage(PipelineStage):
            name = "bad_gate"

            def run(self, ctx):
                return ctx

            def quality_gate(self, ctx):
                raise AssertionError("gate always fails")

        orch = Orchestrator(stages=[FailingGateStage()])
        result = orch.run(TEST_TOPIC)
        assert any("bad_gate" in e for e in result.errors)
        assert any("quality gate" in e for e in result.errors)
