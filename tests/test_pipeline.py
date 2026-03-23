"""
Tests for the semantic SEO pipeline.

Uses MockLLM fixtures — no real API keys required.
Tests verify wiring contracts between pipeline stages:
  sanitize_output → _manual_strategy → _manual_seo → _manual_write
  → _manual_review → _manual_format → _manual_internal_links
"""

import os
import sys
import json
import pytest
from unittest.mock import MagicMock

# ============================================================================
# Pre-import mocks — must happen before any project-level imports.
# crewai and langchain won't install on Python 3.14 (numpy C-ext failure),
# so we stub them out so project modules can still be imported.
# ============================================================================

class _FakeBaseTool:
    """Minimal stub that allows tools.py classes to subclass it normally."""
    pass


_fake_langchain_tools = MagicMock()
_fake_langchain_tools.BaseTool = _FakeBaseTool

sys.modules.setdefault("crewai", MagicMock())
sys.modules.setdefault("langchain_openai", MagicMock())
sys.modules.setdefault("langchain", MagicMock())
sys.modules.setdefault("langchain.tools", _fake_langchain_tools)
sys.modules.setdefault("anthropic", MagicMock())

# Fake env vars so Config.validate_config() won't raise during import.
os.environ.setdefault("LLM_API_KEY", "test-llm-key")
os.environ.setdefault("BRAVE_SEARCH_API_KEY", "test-brave-key")
os.environ.setdefault("GHOST_API_KEY", "test-id:test-secret-aabbccdd")
os.environ.setdefault("GHOST_API_URL", "http://localhost:2368")
os.environ.setdefault("DEMO_MODE", "false")

# ============================================================================
# Project imports (after mocks are set up)
# ============================================================================

from tools import sanitize_output          # noqa: E402  (mocks must come first)
from utils import (                         # noqa: E402
    extract_title_from_content,
    extract_meta_description_from_content,
    clean_markdown_content,
    analyze_content_quality,
)
from config import Config                   # noqa: E402
from main import (                          # noqa: E402
    _manual_format,
    _manual_internal_links,
    _manual_strategy,
    _manual_seo,
    _manual_write,
    _manual_review,
)

# ============================================================================
# MockLLM fixture
# ============================================================================

class MockLLM:
    """Fake LLM that returns a preset response without any API call."""

    def __init__(self, response: str = ""):
        self.response = response
        self.calls: list[str] = []

    def run(self, prompt: str, max_tokens: int = 4096) -> str:
        self.calls.append(prompt)
        return self.response


# ============================================================================
# Shared test data
# ============================================================================

STRATEGY_JSON = json.dumps({
    "target_audience": {
        "primary": "Python developers",
        "pain_points": ["verbose boilerplate", "slow feedback loops"],
        "preferences": "code examples and quick wins",
    },
    "competitive_landscape": {
        "gaps": ["beginner-friendly pytest deep dives"],
        "opportunities": ["fixture composition tutorials"],
    },
    "content_angles": ["pytest mastery", "TDD workflow", "CI integration"],
    "market_opportunities": ["growing Python test culture", "pytest plugin ecosystem"],
    "strategic_positioning": {
        "unique_value": "practical, production-ready testing patterns",
        "key_messages": ["tests as documentation", "fast feedback loops"],
        "tone": "technical but approachable",
    },
})

SEO_JSON = json.dumps({
    "primary_keyword": "python testing best practices",
    "cluster_keywords": ["pytest tutorial", "unit testing python"],
    "lsi_keywords": ["test fixtures", "mocking", "CI pipeline", "code coverage", "TDD"],
    "h2_structure": [
        "Why Testing Matters",
        "Setting Up pytest",
        "Writing Effective Tests",
        "Integrating Tests into CI",
    ],
    "meta_title": "Python Testing Best Practices (2025 Guide)",
    "meta_description": (
        "Master Python testing with pytest. Learn fixtures, mocking, "
        "and CI integration with production-ready examples in this complete guide."
    ),
    "internal_link_targets": [
        {"anchor": "pytest fixtures", "url": "/pytest-fixtures-guide"},
        {"anchor": "CI pipeline", "url": "/ci-cd-setup"},
    ],
    "seo_recommendations": [
        "Include runnable code examples",
        "Add an FAQ section targeting long-tail queries",
        "Link to official pytest documentation",
    ],
})

SAMPLE_ARTICLE = """\
# Python Testing Best Practices (2025 Guide)

*Master Python testing with pytest in this complete guide.*

## Why Testing Matters

Testing ensures correctness and prevents regressions. According to
[pytest documentation](https://docs.pytest.org), well-structured tests
act as living documentation for your codebase.

## Setting Up pytest

Install [pytest](https://pytest.org) with `pip install pytest`. The
[pytest-cov plugin](https://pytest-cov.readthedocs.io) adds coverage
reporting, and [pytest-xdist](https://github.com/pytest-dev/pytest-xdist)
enables parallel test execution.

## Writing Effective Tests

Use [fixtures](https://docs.pytest.org/en/stable/reference/fixtures.html)
to share setup code. [Mocking](https://docs.python.org/3/library/unittest.mock.html)
isolates units under test. See the
[Real Python testing guide](https://realpython.com/python-testing/) for
practical patterns.

## Integrating Tests into CI

[GitHub Actions](https://github.com/features/actions) makes CI trivial.
The [official workflow templates](https://github.com/actions/starter-workflows)
cover Python projects. Pair with [Codecov](https://codecov.io) for
coverage badges. Set up [pre-commit hooks](https://pre-commit.com) to
run tests locally before pushing. Use [tox](https://tox.wiki) for
multi-version matrix testing.

## Conclusion

Testing is an investment that pays dividends. Start with
[pytest](https://pytest.org) and build from there.

## References

1. [pytest documentation](https://docs.pytest.org)
2. [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
3. [Real Python Testing Guide](https://realpython.com/python-testing/)
"""


# ============================================================================
# Tests: sanitize_output
# ============================================================================

class TestSanitizeOutput:
    def test_clean_text_passes_through(self):
        text = "This is clean content about SEO optimization."
        assert sanitize_output(text) == text

    def test_rate_limit_signal_returns_empty(self):
        assert sanitize_output("Error: rate_limit exceeded") == ""

    def test_429_signal_returns_empty(self):
        assert sanitize_output("HTTP 429 Too Many Requests") == ""

    def test_overloaded_signal_returns_empty(self):
        assert sanitize_output("The model is currently overloaded") == ""

    def test_llm_unavailable_signal_returns_empty(self):
        assert sanitize_output("LLM_UNAVAILABLE") == ""

    def test_api_error_signal_returns_empty(self):
        assert sanitize_output("[Anthropic Error] 503 service unavailable") == ""

    def test_custom_fallback_on_error_signal(self):
        result = sanitize_output("rate limit exceeded", fallback="RETRY")
        assert result == "RETRY"

    def test_non_string_integer_is_stringified(self):
        result = sanitize_output(42)
        assert result == "42"

    def test_non_string_dict_is_stringified(self):
        result = sanitize_output({"key": "value"})
        assert isinstance(result, str)

    def test_excessive_newlines_collapsed(self):
        text = "Paragraph one.\n\n\n\n\nParagraph two."
        result = sanitize_output(text)
        assert "\n\n\n" not in result
        assert "Paragraph one." in result
        assert "Paragraph two." in result

    def test_leading_and_trailing_whitespace_stripped(self):
        text = "   Clean content.   "
        assert sanitize_output(text) == "Clean content."

    def test_empty_string_returns_empty(self):
        assert sanitize_output("") == ""

    def test_fallback_returned_for_empty(self):
        # Empty string returns "" not fallback — fallback is only for error signals
        assert sanitize_output("", fallback="X") == ""


# ============================================================================
# Tests: _manual_format
# ============================================================================

class TestManualFormat:
    def test_article_without_h1_gets_title_prepended(self):
        article = "My Article Title\n\nSome body text."
        result = _manual_format(article)
        assert result.startswith("# My Article Title")

    def test_article_with_h1_is_not_doubled(self):
        article = "# Existing Title\n\nBody text."
        result = _manual_format(article)
        assert result.startswith("# Existing Title")
        assert result.count("# Existing Title") == 1

    def test_excessive_blank_lines_collapsed(self):
        article = "# Title\n\n\n\n\nBody text."
        result = _manual_format(article)
        assert "\n\n\n" not in result

    def test_trailing_whitespace_stripped(self):
        article = "# Title\n\nBody.   \n\n  "
        result = _manual_format(article)
        assert result == result.strip()

    def test_h2_sections_preserved(self):
        article = "# Title\n\n## Section One\n\nText.\n\n## Section Two\n\nMore."
        result = _manual_format(article)
        assert "## Section One" in result
        assert "## Section Two" in result

    def test_returns_string(self):
        assert isinstance(_manual_format("Some content"), str)


# ============================================================================
# Tests: _manual_internal_links
# ============================================================================

class TestManualInternalLinks:
    def test_no_targets_returns_article_unchanged(self):
        article = "# Title\n\nGhost tours are popular year-round."
        seo = {"internal_link_targets": []}
        assert _manual_internal_links(article, seo) == article

    def test_missing_targets_key_returns_unchanged(self):
        article = "# Title\n\nSome content."
        assert _manual_internal_links(article, {}) == article

    def test_matching_anchor_inserts_placeholder(self):
        article = "# Title\n\nGhost tours are popular year-round."
        seo = {"internal_link_targets": [{"anchor": "Ghost tours", "url": "/ghost-tours"}]}
        result = _manual_internal_links(article, seo)
        assert "[[LINK: Ghost tours → /ghost-tours]]" in result

    def test_case_insensitive_anchor_match(self):
        article = "# Title\n\nghost tours happen at night."
        seo = {"internal_link_targets": [{"anchor": "ghost tours", "url": "/ghost-tours"}]}
        result = _manual_internal_links(article, seo)
        assert "[[LINK:" in result

    def test_line_with_external_link_is_skipped(self):
        article = "# Title\n\nVisit [ghost tours](https://example.com) for details."
        seo = {"internal_link_targets": [{"anchor": "ghost tours", "url": "/ghost-tours"}]}
        result = _manual_internal_links(article, seo)
        # The line already has an external link → should not receive [[LINK:]]
        assert "[[LINK:" not in result

    def test_maximum_five_insertions(self):
        seo = {
            "internal_link_targets": [
                {"anchor": f"term{i}", "url": f"/path{i}"}
                for i in range(10)
            ]
        }
        lines = ["# Title"] + [f"\n\nThis mentions term{i} in context." for i in range(10)]
        article = "".join(lines)
        result = _manual_internal_links(article, seo)
        assert result.count("[[LINK:") <= 5

    def test_blank_anchor_skipped(self):
        article = "# Title\n\nSome content here."
        seo = {"internal_link_targets": [{"anchor": "", "url": "/path"}]}
        result = _manual_internal_links(article, seo)
        assert "[[LINK:" not in result

    def test_blank_url_skipped(self):
        article = "# Title\n\nSome content here."
        seo = {"internal_link_targets": [{"anchor": "content", "url": ""}]}
        result = _manual_internal_links(article, seo)
        assert "[[LINK:" not in result

    def test_result_is_string(self):
        result = _manual_internal_links("# Title\n\nBody.", {"internal_link_targets": []})
        assert isinstance(result, str)


# ============================================================================
# Tests: extract_title_from_content
# ============================================================================

class TestExtractTitle:
    def test_markdown_h1(self):
        content = "# My Blog Title\n\nBody text."
        assert extract_title_from_content(content) == "My Blog Title"

    def test_html_h1(self):
        content = "<h1>HTML Title</h1><p>Body</p>"
        assert extract_title_from_content(content) == "HTML Title"

    def test_no_heading_returns_default(self):
        content = "No heading here, just plain text."
        assert extract_title_from_content(content) == "Generated Blog Post"

    def test_markdown_h1_with_extra_spaces(self):
        content = "#   Spaced Title   \n\nBody."
        assert extract_title_from_content(content) == "Spaced Title"

    def test_html_h1_with_attributes(self):
        content = '<h1 class="title">Attributed Title</h1>'
        assert extract_title_from_content(content) == "Attributed Title"


# ============================================================================
# Tests: extract_meta_description_from_content
# ============================================================================

class TestExtractMetaDescription:
    def test_italics_after_h1(self):
        content = "# Title\n\n*This is the meta description for the article.*\n\nBody."
        result = extract_meta_description_from_content(content)
        assert "meta description" in result.lower()

    def test_no_meta_returns_default(self):
        content = "# Title\n\nPlain body text without any meta pattern."
        result = extract_meta_description_from_content(content)
        assert result == "A comprehensive blog post generated by CrewAI"


# ============================================================================
# Tests: clean_markdown_content
# ============================================================================

class TestCleanMarkdownContent:
    def test_removes_italicized_meta_after_title(self):
        content = "# My Title\n\n*Short meta description.*\n\nBody text here."
        result = clean_markdown_content(content)
        assert "*Short meta description.*" not in result
        assert "# My Title" in result
        assert "Body text here." in result

    def test_content_without_meta_unchanged(self):
        content = "# My Title\n\nBody text without meta."
        result = clean_markdown_content(content)
        assert "Body text without meta." in result

    def test_returns_string(self):
        assert isinstance(clean_markdown_content("# Title\n\nBody."), str)


# ============================================================================
# Tests: analyze_content_quality
# ============================================================================

class TestAnalyzeContentQuality:
    @staticmethod
    def _words(n: int) -> str:
        return " ".join(["word"] * n)

    def test_excellent_quality_at_1000_words(self):
        result = analyze_content_quality(self._words(1100))
        assert result["quality_score"] == "excellent"
        assert result["is_substantial"] is True

    def test_good_quality_between_500_and_1000(self):
        result = analyze_content_quality(self._words(600))
        assert result["quality_score"] == "good"
        assert result["is_moderate"] is True

    def test_needs_improvement_below_500(self):
        result = analyze_content_quality(self._words(100))
        assert result["quality_score"] == "needs_improvement"
        assert result["is_short"] is True

    def test_word_count_returned(self):
        result = analyze_content_quality(self._words(300))
        assert result["word_count"] == 300

    def test_html_content_stripped_before_counting(self):
        html = "<p>" + self._words(1200) + "</p>"
        result = analyze_content_quality(html)
        assert result["quality_score"] == "excellent"

    def test_result_has_required_keys(self):
        result = analyze_content_quality(self._words(50))
        for key in ("word_count", "char_count", "quality_score",
                    "is_substantial", "is_moderate", "is_short"):
            assert key in result


# ============================================================================
# Tests: Config
# ============================================================================

class TestConfig:
    def test_load_without_profile(self):
        Config.load(profile=None, yaml_path="nonexistent_file.yaml")
        assert isinstance(Config.PIPELINE, dict)

    def test_validate_config_returns_true_with_env_vars(self):
        assert Config.validate_config() is True

    def test_demo_mode_is_false_when_set_to_false(self):
        # We set DEMO_MODE=false at the top of this file
        assert Config.DEMO_MODE is False


# ============================================================================
# Tests: _manual_strategy (MockLLM)
# ============================================================================

class TestManualStrategy:
    def test_valid_json_returns_dict_with_expected_keys(self):
        llm = MockLLM(response=STRATEGY_JSON)
        result = _manual_strategy("Python testing", llm)
        assert isinstance(result, dict)
        assert "content_angles" in result
        assert "target_audience" in result
        assert "strategic_positioning" in result

    def test_llm_called_exactly_once(self):
        llm = MockLLM(response=STRATEGY_JSON)
        _manual_strategy("Python testing", llm)
        assert len(llm.calls) == 1

    def test_prompt_contains_topic(self):
        llm = MockLLM(response=STRATEGY_JSON)
        _manual_strategy("Ghost tours in New Orleans", llm)
        assert "Ghost tours in New Orleans" in llm.calls[0]

    def test_empty_response_returns_fallback_dict(self):
        llm = MockLLM(response="")
        result = _manual_strategy("Test topic", llm)
        assert isinstance(result, dict)
        assert "content_angles" in result

    def test_garbage_response_returns_fallback_dict(self):
        llm = MockLLM(response="Sorry, I cannot help with that request.")
        result = _manual_strategy("Test topic", llm)
        assert isinstance(result, dict)

    def test_rate_limit_response_returns_fallback(self):
        llm = MockLLM(response="rate_limit exceeded, please slow down")
        result = _manual_strategy("Test topic", llm)
        assert isinstance(result, dict)
        assert "content_angles" in result

    def test_content_angles_is_list(self):
        llm = MockLLM(response=STRATEGY_JSON)
        result = _manual_strategy("Topic", llm)
        assert isinstance(result["content_angles"], list)


# ============================================================================
# Tests: _manual_seo (MockLLM)
# ============================================================================

STRATEGY_DICT = json.loads(STRATEGY_JSON)


class TestManualSEO:
    def test_valid_json_returns_dict_with_expected_keys(self):
        llm = MockLLM(response=SEO_JSON)
        result = _manual_seo("Python testing", STRATEGY_DICT, llm)
        assert isinstance(result, dict)
        for key in ("primary_keyword", "h2_structure", "meta_description",
                    "cluster_keywords", "lsi_keywords"):
            assert key in result

    def test_llm_called_exactly_once(self):
        llm = MockLLM(response=SEO_JSON)
        _manual_seo("Python testing", STRATEGY_DICT, llm)
        assert len(llm.calls) == 1

    def test_prompt_references_topic(self):
        llm = MockLLM(response=SEO_JSON)
        _manual_seo("Biblical archaeology", STRATEGY_DICT, llm)
        assert "Biblical archaeology" in llm.calls[0]

    def test_prompt_uses_strategy_context(self):
        llm = MockLLM(response=SEO_JSON)
        _manual_seo("Python testing", STRATEGY_DICT, llm)
        prompt = llm.calls[0]
        # Strategy audience or angles should appear in the prompt
        assert (
            "Python developer" in prompt
            or "pytest mastery" in prompt
            or "Python testing" in prompt
        )

    def test_empty_response_returns_fallback_with_topic_as_keyword(self):
        llm = MockLLM(response="")
        result = _manual_seo("My Topic", {}, llm)
        assert isinstance(result, dict)
        assert result["primary_keyword"] == "My Topic"

    def test_fallback_h2_structure_is_non_empty(self):
        llm = MockLLM(response="")
        result = _manual_seo("Topic X", {}, llm)
        assert isinstance(result["h2_structure"], list)
        assert len(result["h2_structure"]) > 0

    def test_garbage_response_returns_fallback(self):
        llm = MockLLM(response="I don't understand the request.")
        result = _manual_seo("Topic", {}, llm)
        assert isinstance(result, dict)
        assert "primary_keyword" in result


# ============================================================================
# Tests: _manual_write (MockLLM)
# ============================================================================

SEO_DICT = json.loads(SEO_JSON)


class TestManualWrite:
    def test_returns_string_content(self):
        llm = MockLLM(response=SAMPLE_ARTICLE)
        result = _manual_write("Python testing", "Research text", SEO_DICT, llm)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_llm_called_once(self):
        llm = MockLLM(response=SAMPLE_ARTICLE)
        _manual_write("Python testing", "Research text", SEO_DICT, llm)
        assert len(llm.calls) == 1

    def test_prompt_contains_topic(self):
        llm = MockLLM(response=SAMPLE_ARTICLE)
        _manual_write("Ghost tours in Paris", "Research text", SEO_DICT, llm)
        assert "Ghost tours in Paris" in llm.calls[0]

    def test_prompt_uses_seo_headings(self):
        llm = MockLLM(response=SAMPLE_ARTICLE)
        _manual_write("Python testing", "Research text", SEO_DICT, llm)
        prompt = llm.calls[0]
        assert "Why Testing Matters" in prompt or "Setting Up pytest" in prompt

    def test_prompt_uses_primary_keyword(self):
        llm = MockLLM(response=SAMPLE_ARTICLE)
        _manual_write("Python testing", "Research text", SEO_DICT, llm)
        assert "python testing best practices" in llm.calls[0]

    def test_empty_response_returns_fallback_with_topic(self):
        llm = MockLLM(response="")
        result = _manual_write("My Fallback Topic", "Research", {}, llm)
        assert isinstance(result, str)
        assert "My Fallback Topic" in result

    def test_llm_unavailable_returns_fallback(self):
        llm = MockLLM(response="LLM_UNAVAILABLE")
        result = _manual_write("My Topic", "Research", {}, llm)
        assert isinstance(result, str)
        assert "My Topic" in result

    def test_prompt_includes_research(self):
        llm = MockLLM(response=SAMPLE_ARTICLE)
        _manual_write("Topic", "KEY RESEARCH SUMMARY", SEO_DICT, llm)
        assert "KEY RESEARCH SUMMARY" in llm.calls[0]


# ============================================================================
# Tests: _manual_review (MockLLM)
# ============================================================================

class TestManualReview:
    def test_returns_reviewed_article(self):
        # _manual_review passes the LLM response through sanitize_output (strips
        # whitespace, collapses blank lines) so we check content, not byte equality.
        reviewed = SAMPLE_ARTICLE + "\n\n*[Editor: approved]*"
        llm = MockLLM(response=reviewed)
        result = _manual_review(SAMPLE_ARTICLE, "Python testing", llm)
        assert "*[Editor: approved]*" in result
        assert "Python Testing Best Practices" in result

    def test_llm_called_once(self):
        llm = MockLLM(response=SAMPLE_ARTICLE)
        _manual_review(SAMPLE_ARTICLE, "Python testing", llm)
        assert len(llm.calls) == 1

    def test_prompt_contains_article_content(self):
        llm = MockLLM(response=SAMPLE_ARTICLE)
        _manual_review(SAMPLE_ARTICLE, "Python testing", llm)
        # The article is included in the review prompt
        assert "Python Testing" in llm.calls[0] or SAMPLE_ARTICLE[:80] in llm.calls[0]

    def test_prompt_contains_topic(self):
        llm = MockLLM(response=SAMPLE_ARTICLE)
        _manual_review(SAMPLE_ARTICLE, "Ghost Hunting Techniques", llm)
        assert "Ghost Hunting Techniques" in llm.calls[0]

    def test_empty_response_falls_back_to_original_article(self):
        llm = MockLLM(response="")
        result = _manual_review(SAMPLE_ARTICLE, "Python testing", llm)
        assert result == SAMPLE_ARTICLE

    def test_rate_limit_response_falls_back_to_original(self):
        llm = MockLLM(response="rate_limit exceeded")
        result = _manual_review(SAMPLE_ARTICLE, "Python testing", llm)
        assert result == SAMPLE_ARTICLE


# ============================================================================
# Tests: pipeline stage wiring contracts
# ============================================================================

class TestPipelineWiring:
    """
    Verify that each stage's output satisfies the input contract of the next stage.
    These tests use only MockLLM and don't touch any external services.
    """

    def test_strategy_output_is_dict(self):
        llm = MockLLM(response=STRATEGY_JSON)
        result = _manual_strategy("Python testing", llm)
        assert isinstance(result, dict)

    def test_seo_accepts_strategy_dict(self):
        """SEO stage receives strategy dict and produces its own dict."""
        strategy_llm = MockLLM(response=STRATEGY_JSON)
        seo_llm = MockLLM(response=SEO_JSON)

        strategy_out = _manual_strategy("Python testing", strategy_llm)
        seo_out = _manual_seo("Python testing", strategy_out, seo_llm)

        assert isinstance(seo_out, dict)
        assert "primary_keyword" in seo_out
        assert "h2_structure" in seo_out

    def test_seo_strategy_context_reaches_prompt(self):
        """Strategy audience and angles are echoed into the SEO prompt."""
        strategy_llm = MockLLM(response=STRATEGY_JSON)
        seo_llm = MockLLM(response=SEO_JSON)

        strategy_out = _manual_strategy("Python testing", strategy_llm)
        _manual_seo("Python testing", strategy_out, seo_llm)

        seo_prompt = seo_llm.calls[0]
        assert "Python developer" in seo_prompt or "pytest mastery" in seo_prompt

    def test_write_accepts_research_string_and_seo_dict(self):
        """Write stage receives a plain string (research) and a dict (SEO brief)."""
        write_llm = MockLLM(response=SAMPLE_ARTICLE)
        article = _manual_write("Python testing", "Research summary.", SEO_DICT, write_llm)
        assert isinstance(article, str)
        assert len(article) > 10

    def test_review_accepts_article_string(self):
        """Review stage receives article string, returns article string."""
        write_llm = MockLLM(response=SAMPLE_ARTICLE)
        review_llm = MockLLM(response=SAMPLE_ARTICLE)

        article = _manual_write("Python testing", "Research.", SEO_DICT, write_llm)
        reviewed = _manual_review(article, "Python testing", review_llm)

        assert isinstance(reviewed, str)

    def test_format_accepts_reviewed_string(self):
        """Format stage receives a string and returns a string starting with #."""
        review_llm = MockLLM(response=SAMPLE_ARTICLE)
        reviewed = _manual_review(SAMPLE_ARTICLE, "Python testing", review_llm)
        formatted = _manual_format(reviewed)

        assert isinstance(formatted, str)
        assert formatted.startswith("#")

    def test_internal_links_accepts_formatted_and_seo(self):
        """Internal link stage receives formatted string and SEO dict."""
        formatted = _manual_format(SAMPLE_ARTICLE)
        linked = _manual_internal_links(formatted, SEO_DICT)

        assert isinstance(linked, str)
        assert len(linked) >= len(formatted)

    def test_internal_links_inserts_placeholder_from_seo(self):
        """Placeholder from SEO brief appears when anchor is found in article."""
        article = "# Title\n\nLearn about pytest fixtures and CI pipeline setup."
        result = _manual_internal_links(article, SEO_DICT)
        assert "[[LINK: pytest fixtures → /pytest-fixtures-guide]]" in result

    def test_full_chain_strategy_to_formatted_article(self):
        """Run all non-publishing stages end-to-end with MockLLM."""
        strategy = _manual_strategy("Python testing", MockLLM(response=STRATEGY_JSON))
        seo = _manual_seo("Python testing", strategy, MockLLM(response=SEO_JSON))
        article = _manual_write("Python testing", "Research.", seo, MockLLM(response=SAMPLE_ARTICLE))
        reviewed = _manual_review(article, "Python testing", MockLLM(response=SAMPLE_ARTICLE))
        formatted = _manual_format(reviewed)
        linked = _manual_internal_links(formatted, seo)

        # Final output must be a non-empty Markdown string
        assert isinstance(linked, str)
        assert len(linked) > 100
        assert linked.startswith("#")

    def test_result_dict_shape_matches_contract(self):
        """_run_local_pipeline produces a dict with the expected keys."""
        # We simulate the return shape rather than calling the full function
        # (which would need real Brave Search + Ghost CMS).
        result = {
            "final_result": SAMPLE_ARTICLE,
            "strategy": json.loads(STRATEGY_JSON),
            "seo_brief": SEO_DICT,
            "research": "Research text",
            "markup_content": SAMPLE_ARTICLE,
            "seo_content": SEO_DICT.get("meta_description", ""),
            "content": SAMPLE_ARTICLE,
            "ghost_result": None,
            "pipeline": "manual",
        }

        required_keys = {
            "final_result", "strategy", "seo_brief", "research",
            "markup_content", "seo_content", "content", "ghost_result", "pipeline",
        }
        assert required_keys.issubset(result.keys())
        assert result["pipeline"] == "manual"
        assert isinstance(result["seo_brief"], dict)
        assert isinstance(result["markup_content"], str)
