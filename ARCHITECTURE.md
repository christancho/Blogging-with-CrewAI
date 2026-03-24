# Semantic SEO Pipeline Architecture

## Multi-Agent Architecture Document

**Version:** 1.0
**Date:** March 23, 2026
**Author:** Genaro Vasquez
**System:** Cowork Skill-Chain (Lightweight Multi-Agent)

---

## 1. Executive Summary

This document defines the architecture for a multi-agent semantic SEO pipeline serving the Astro site portfolio (erin-gee-site, cursedtours, devour-destinations, diggingscriptures, protrainerprep). Rather than deploying a heavyweight framework like CrewAI, the system is implemented as a **skill-chain within Cowork** — a master orchestrator skill that sequentially invokes specialist skills, passing a shared context object that accumulates through each step. Every specialist receives the full history of the pipeline so far, ensuring each agent is hydrated on the complete process context.

The pipeline is built around **semantic SEO principles** — building topical authority through comprehensive, intent-driven content that maps entity relationships, topic clusters, and concept hierarchies rather than chasing individual keywords. It transforms a topic into a fully optimized, semantically rich, internally linked article — and includes a scheduled auditor that identifies content needing refresh, feeding the loop back to the beginning.

---

## 2. Design Principles

**Skill-chain, not framework.** Each specialist is a Cowork skill. The orchestrator is a skill that calls other skills sequentially, accumulating context. No external orchestration layer, no containerized agents, no message queues. Just skills calling skills with a growing context payload.

**Full context hydration.** Every specialist receives the complete shared context object — not just its immediate input. The Writer sees the Strategist's brief AND the Researcher's sources. The Editor sees the brief, research, AND the draft. This eliminates information loss between steps.

**Research-before-execute.** Every agent operating in an evolving domain (SEO, web standards, content strategy) must research current best practices before executing its task. No agent relies solely on training data for tactical decisions.

**Three-tier source credibility.**

| Tier | Label | Criteria | Action |
|------|-------|----------|--------|
| 1 | Established Consensus | Consistent across authoritative sources over 2+ years | Adopt confidently |
| 2 | Emerging Signal | Data-backed, from credible source, but < 1 year old | Adopt cautiously, note as emerging |
| 3 | Fad / Unproven | Single source, no data, volatile discourse | Flag explicitly, do not adopt |

**Authoritative source list.** Google Search Central, MDN Web Docs, W3C specifications, Moz foundational guides, Ahrefs data studies, Search Engine Journal (editorial, not sponsored), web.dev by Google. Consistency over time is signal. Volatility is a red flag.

**No black hat.** Never adopt black hat or gray hat tactics regardless of claimed results. If a technique appears in Google's spam policies, it's permanently excluded.

---

## 3. System Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                          │
│              (Master Skill / Context Bus)                │
│                                                         │
│  Shared Context Object ──────────────────────────────┐  │
│  {                                                   │  │
│    topic, brief, research, draft,                    │  │
│    editedDraft, seoOptimized, linkedContent, audit   │  │
│  }                                                   │  │
│                                                      │  │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐             │  │
│  │  1   │→ │  2   │→ │  3   │→ │  4   │→            │  │
│  │ SEO  │  │Resrch│  │Writer│  │Editor│             │  │
│  │Strat.│  │      │  │      │  │      │             │  │
│  └──────┘  └──────┘  └──────┘  └──────┘             │  │
│                                                      │  │
│  ┌──────┐  ┌──────┐                                  │  │
│  │  5   │→ │  6   │→  PUBLISH                        │  │
│  │OnPage│  │Intern│                                  │  │
│  │ Opt. │  │Linker│                                  │  │
│  └──────┘  └──────┘                                  │  │
│                                                      │  │
└──────────────────────────────────────────────────────┘  │
                                                          │
┌──────────────────────────┐                              │
│  7. CONTENT AUDITOR      │ ← Scheduled (weekly)         │
│  (Independent / Async)   │──── feeds topics back ───────┘
│  GSC data → decay flags  │
└──────────────────────────┘
```

**Flow:** Topic → Strategist → Researcher → Writer → Editor → On-Page Optimizer → Internal Linker → Publish

**Feedback Loop:** Content Auditor runs on a schedule, identifies underperforming content, and feeds refresh candidates back into the pipeline as new Strategist inputs.

---

## 4. Shared Context Object

The context object is the pipeline's backbone. It starts nearly empty and grows at each step. Every specialist receives the full object and appends its output.

```json
{
  "pipelineId": "string (UUID)",
  "createdAt": "ISO 8601 timestamp",
  "status": "strategist | researcher | writer | editor | optimizer | linker | complete | failed",
  "topic": "string — the seed topic or keyword",

  "brief": {
    "primaryKeyword": "string",
    "secondaryKeywords": ["string"],
    "longTailKeywords": ["string"],
    "searchIntent": "informational | navigational | transactional | commercial",
    "targetWordCount": "number",
    "competitorUrls": ["string"],
    "competitorGaps": ["string — content gaps identified"],
    "recommendedStructure": {
      "h1": "string",
      "sections": [
        {
          "heading": "string",
          "purpose": "string",
          "targetKeywords": ["string"]
        }
      ]
    },
    "serpFeatures": ["featured snippet | PAA | video | image pack | etc."],
    "difficulty": "number (0-100)",
    "monthlySearchVolume": "number",
    "notes": "string — strategist commentary"
  },

  "research": {
    "sources": [
      {
        "url": "string",
        "title": "string",
        "credibilityTier": "1 | 2 | 3",
        "keyInsights": ["string"],
        "dataPoints": ["string"],
        "publishedDate": "string"
      }
    ],
    "competitorContentAnalysis": [
      {
        "url": "string",
        "wordCount": "number",
        "strengths": ["string"],
        "weaknesses": ["string"],
        "uniqueAngles": ["string — things they cover that we should too"],
        "missedAngles": ["string — things they miss that we can cover"]
      }
    ],
    "uniqueAngleRecommendation": "string — our differentiation strategy",
    "statistics": [
      {
        "stat": "string",
        "source": "string",
        "year": "number"
      }
    ]
  },

  "draft": {
    "content": "string (markdown)",
    "wordCount": "number",
    "readabilityScore": "number (Flesch-Kincaid)",
    "headingCount": { "h1": "number", "h2": "number", "h3": "number" },
    "writerNotes": "string"
  },

  "editedDraft": {
    "content": "string (markdown)",
    "changes": [
      {
        "type": "tone | fact | structure | readability | brand-voice",
        "description": "string",
        "location": "string — approximate section"
      }
    ],
    "brandVoiceScore": "number (0-100)",
    "readabilityScore": "number (Flesch-Kincaid)",
    "factCheckFlags": ["string — any claims that couldn't be verified"],
    "editorNotes": "string"
  },

  "seoOptimized": {
    "content": "string (markdown, with optimizations applied)",
    "metadata": {
      "metaTitle": "string (≤60 chars)",
      "metaDescription": "string (≤160 chars)",
      "ogTitle": "string",
      "ogDescription": "string",
      "canonicalUrl": "string",
      "urlSlug": "string"
    },
    "headerHierarchy": ["string — validated H1 > H2 > H3 chain"],
    "keywordDensity": {
      "primary": "number (%)",
      "secondary": { "keyword": "number (%)" }
    },
    "imageAltSuggestions": [
      {
        "imageDescription": "string",
        "suggestedAlt": "string"
      }
    ],
    "schemaMarkup": "object (JSON-LD Article schema)",
    "optimizerNotes": "string"
  },

  "linkedContent": {
    "content": "string (markdown, with internal links inserted)",
    "internalLinks": [
      {
        "anchorText": "string",
        "targetUrl": "string",
        "targetTitle": "string",
        "context": "string — why this link is relevant",
        "position": "string — section where inserted"
      }
    ],
    "linkingReport": {
      "totalLinksAdded": "number",
      "hubPageLinks": "number",
      "relatedArticleLinks": "number",
      "orphanPagesConnected": ["string — URLs of previously orphaned content now linked"],
      "suggestedBacklinks": ["string — existing articles that should link TO this new piece"]
    },
    "linkerNotes": "string"
  },

  "audit": {
    "runDate": "ISO 8601 timestamp",
    "performanceData": [
      {
        "url": "string",
        "clicks28d": "number",
        "impressions28d": "number",
        "avgPosition": "number",
        "ctr": "number (%)"
      }
    ],
    "decayFlags": [
      {
        "url": "string",
        "signal": "ranking drop | traffic decline | CTR decline",
        "severity": "low | medium | high",
        "recommendation": "refresh | rewrite | merge | redirect"
      }
    ],
    "cannibalizationFlags": [
      {
        "keyword": "string",
        "competingUrls": ["string"],
        "recommendation": "string"
      }
    ],
    "refreshQueue": [
      {
        "url": "string",
        "priority": "number (1-10)",
        "reason": "string",
        "suggestedAction": "string"
      }
    ]
  }
}
```

---

## 5. Specialist Agent Specifications

### 5.1 — Orchestrator (Master Skill)

**Role:** Pipeline controller and context bus.

**Responsibility:**

- Initializes the shared context object with the seed topic
- Invokes each specialist skill in sequence, passing the full context
- Receives updated context back from each specialist
- Runs quality gates between steps (described in Section 6)
- Handles errors: if a specialist fails, logs the error, retries once, and if still failing, halts the pipeline and reports
- Triggers deployment when the pipeline completes successfully

**Implementation Notes:**

- This is the skill the user invokes directly. It reads the topic from user input (or from the Content Auditor's refresh queue).
- Between each step, it writes the current context to a temp file so the pipeline can be resumed if interrupted.
- It logs timing for each step so pipeline performance can be monitored.

**Maps to:** Custom skill (needs to be built). This is the Phase 3 deliverable.

**Pseudocode:**

```
function runPipeline(topic):
    context = initContext(topic)

    context = invokeSkill("seo-strategist", context)
    if not qualityGate("strategist", context): halt("Brief incomplete")

    context = invokeSkill("researcher", context)
    if not qualityGate("researcher", context): halt("Research insufficient")

    context = invokeSkill("writer", context)
    if not qualityGate("writer", context): halt("Draft below threshold")

    context = invokeSkill("editor", context)
    if not qualityGate("editor", context): halt("Edit quality insufficient")

    context = invokeSkill("on-page-optimizer", context)
    if not qualityGate("optimizer", context): halt("SEO optimization incomplete")

    context = invokeSkill("internal-linker", context)
    if not qualityGate("linker", context): halt("Linking failed")

    presentForReview(context)
    // User reviews and approves before publish
```

---

### 5.2 — SEO Strategist

**Role:** Maps the semantic landscape for a given topic — identifying entities, related concepts, topic relationships, and intent patterns that define how modern search engines understand the subject.

**Input:** `context.topic` (string — target topic or seed concept)

**Process:**

1. **Research current semantic SEO best practices** — before doing anything else, query current Google Search Central guidance, recent Moz/Ahrefs studies, and any algorithm update news. Focus specifically on how search engines evaluate topical authority, entity relationships, and content comprehensiveness. Apply the three-tier credibility filter.
2. **Semantic landscape mapping** — identify the core entities, related concepts, and topic relationships surrounding the seed topic. Map People Also Ask (PAA) questions to understand the question graph. Identify co-occurring entities and concepts that search engines associate with comprehensive coverage of this topic. Use GSC performance data to find related queries the site already ranks for and identify semantic gaps in existing coverage.
3. **Search intent and SERP analysis** — analyze the current SERP for the target topic. What search intent dominates? What content formats rank (guides, comparisons, how-tos)? What SERP features appear (featured snippets, PAA, knowledge panels)? Map the intent spectrum — a single topic often spans multiple intents that a comprehensive piece should address.
4. **Competitive topical gap analysis** — pull the top 5 ranking pages. Analyze not just what they cover, but how deeply they cover it. Which subtopics and entities do they address? Where do they leave semantic gaps — related concepts, questions, or entity relationships they fail to explore? Identify where our sites can differentiate through deeper topical coverage.
5. **Semantic content brief generation** — synthesize everything into a structured brief organized around topic clusters and entity relationships, not just keywords. Include recommended article structure that maps to the semantic landscape, target word count, entity/concept targets, PAA questions to address, and SERP feature opportunities.

**Output:** Populates `context.brief`

**Maps to:**

| Component | Existing Tool | Status |
|-----------|--------------|--------|
| SEO audit framework | `marketing:seo-audit` skill | Exists |
| GSC keyword data | `google-search-console` MCP (get_performance_data, detect_quick_wins) | Exists |
| SERP / PAA analysis | WebSearch tool | Exists |
| Competitive content pull | WebFetch tool | Exists |

**Custom work needed:** A wrapper prompt that chains these tools with a semantic-first methodology — mapping the entity and concept landscape before narrowing to specific keyword targets. Outputs the brief in the context object format. This is a skill prompt, not code.

---

### 5.3 — Researcher

**Role:** Deep-dives into the topic to gather authoritative sources, data, and differentiation angles.

**Input:** `context.topic` + `context.brief`

**Process:**

1. **Source discovery** — based on the brief's keyword targets and recommended structure, find 8-15 authoritative sources. Prioritize primary research, data studies, and official documentation over opinion pieces.
2. **Data/statistics gathering** — extract specific data points, statistics, and quotable findings that will strengthen the article's authority.
3. **Competitor content deep-dive** — read the top 3-5 competitor articles identified in the brief. Document their strengths, weaknesses, and the angles they miss.
4. **Unique angle recommendation** — based on competitor gaps and available data, recommend a specific differentiation strategy for the article.

**Output:** Populates `context.research`

**Maps to:**

| Component | Existing Tool | Status |
|-----------|--------------|--------|
| Web research | WebSearch tool | Exists |
| Page content reading | WebFetch tool | Exists |
| GSC competitor data | `google-search-console` MCP | Exists |

**Custom work needed:** Skill prompt that orchestrates research in a structured way and outputs into the context format.

**Note:** In practice, the Strategist and Researcher could be merged into a single skill invocation with two prompt phases. They're separated here for clarity and because they serve distinct purposes — strategy vs. evidence gathering. The orchestrator can choose to run them as one step or two.

---

### 5.4 — Writer

**Role:** Produces comprehensive, intent-driven content that naturally satisfies semantic search signals through depth of coverage rather than keyword targeting.

**Input:** `context.topic` + `context.brief` + `context.research`

**Process:**

1. **Internalize the semantic brief** — understand the entity landscape, topic relationships, and intent spectrum mapped by the Strategist. The goal is comprehensive topical coverage, not hitting keyword density targets. The brief's structure reflects the semantic landscape — each section exists because it addresses a concept cluster or entity relationship that search engines expect in authoritative content on this topic.
2. **Review research packet** — understand available sources, data points, and the unique angle recommendation. Identify which entities and concepts from the brief have strong supporting evidence and which need careful treatment.
3. **Write for topical authority** — following the brief's recommended structure, produce content that comprehensively covers the topic's semantic landscape. Address the PAA questions and related concepts identified in the brief. Let keywords emerge naturally from thorough coverage rather than inserting them artificially. Incorporate data, sources, and entity relationships. Maintain the site's brand voice throughout.
4. **Semantic self-assessment** — before handing off, evaluate against the semantic brief. Does the content address the full intent spectrum? Are the key entities and concept relationships covered? Would a reader (or search engine) consider this a comprehensive, authoritative treatment of the topic? Does it answer the PAA questions naturally within the flow?

**Output:** Populates `context.draft`

**Maps to:**

| Component | Existing Tool | Status |
|-----------|--------------|--------|
| Content writing framework | `marketing:content-creation` skill | Exists |
| Brand voice reference | User's existing writer skill | Exists |
| Readability scoring | Bash (can compute Flesch-Kincaid with Python) | Exists |

**Custom work needed:** Integration prompt that feeds the semantic brief and research into the writing skill, emphasizing comprehensive topical coverage over keyword insertion. The user's existing writer skill likely has brand voice baked in — this needs to be preserved and referenced.

---

### 5.5 — Editor

**Role:** Quality control — tone, accuracy, readability, brand voice.

**Input:** `context.topic` + `context.brief` + `context.research` + `context.draft`

**Process:**

1. **Brand voice enforcement** — check the draft against the site's brand voice guidelines. Flag sections that deviate.
2. **Fact verification** — cross-reference claims in the draft against the research packet's sources. Flag any claims that aren't supported by the gathered evidence.
3. **Readability scoring** — compute Flesch-Kincaid and flag sections that are too dense or too thin.
4. **Structural review** — verify the draft follows the brief's recommended structure. Are all sections present? Is the flow logical?
5. **Edit and annotate** — make direct edits where possible. For judgment calls, leave change notes explaining the rationale.

**Output:** Populates `context.editedDraft`

**Maps to:**

| Component | Existing Tool | Status |
|-----------|--------------|--------|
| Brand voice checking | `brand-voice:enforce-voice` skill | Exists |
| Readability analysis | Bash (Python libraries) | Exists |

**Custom work needed:** Prompt that combines brand voice enforcement with fact-checking and structural review in a single pass. The brand-voice skill handles tone; the custom layer handles facts and structure.

---

### 5.6 — On-Page Optimizer

**Role:** Semantic markup and technical SEO optimization — ensuring the article's meaning, entities, and topical signals are machine-readable alongside traditional on-page elements.

**Input:** Full context through `context.editedDraft`

**Process:**

1. **Research current semantic and on-page best practices** — mandatory first step. Query Google Search Central and recent authoritative guides. Apply three-tier credibility filter. Focus on current guidance for structured data, entity markup, semantic HTML, header structure, and meta descriptions. How are search engines currently interpreting schema markup, entity signals, and content structure?
2. **Schema markup and structured data** — generate comprehensive JSON-LD schema beyond basic Article markup. Include relevant entity types (Person, Organization, HowTo, FAQ, Product — whatever fits the content). Map entities mentioned in the article to schema properties. If the article addresses PAA questions, consider FAQPage schema. The goal is to make the article's semantic relationships machine-readable.
3. **Entity and concept signal validation** — verify that the key entities and concepts from the Strategist's semantic landscape are present and contextually clear. Search engines identify entities through co-occurrence and context — ensure the article provides enough semantic context around each entity for accurate interpretation.
4. **Meta title optimization** — craft a meta title (≤60 chars) that reflects the topic's core entity/concept, is compelling for CTR, and differentiates from competitor titles in the SERP analysis.
5. **Meta description optimization** — craft a meta description (≤160 chars) that addresses the primary search intent, includes a call-to-action, and signals the content's comprehensive scope.
6. **Semantic header hierarchy** — ensure exactly one H1, logical H2/H3 nesting. Headers should reflect the topic cluster structure — each H2 maps to a concept cluster, H3s to subtopics within that cluster. Validate that the heading hierarchy mirrors the semantic landscape from the brief.
7. **Natural keyword distribution check** — verify the primary topic terms appear naturally throughout. Focus on semantic relevance over density metrics. Flag any sections where keyword insertion feels forced or where natural topic coverage has left semantic gaps.
8. **Image alt text suggestions** — suggest descriptive, entity-aware alt text that reinforces the article's semantic signals.
9. **URL slug optimization** — suggest a clean, topic-descriptive URL slug.
10. **Open Graph tags** — generate og:title, og:description for social sharing.

**Output:** Populates `context.seoOptimized`

**Maps to:**

| Component | Existing Tool | Status |
|-----------|--------------|--------|
| Current best practices research | WebSearch tool | Exists |
| GSC data for SERP context | `google-search-console` MCP | Exists |
| PageSpeed for technical context | `pagespeed_analyze` tool | Exists |

**Custom work needed:** This is a fully custom skill. No existing skill covers semantic on-page optimization at this granularity. Needs to be built as a Cowork skill with the research-first pattern and entity-awareness baked into its prompt.

---

### 5.7 — Internal Linker

**Role:** Builds and reinforces the topic cluster architecture across the site portfolio, signaling topical authority to search engines through deliberate internal link structure — not just connecting pages for crawlability.

**Input:** Full context through `context.seoOptimized` + the site's content inventory

**Process:**

1. **Build/load site content inventory with topic mapping** — use GSC sitemap tools to get all indexed URLs. For each, pull the title, primary queries (from GSC query data), and identify which topic cluster it belongs to. Cache this inventory with topic cluster assignments so it doesn't need rebuilding every run.
2. **Determine topic cluster placement** — based on the new article's semantic brief, determine which topic cluster(s) it belongs to. Is it a pillar/hub page for a cluster? A supporting spoke article? Does it bridge two clusters? This determines the linking strategy.
3. **Map topical relationships** — identify existing articles across the portfolio that share entities, concepts, or topic cluster membership with the new article. Prioritize articles in the same topic cluster, then adjacent clusters with shared entities.
4. **Build contextual links that signal topical authority** — for each related article, identify a natural place in the new content where a link reinforces the topic cluster relationship. Use descriptive, semantically relevant anchor text that signals the relationship between the two pieces (not generic "click here" or exact-match keyword anchors). Target 3-8 internal links per article, weighted toward same-cluster connections.
5. **Insert links** — add the links directly into the article content with the chosen anchor text.
6. **Orphan page rescue** — identify existing content with zero or very few internal links. If topically relevant to the new article or its cluster, connect them to strengthen the cluster's link graph.
7. **Hub-spoke architecture enforcement** — if the new article is a spoke in a topic cluster, ensure it links to the cluster's pillar/hub page. Flag the hub page for a reciprocal link update. If the new article IS a pillar page, identify all existing spoke articles that should link to it.
8. **Cross-cluster bridging** — identify opportunities where the new article naturally connects two topic clusters (e.g., an article about "travel insurance" bridges a "travel planning" cluster and a "personal finance" cluster). Add bridge links that signal these topical relationships.
9. **Generate backlink suggestions** — identify existing articles that should link TO this new piece to strengthen cluster architecture. Output as a prioritized action list.

**Output:** Populates `context.linkedContent`

**Maps to:**

| Component | Existing Tool | Status |
|-----------|--------------|--------|
| Sitemap URL inventory | `google-search-console:get_sitemap_urls` | Exists |
| Page performance data | `google-search-console:get_top_pages_tool` | Exists |
| Page content reading | WebFetch tool | Exists |

**Custom work needed:** Fully custom skill. The topic cluster mapping, semantic anchor text selection, and hub-spoke architecture enforcement are all novel. This skill also needs a caching mechanism for the site inventory with topic cluster assignments — possibly a file in the Cowork workspace that gets refreshed weekly by the Content Auditor.

---

### 5.8 — Content Auditor (Scheduled)

**Role:** Monitors published content performance and identifies optimization opportunities.

**Input:** GSC performance data across all sites in the portfolio (all indexed content)

**Process:**

1. **Pull performance data** — query GSC for all pages' clicks, impressions, CTR, and average position over the last 28 days and 90 days.
2. **Detect ranking decay** — compare 28-day to 90-day data. Flag pages where position has dropped 3+ spots or clicks have declined 20%+.
3. **Detect traffic decline** — flag pages where clicks have dropped 30%+ period-over-period.
4. **Detect CTR decline** — flag pages where CTR has dropped significantly relative to their position (may indicate stale meta descriptions or increased SERP competition).
5. **Content cannibalization check** — identify keywords where multiple pages across the portfolio compete for the same query. Flag pairs with similar average positions.
6. **Thin content identification** — flag pages with high impressions but very low CTR and poor positions (may indicate content doesn't match search intent).
7. **Generate refresh queue** — prioritize flagged pages by opportunity size (impressions × potential CTR improvement) and output as a ranked list.

**Output:** Populates `context.audit` and generates a refresh queue that feeds back into the pipeline.

**Maps to:**

| Component | Existing Tool | Status |
|-----------|--------------|--------|
| Performance data | `google-search-console:get_performance_data` | Exists |
| Quick wins detection | `google-search-console:detect_quick_wins` | Exists |
| Period comparison | `google-search-console:compare_periods_tool` | Exists |
| Date trends | `google-search-console:get_date_trend_tool` | Exists |
| Top pages | `google-search-console:get_top_pages_tool` | Exists |
| Scheduling | `mcp__scheduled-tasks__create_scheduled_task` | Exists |

**Custom work needed:** Skill prompt that orchestrates the GSC tools into a cohesive audit workflow. Scheduled task configuration to run weekly/bi-weekly.

---

## 6. Quality Gates

The orchestrator enforces quality gates between steps. If a gate fails, the pipeline halts and reports the issue rather than propagating poor-quality output downstream.

| Gate | Between | Pass Criteria |
|------|---------|---------------|
| Brief Completeness | Strategist → Researcher | `brief.primaryKeyword` exists, `brief.searchIntent` is set, `brief.recommendedStructure` has ≥3 sections, ≥2 competitor URLs analyzed |
| Research Sufficiency | Researcher → Writer | ≥5 sources with credibility tier 1 or 2, ≥3 data points, unique angle recommendation present |
| Draft Quality | Writer → Editor | Word count within 20% of target, all recommended sections present, readability score ≥ 40 (Flesch-Kincaid) |
| Edit Quality | Editor → Optimizer | Brand voice score ≥ 70, zero unresolved fact-check flags, readability score ≥ 50 |
| SEO Completeness | Optimizer → Linker | Meta title ≤ 60 chars, meta description ≤ 160 chars, schema markup valid, keyword density between 0.5-3% |
| Linking Quality | Linker → Publish | ≥ 3 internal links added, no broken link targets, linking report generated |

**On failure:** The orchestrator logs which gate failed and why, then presents the issue to the user. The user can choose to fix manually, re-run the failed step with adjusted parameters, or override the gate.

---

## 7. Skill-to-Agent Mapping Table

| Agent | Existing Skills/Tools | Custom Skill Needed | Phase |
|-------|----------------------|---------------------|-------|
| **Orchestrator** | None (pure orchestration) | Yes — master skill with context management, sequential invocation, quality gates | Phase 3 |
| **SEO Strategist** | `marketing:seo-audit`, GSC MCP tools, WebSearch | Yes — wrapper prompt that chains tools and outputs structured brief | Phase 1 |
| **Researcher** | WebSearch, WebFetch, GSC MCP | Yes — prompt that structures research and outputs into context format | Phase 1 |
| **Writer** | `marketing:content-creation`, user's existing writer skill | Partial — integration prompt that feeds brief + research into writer | Phase 1 |
| **Editor** | `brand-voice:enforce-voice` | Partial — prompt that adds fact-checking and structural review to brand voice | Phase 1 |
| **On-Page Optimizer** | WebSearch (for best practices research), GSC MCP, PageSpeed | Yes — fully custom skill | Phase 2 |
| **Internal Linker** | GSC sitemap tools, WebFetch | Yes — fully custom skill with site inventory caching | Phase 2 |
| **Content Auditor** | GSC MCP tools (all performance tools), scheduled-tasks | Yes — skill prompt + scheduled task configuration | Phase 4 |

---

## 8. Implementation Phases

### Phase 1 — Wire Up Existing Skills

**Goal:** Get the core pipeline working end-to-end with existing tools, even if manually orchestrated.

**Deliverables:**

- SEO Strategist skill prompt (wraps `marketing:seo-audit` + GSC tools)
- Researcher skill prompt (wraps WebSearch + WebFetch)
- Writer integration prompt (feeds brief + research into existing writer skill)
- Editor skill prompt (wraps `brand-voice:enforce-voice` + fact-checking layer)
- Shared context object template (JSON file)
- Manual test: run each skill in sequence on a real topic from one of the Astro sites, passing context manually

**Success criteria:** A complete context object from topic to edited draft, produced by invoking skills in sequence.

**Estimated effort:** 2-3 sessions

---

### Phase 2 — Build Custom Skills

**Goal:** Build the two novel specialists that don't map to existing skills.

**Deliverables:**

- On-Page Optimizer skill (SKILL.md + any supporting reference files)
- Internal Linker skill (SKILL.md + site inventory caching mechanism)
- Test both skills with real content from the Astro sites
- Validate optimizer output against manual SEO checklist
- Validate linker output against actual site structure

**Success criteria:** Both skills produce correct, actionable output when given a real edited draft and site inventory.

**Estimated effort:** 2-3 sessions

---

### Phase 3 — Build the Orchestrator

**Goal:** Automate the full pipeline with a single skill invocation.

**Deliverables:**

- Orchestrator skill (SKILL.md) that:
  - Accepts a topic as input
  - Initializes the context object
  - Invokes each specialist in sequence
  - Passes accumulated context at each step
  - Enforces quality gates
  - Writes intermediate context to file for resumability
  - Presents final output for user review
- Error handling and retry logic
- Pipeline timing/logging

**Success criteria:** User invokes one skill with a topic, and receives a fully optimized, internally linked article ready for review.

**Estimated effort:** 1-2 sessions

---

### Phase 4 — Build the Content Auditor

**Goal:** Automated content health monitoring.

**Deliverables:**

- Content Auditor skill prompt
- Scheduled task configuration (weekly or bi-weekly)
- Output format: prioritized refresh queue as markdown report
- Integration point: refresh queue items can be fed back into the orchestrator as new topics

**Success criteria:** Auditor runs on schedule, produces actionable refresh recommendations, and its output can seed a new pipeline run.

**Estimated effort:** 1 session

---

### Phase 5 — Test and Iterate

**Goal:** Run the full pipeline on real articles from the Astro sites and refine.

**Deliverables:**

- Run pipeline on 3-5 real topics
- Document what works and what breaks
- Refine quality gate thresholds based on real output
- Tune keyword density targets, readability thresholds, and linking targets
- Optimize prompt wording for each specialist based on output quality
- Benchmark: compare pipeline output quality to manually written/optimized articles

**Success criteria:** Pipeline consistently produces articles that meet or exceed the quality of manually optimized content, with measurable GSC performance improvements within 30-60 days of publication.

**Estimated effort:** Ongoing, 1 session per iteration cycle

---

## 9. Guardrails (Applied to Every Agent)

These guardrails are embedded in every specialist skill's prompt. They are not optional or context-dependent — they apply universally.

**Research-first mandate.** Every agent operating in SEO, web standards, or content strategy MUST research current best practices before executing. The research step is not skippable. If web search is unavailable, the agent must flag this and proceed with explicit caveats that its output reflects training data, not current guidance.

**Three-tier credibility filter.** All sources encountered during research are classified into the three tiers defined in Section 2. Only Tier 1 and Tier 2 recommendations are adopted. Tier 3 items are flagged with a warning label in the output but never implemented.

**No black hat.** The following are permanently excluded regardless of any source recommending them: keyword stuffing, cloaking, hidden text, link schemes, doorway pages, scraped content, sneaky redirects, automatically generated content presented as human-written without disclosure, and any technique listed in Google's spam policies.

**No gray hat.** Techniques in a gray area (aggressive link building outreach, exact-match anchor text optimization, content spinning variations) are flagged for human review rather than implemented automatically.

**Transparency.** Every agent includes a notes field in its output. If the agent made judgment calls, deviated from the brief, or encountered conflicting guidance, it documents this in the notes. The orchestrator surfaces these notes to the user.

**Human-in-the-loop.** The pipeline does not auto-publish. The orchestrator presents the final output for human review. The user approves, requests changes, or rejects. This is a design constraint, not a temporary limitation.

---

## 10. Data Flow Diagram

```
USER INPUT                    EXTERNAL DATA
    │                              │
    ▼                              ▼
┌─────────┐    WebSearch     ┌──────────┐
│  Topic   │────────────────→│  Google   │
│  Keyword │    GSC MCP      │  Search   │
└────┬─────┘────────────────→│  Console  │
     │                       └──────────┘
     ▼                              │
┌─────────────────────────────────┐ │
│        ORCHESTRATOR             │ │
│                                 │ │
│  ┌───────────────────────────┐  │ │
│  │    SHARED CONTEXT OBJECT  │←─┼─┘
│  │                           │  │
│  │  Grows at each step:      │  │
│  │  topic → +brief →         │  │
│  │  +research → +draft →     │  │
│  │  +editedDraft →           │  │
│  │  +seoOptimized →          │  │
│  │  +linkedContent           │  │
│  └───────────────────────────┘  │
│                                 │
│  Step 1: SEO Strategist        │
│    reads: topic                 │
│    writes: brief                │
│    tools: seo-audit, GSC,      │
│           WebSearch             │
│                                 │
│  Step 2: Researcher             │
│    reads: topic, brief          │
│    writes: research             │
│    tools: WebSearch, WebFetch   │
│                                 │
│  Step 3: Writer                 │
│    reads: topic, brief,         │
│           research              │
│    writes: draft                │
│    tools: content-creation,     │
│           existing writer skill │
│                                 │
│  Step 4: Editor                 │
│    reads: topic, brief,         │
│           research, draft       │
│    writes: editedDraft          │
│    tools: brand-voice           │
│                                 │
│  Step 5: On-Page Optimizer      │
│    reads: ALL above             │
│    writes: seoOptimized         │
│    tools: WebSearch, GSC,       │
│           PageSpeed             │
│                                 │
│  Step 6: Internal Linker        │
│    reads: ALL above             │
│    writes: linkedContent        │
│    tools: GSC sitemap,          │
│           WebFetch, site cache  │
│                                 │
│  ═══════════════════════════    │
│  QUALITY GATE CHECK AT EACH    │
│  STEP BOUNDARY                 │
│  ═══════════════════════════    │
│                                 │
└────────────┬────────────────────┘
             │
             ▼
      HUMAN REVIEW
             │
             ▼
         PUBLISH
             │
             ▼
┌─────────────────────────────────┐
│      CONTENT AUDITOR            │
│      (Scheduled - Weekly)       │
│                                 │
│  Monitors: all published pages  │
│  Tools: GSC performance data    │
│  Output: refresh queue          │
│     │                           │
│     └──→ feeds back as new      │
│          topics for pipeline    │
└─────────────────────────────────┘
```

---

## 11. File Structure (Cowork Skills Layout)

```
~/.skills/semantic-seo-pipeline/
├── orchestrator/
│   └── SKILL.md              ← Master orchestrator prompt
├── seo-strategist/
│   └── SKILL.md              ← Strategist prompt (wraps seo-audit + GSC)
├── researcher/
│   └── SKILL.md              ← Research orchestration prompt
├── writer/
│   └── SKILL.md              ← Writer integration prompt
├── editor/
│   └── SKILL.md              ← Editor prompt (wraps brand-voice + fact-check)
├── on-page-optimizer/
│   └── SKILL.md              ← Custom on-page SEO skill
├── internal-linker/
│   ├── SKILL.md              ← Custom linking skill
│   └── site-inventory.json   ← Cached site content inventory
├── content-auditor/
│   └── SKILL.md              ← Audit skill (scheduled)
├── shared/
│   ├── context-template.json ← Empty context object template
│   ├── guardrails.md         ← Shared guardrails (included by all skills)
│   └── credibility-filter.md ← Three-tier source evaluation criteria
└── README.md                 ← This architecture document
```

---

## 12. Open Questions and Future Considerations

**Content inventory caching.** The Internal Linker needs a site inventory. Should this be rebuilt from scratch each run (slow, API-heavy) or cached and refreshed by the Content Auditor on its weekly schedule? The cache approach is recommended but needs a freshness mechanism.

**Strategist + Researcher merge.** These two agents have significant overlap. In practice, they may work better as a single skill with two phases. The orchestrator should be flexible enough to support both configurations.

**Parallel execution.** The current design is strictly sequential. Some steps could theoretically run in parallel (e.g., the Researcher could start while the Strategist is finishing). However, the sequential model is simpler, and the full-context-hydration pattern means later agents genuinely benefit from earlier agents' complete output. Parallelism is a premature optimization here.

**Multi-article batching.** The Content Auditor may flag 10+ articles for refresh. Should the orchestrator support batch mode (process multiple topics in sequence) or should each topic be a separate pipeline invocation? Batch mode would be more efficient but harder to monitor.

**Version control for context.** As articles get refreshed through the pipeline multiple times, it may be valuable to version the context objects. This would allow comparing what changed between the original and refreshed versions.

**GSC API rate limits.** Several agents query GSC. The orchestrator should implement rate-limit awareness to avoid hitting API quotas, especially if running in batch mode or if the Content Auditor runs on the same day as a pipeline execution.

**Brand voice evolution.** The Editor relies on brand voice guidelines. As each site's voice evolves, the guidelines need updating. Consider a periodic review process where the Editor's brand voice scoring is calibrated against recently published content the user is happy with.

---

## 13. Success Metrics

The pipeline's effectiveness should be measured against these metrics, tracked over 90-day windows:

| Metric | Measurement | Target |
|--------|-------------|--------|
| Pipeline completion rate | % of invocations that complete all 6 steps without halting | > 85% |
| Time to publish-ready | Minutes from topic input to human review stage | < 45 min |
| Content quality (human score) | User satisfaction rating on 1-5 scale | ≥ 4.0 average |
| Organic traffic per article | GSC clicks in first 30 days | Baseline + 20% vs. manual articles |
| Average position | GSC avg position for primary keyword at 60 days | Top 20 for target keywords |
| Internal link coverage | % of site pages with ≥ 3 internal links | > 80% |
| Content decay detection | % of decaying articles caught by auditor before 30%+ traffic loss | > 90% |
| Refresh impact | Traffic recovery rate for auditor-flagged refreshed articles | > 50% recovery within 60 days |
