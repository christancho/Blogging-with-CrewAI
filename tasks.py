"""
SEO pipeline task definitions.

Pipeline order (7 writing stages + 1 publish):
  1. strategy_task       — MathWizz: competitive landscape JSON
  2. upstream_seo_task   — MathWizz: SEO brief JSON (upstream, before research)
  3. research_task       — Chris: Brave Search, source URLs, credibility tiers
  4. content_creation_task — Chris: 3500-word article, 10+ inline hyperlinks
  5. quality_review_task — Chris: FULL article output (not a report)
  6. html_formatting_task — Chris: clean Markdown for Ghost CMS
  7. internal_link_task  — Ours: insert [[LINK: anchor → /url]] placeholders
  8. ghost_publication_task — Chris: JWT auth, Ghost CMS draft

Context-passing: MathWizz pure-Python dict style for manual pipeline;
CrewAI .context = [prev_task] chaining for crew pipeline.
"""

from crewai import Task
from agents import SEOAgents


class SEOTasks:
    """Define all tasks for the semantic SEO pipeline workflow."""

    def __init__(self):
        self.agents = SEOAgents()

    # ------------------------------------------------------------------
    # 1. Strategy Task — MathWizz pattern
    # ------------------------------------------------------------------
    def strategy_task(self, topic: str):
        return Task(
            description=f"""Analyze the competitive content landscape for "{topic}" and
produce a comprehensive strategy brief.

REQUIRED OUTPUT — JSON dict with these exact keys:
{{
    "target_audience": {{
        "primary": "...",
        "pain_points": ["...", "..."],
        "preferences": "..."
    }},
    "competitive_landscape": {{
        "gaps": ["...", "..."],
        "opportunities": ["...", "..."]
    }},
    "content_angles": ["angle1", "angle2", "angle3"],
    "market_opportunities": ["opportunity1", "opportunity2"],
    "strategic_positioning": {{
        "unique_value": "...",
        "key_messages": ["...", "..."],
        "tone": "..."
    }}
}}

Analysis must cover:
1. TARGET AUDIENCE — demographics, pain points, content preferences
2. COMPETITIVE LANDSCAPE — what competitors publish, what they miss
3. UNIQUE CONTENT ANGLES — 3 distinct approaches that differentiate from typical content
4. MARKET OPPORTUNITIES — underserved subtopics, trending angles
5. STRATEGIC POSITIONING — unique value proposition, recommended tone

Return the JSON dict ONLY — no markdown fences, no preamble.""",
            agent=self.agents.strategy_agent(),
            expected_output=(
                "JSON dict with keys: target_audience, competitive_landscape, "
                "content_angles, market_opportunities, strategic_positioning"
            ),
        )

    # ------------------------------------------------------------------
    # 2. Upstream SEO Task — MathWizz pattern (runs BEFORE research)
    # ------------------------------------------------------------------
    def upstream_seo_task(self, topic: str):
        return Task(
            description=f"""Using the strategy brief from the previous task, produce a
complete SEO brief for "{topic}" that will guide all downstream writing.

REQUIRED OUTPUT — JSON dict with these exact keys:
{{
    "primary_keyword": "...",
    "cluster_keywords": ["...", "..."],
    "lsi_keywords": ["...", "...", "...", "...", "..."],
    "h2_structure": ["H2 heading 1", "H2 heading 2", "H2 heading 3", "H2 heading 4"],
    "meta_title": "SEO title 50-60 chars",
    "meta_description": "Meta description 150-160 chars",
    "internal_link_targets": [
        {{"anchor": "anchor text", "url": "/suggested-path"}}
    ],
    "seo_recommendations": ["tip1", "tip2", "tip3"]
}}

Analysis must cover:
1. PRIMARY KEYWORD — single highest-value keyword for this topic
2. CLUSTER KEYWORDS — 2–3 supporting keywords that form a topical cluster
3. LSI KEYWORDS — 5 latent semantic terms that signal topical authority
4. H2 STRUCTURE — 4 heading suggestions that reflect the SEO-optimized content outline
5. META TITLE — 50–60 character title using the primary keyword
6. META DESCRIPTION — 150–160 character description that improves click-through
7. INTERNAL LINK TARGETS — pages on the same site that this article should link to
8. SEO RECOMMENDATIONS — 3 specific optimization tips for this topic

Return the JSON dict ONLY — no markdown fences, no preamble.""",
            agent=self.agents.seo_agent(),
            expected_output=(
                "JSON dict with keys: primary_keyword, cluster_keywords, lsi_keywords, "
                "h2_structure, meta_title, meta_description, internal_link_targets, "
                "seo_recommendations"
            ),
        )

    # ------------------------------------------------------------------
    # 3. Research Task — Chris pattern + three-tier credibility
    # ------------------------------------------------------------------
    def research_task(self, topic: str):
        return Task(
            description=f"""Research "{topic}" using the Brave Search tool, guided by
the strategy and SEO briefs from previous tasks.

Execute 5–7 searches covering:
  - Overview and foundational concepts
  - Key trends and recent developments (past 12 months)
  - Best practices and methodologies
  - Common challenges and solutions
  - Real-world use cases and examples
  - Expert opinions and authoritative studies
  - Future outlook

THREE-TIER SOURCE CREDIBILITY — evaluate and label each source:
  Tier 1 (preferred): Official documentation, peer-reviewed papers,
    .gov/.edu/.ac.* domains
  Tier 2 (acceptable): Established industry publications, recognized standards
    bodies, reputable news organizations
  Tier 3 (use sparingly): Expert blog posts, vendor whitepapers

Compile findings into a structured research report including:
- Key findings and insights (grouped by subtopic)
- Source URLs with titles and credibility tier — format: [Title](URL) [Tier N]
- Date/recency of information
- Direct quotes from authoritative sources (with attribution)
- Statistics and data points (with source)""",
            agent=self.agents.research_agent(),
            expected_output=(
                "Comprehensive research report with key findings, credibility-tiered "
                "source URLs, statistics, and expert quotes"
            ),
        )

    # ------------------------------------------------------------------
    # 4. Content Creation Task — Chris pattern, semantic SEO extensions
    # ------------------------------------------------------------------
    def content_creation_task(self, topic: str):
        return Task(
            description=f"""Write a COMPLETE 3500-word article on "{topic}" using
the research report and SEO brief from previous tasks.

Follow the H2 structure from the SEO brief exactly.
Incorporate the primary keyword, cluster keywords, and LSI terms naturally.

ARTICLE STRUCTURE — write FULL PARAGRAPHS for each section:
1. Introduction (400–500 words): Hook, context, overview of what readers will learn
2. Section 1 (600–700 words): Foundational concepts with explanations and examples
3. Section 2 (600–700 words): Deeper dive — methodologies, practical applications
4. Section 3 (600–700 words): Advanced concepts, best practices, case studies
5. Section 4 (500–600 words): Future trends, challenges, actionable insights
6. Conclusion (300–400 words): Key takeaways and next steps

CRITICAL: Write FULL PARAGRAPHS — not just section titles or one-liners.

MANDATORY INLINE HYPERLINKS — minimum 10, using URLs from the research report:
- Add links NATURALLY where you mention tools, concepts, frameworks, companies
- Do NOT save all links for the References section — embed them in the text
- Distribution: 2–3 in intro, 2–3 per main section
- Format: [anchor text](https://url.com)

EXAMPLES OF INLINE HYPERLINKS:
- "According to [OpenAI's documentation](https://platform.openai.com/docs), the API..."
- "Tools like [Docker](https://docker.com) and [Kubernetes](https://kubernetes.io) enable..."
- "Research from [MIT](https://mit.edu) shows that..."

REFERENCES SECTION:
- Add a "## References" section at the end
- Number list with titles and URLs
- Include 5–10 credible sources

VERIFICATION: Before finishing, count your inline hyperlinks. You must have
at least 10 links embedded in the article body (not counting the References section).""",
            agent=self.agents.content_writer_agent(),
            expected_output=(
                "Complete 3500-word article with ALL sections fully written, "
                "AT LEAST 10 inline hyperlinks, keyword integration, and References section"
            ),
        )

    # ------------------------------------------------------------------
    # 5. Quality Review Task — Chris behavioral contract (full article output)
    # ------------------------------------------------------------------
    def quality_review_task(self, topic: str):
        return Task(
            description=f"""Review the article on "{topic}" and return the COMPLETE
FINAL ARTICLE — not a review report, not a summary.

MANDATORY QUALITY CHECKS:
1. Verify the article contains AT LEAST 10 inline hyperlinks in the body text
   (not counting the References section)
2. If inline hyperlinks are missing, ADD THEM NOW using research URLs or official sources
3. Ensure hyperlinks are distributed throughout the article (intro, body sections,
   not clustered in one place)
4. Verify all links use proper Markdown format: [anchor text](https://url.com)
5. Check that links are relevant and authoritative
6. Verify keyword integration — primary keyword, cluster keywords, LSI terms
   appear naturally throughout
7. Check technical accuracy and factual correctness
8. Verify content structure follows the SEO brief's H2 headings
9. Check writing quality, clarity, and logical flow
10. Confirm word count is at least 3000 words

INLINE HYPERLINK AUDIT — add if missing:
- Link technology/tool names to their official websites
- Link research findings to original sources
- Link frameworks/libraries to their documentation
- Link companies/organizations to their main sites

CRITICAL: Your output MUST be the entire article content (3000+ words with all sections
fully written), NOT a review report or summary. Return the actual article that will
be published, with all inline hyperlinks included.""",
            agent=self.agents.quality_reviewer_agent(),
            expected_output=(
                "Complete article with all sections, full paragraphs, and AT LEAST 10 "
                "inline hyperlinks throughout the text — NOT a review report"
            ),
        )

    # ------------------------------------------------------------------
    # 6. HTML Formatting Task — Chris pattern
    # ------------------------------------------------------------------
    def html_formatting_task(self):
        return Task(
            description="""Use the Content Formatter tool to convert the reviewed article
to clean Ghost CMS-compatible Markdown.

Requirements:
- Proper heading hierarchy: # for H1 title, ## for H2 sections, ### for H3 subsections
- Format lists, code blocks, and blockquotes correctly
- Include the article title as the H1 heading
- Include the meta description as an italicized line immediately below the H1
- Preserve all inline hyperlinks in Markdown format: [text](url)
- Preserve the References section at the end
- Ensure accessibility (meaningful link text, not "click here")
- Semantic structure that Ghost CMS can process correctly""",
            agent=self.agents.html_formatter_agent(),
            expected_output="Clean Markdown formatted for Ghost CMS with proper hierarchy and preserved hyperlinks",
        )

    # ------------------------------------------------------------------
    # 7. Internal Link Task — our addition
    # ------------------------------------------------------------------
    def internal_link_task(self):
        return Task(
            description="""Review the formatted article and insert internal link
placeholders using the SEO brief's internal_link_targets.

PLACEHOLDER SYNTAX: [[LINK: anchor text → /target-url]]

RULES:
1. Identify 3–5 natural anchor text opportunities in the article
2. Match anchors against the internal_link_targets from the SEO brief
3. Insert placeholders where the link fits contextually (never forced)
4. Prefer anchor text that appears verbatim in the article
5. Do not insert a placeholder in the same sentence as an existing external link

EXAMPLES:
- Before: "Ghost tours are popular year-round."
  After:  "[[LINK: Ghost tours → /ghost-tours]] are popular year-round."

- Before: "Biblical archaeology has revealed..."
  After:  "[[LINK: Biblical archaeology → /biblical-archaeology]] has revealed..."

CRITICAL: Return the COMPLETE article with placeholders inserted — all sections,
all paragraphs, all existing hyperlinks preserved. Do not summarize or describe
what you did.""",
            agent=self.agents.internal_linker_agent(),
            expected_output=(
                "Complete article with 3–5 [[LINK: anchor → /path]] placeholders "
                "inserted at natural positions, all existing content preserved"
            ),
        )

    # ------------------------------------------------------------------
    # 8. Ghost Publication Task — Chris pattern
    # ------------------------------------------------------------------
    def ghost_publication_task(self, topic: str):
        return Task(
            description=f"""Publish the "{topic}" article to Ghost CMS using the
Ghost CMS Publisher tool.

CRITICAL — format your tool input as a JSON string with these keys:
1. Extract the article TITLE from the H1 heading or first line
2. Extract the FULL CONTENT (entire article, all paragraphs and formatting)
3. Extract the META DESCRIPTION from the italicized line below the H1,
   or from the SEO brief
4. Extract TAGS from the SEO brief (as array)

JSON format:
{{
    "title": "Article Title Here",
    "content": "FULL ARTICLE CONTENT with all sections and paragraphs",
    "meta_description": "SEO description 150-160 chars",
    "tags": ["tag1", "tag2", "tag3"]
}}

IMPORTANT: The 'content' field must contain the COMPLETE article text — not just
the title. Include all sections, paragraphs, hyperlinks, and the References section.

Call the Ghost CMS Publisher tool with this JSON string.
Report success with the draft URL, or full error details on failure.""",
            agent=self.agents.ghost_publisher_agent(),
            expected_output="Ghost CMS publication result with draft URL or detailed error",
        )


# ---------------------------------------------------------------------------
# Backward-compatibility alias
# ---------------------------------------------------------------------------
BlogTasks = SEOTasks
