#!/usr/bin/env python3
"""
Semantic SEO Pipeline — Hybrid Orchestrator

Architecture sources:
  - christancho/Blogging-with-CrewAI     (Chris)  — agents, tasks, Ghost publishing
  - MissMathWizz/Multi-Agent-Blog-Generator (MathWizz) — strategy-first, YAML config
  - Nimish-0070/AI-CONTENT-GENERATOR-AGENT (Nimish)  — dual-path, model fallback
  - ARCHITECTURE.md                       (Ours)   — research-first, internal linker

Dual-path execution (Nimish pattern):
  1. Attempt CrewAI sequential pipeline (8 tasks)
  2. If CrewAI fails or returns nothing, fall through to manual pipeline
     (calls agent functions directly using AnthropicLLM)

Context passing (MathWizz pattern):
  Manual pipeline passes typed dicts between stages — fully debuggable.

Pipeline stages:
  1. Strategy    — competitive landscape JSON
  2. SEO         — keyword brief JSON (upstream, before research)
  3. Research    — Brave Search + source URLs
  4. Write       — 3500-word article, 10+ inline hyperlinks
  5. Review      — quality gate, returns FULL article
  6. Format      — clean Markdown for Ghost CMS
  7. InternalLink — insert [[LINK: anchor → /path]] placeholders
  8. Publish     — Ghost CMS draft via JWT API
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Optional, Dict, Any

from crewai import Crew, Process
from config import Config
from agents import SEOAgents
from tasks import SEOTasks
from constants import *
from tools import sanitize_output, GhostCMSTool, generate_ghost_jwt
from utils import (
    validate_ghost_post,
    publish_to_ghost,
    extract_blog_metadata,
    extract_content_from_file,
    extract_title_from_content,
    extract_meta_description_from_content,
    extract_article_content_from_file,
    clean_markdown_content,
    analyze_content_quality,
    show_content_preview,
    RateLimitHandler,
    ProgressTracker,
)


# ============================================================================
# Manual fallback pipeline — plain Python, no CrewAI dependency
# Mirrors MathWizz's pure-method-chain pattern, using AnthropicLLM for calls.
# ============================================================================

def _manual_strategy(topic: str, llm) -> Dict[str, Any]:
    """Run strategy analysis directly, bypassing CrewAI."""
    prompt = f"""As a Strategic Content Analyst, analyze the competitive landscape for:
"{topic}"

Return a JSON dict ONLY (no markdown fences) with these keys:
{{
    "target_audience": {{"primary": "...", "pain_points": ["..."], "preferences": "..."}},
    "competitive_landscape": {{"gaps": ["..."], "opportunities": ["..."]}},
    "content_angles": ["angle1", "angle2", "angle3"],
    "market_opportunities": ["opportunity1", "opportunity2"],
    "strategic_positioning": {{"unique_value": "...", "key_messages": ["..."], "tone": "..."}}
}}"""
    raw = llm.run(prompt, max_tokens=1024)
    raw = sanitize_output(raw)
    if not raw:
        return {
            "target_audience": {"primary": "general audience", "pain_points": [], "preferences": ""},
            "content_angles": [f"Comprehensive guide to {topic}"],
            "strategic_positioning": {"unique_value": f"Expert insights on {topic}", "tone": "informative"},
        }
    try:
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group()) if m else json.loads(raw)
    except Exception:
        return {"target_audience": {"primary": "general audience"}, "content_angles": [topic]}


def _manual_seo(topic: str, strategy: Dict, llm) -> Dict[str, Any]:
    """Run SEO analysis directly, receiving strategy dict as context."""
    angles = strategy.get("content_angles", [topic])
    audience = strategy.get("target_audience", {}).get("primary", "general audience")

    prompt = f"""As an SEO Specialist, produce a complete SEO brief for: "{topic}"

Context:
- Target audience: {audience}
- Content angles: {', '.join(angles[:3])}

Return a JSON dict ONLY (no markdown fences) with these keys:
{{
    "primary_keyword": "...",
    "cluster_keywords": ["...", "..."],
    "lsi_keywords": ["...", "...", "...", "...", "..."],
    "h2_structure": ["H2 heading 1", "H2 heading 2", "H2 heading 3", "H2 heading 4"],
    "meta_title": "50-60 char title",
    "meta_description": "150-160 char description",
    "internal_link_targets": [{{"anchor": "...", "url": "/..."}}],
    "seo_recommendations": ["tip1", "tip2", "tip3"]
}}"""
    raw = llm.run(prompt, max_tokens=1024)
    raw = sanitize_output(raw)
    if not raw:
        return {
            "primary_keyword": topic,
            "cluster_keywords": [],
            "lsi_keywords": [],
            "h2_structure": [f"Understanding {topic}", f"How {topic} Works",
                             f"Benefits of {topic}", f"Getting Started with {topic}"],
            "meta_title": topic[:60],
            "meta_description": f"A comprehensive guide to {topic}."[:160],
            "internal_link_targets": [],
            "seo_recommendations": [],
        }
    try:
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group()) if m else json.loads(raw)
    except Exception:
        return {"primary_keyword": topic, "h2_structure": [], "meta_title": topic, "meta_description": ""}


def _manual_research(topic: str, seo: Dict, llm) -> str:
    """Run research via Brave Search + LLM synthesis."""
    from tools import BraveSearchTool
    search = BraveSearchTool()
    results = []

    angles = seo.get("cluster_keywords", []) or [topic]
    queries = [topic] + angles[:2] + [f"{topic} best practices", f"{topic} 2025"]

    for q in queries[:4]:
        raw = search._run(q, count=5)
        results.append(f"### Search: {q}\n{sanitize_output(raw)}")

    research_text = "\n\n".join(results)

    # Synthesise with LLM
    primary = seo.get("primary_keyword", topic)
    synth_prompt = f"""You are a research specialist. Synthesise the following search results
into a coherent research brief for an article on "{topic}" (primary keyword: {primary}).

Include:
- Key findings grouped by subtopic
- Authoritative URLs with titles and credibility notes
- Relevant statistics and data points

SEARCH RESULTS:
{research_text[:6000]}

Provide a structured research brief with source URLs."""

    synthesis = llm.run(synth_prompt, max_tokens=2048)
    synthesis = sanitize_output(synthesis)
    return synthesis if synthesis else research_text


def _manual_write(topic: str, research: str, seo: Dict, llm) -> str:
    """Write the full article using research + SEO brief."""
    h2s = seo.get("h2_structure", [])
    primary = seo.get("primary_keyword", topic)
    lsi = ", ".join(seo.get("lsi_keywords", []))
    headings_block = "\n".join(f"  ## {h}" for h in h2s) if h2s else ""

    prompt = f"""Write a COMPLETE 3500-word article on "{topic}".

SEO BRIEF:
- Primary keyword: {primary}
- LSI keywords: {lsi}
- Use these H2 headings (in order):
{headings_block if headings_block else "  (generate 4 appropriate H2 headings)"}

RESEARCH BRIEF:
{research[:4000]}

REQUIREMENTS:
1. 400–500 word introduction with hook and context
2. Four body sections of 600–700 words each, using the H2 headings above
3. 300–400 word conclusion with takeaways and next steps
4. Minimum 10 inline hyperlinks using URLs from the research brief
   - Format: [anchor text](https://url.com)
   - Distribute: 2–3 in intro, 2–3 per section
5. ## References section at end (5–10 numbered sources)

Return the complete article in Markdown format."""

    article = llm.run(prompt, max_tokens=8192)
    article = sanitize_output(article)
    return article if article else f"# {topic}\n\n(Article generation failed — please retry.)"


def _manual_review(article: str, topic: str, llm) -> str:
    """Polish and verify the article, returning the FULL article."""
    prompt = f"""Review and polish this article on "{topic}".

MANDATORY CHECKS:
1. Count inline hyperlinks — must be at least 10 in the article body
2. If fewer than 10 links, ADD MORE now using official docs or authoritative sources
3. Verify all links use [anchor](url) format
4. Check technical accuracy and logical flow
5. Fix any grammar or clarity issues

CRITICAL: Return the COMPLETE article — all sections, all paragraphs.
Do NOT return a review report or summary.

ARTICLE:
{article[:12000]}"""

    reviewed = llm.run(prompt, max_tokens=8192)
    reviewed = sanitize_output(reviewed)
    return reviewed if reviewed else article


def _manual_format(article: str) -> str:
    """Format article as Ghost CMS-compatible Markdown."""
    import re
    # Ensure title is H1
    if not article.startswith("#"):
        lines = article.split("\n", 1)
        title_line = lines[0].strip()
        rest = lines[1] if len(lines) > 1 else ""
        article = f"# {title_line}\n\n{rest}"
    # Collapse excessive blank lines
    article = re.sub(r"\n{3,}", "\n\n", article)
    return article.strip()


def _manual_internal_links(article: str, seo: Dict) -> str:
    """Insert [[LINK: anchor → /url]] placeholders from SEO brief."""
    targets = seo.get("internal_link_targets", [])
    if not targets:
        return article

    lines = article.split("\n")
    insertions = 0

    for target in targets[:5]:
        if insertions >= 5:
            break
        anchor = target.get("anchor", "")
        url = target.get("url", "")
        if not anchor or not url:
            continue
        # Find first line containing the anchor text (case-insensitive), not already linked
        import re
        pattern = re.compile(re.escape(anchor), re.IGNORECASE)
        for i, line in enumerate(lines):
            if pattern.search(line) and "[[LINK:" not in line and "](http" not in line:
                lines[i] = pattern.sub(f"[[LINK: {anchor} → {url}]]", line, count=1)
                insertions += 1
                break

    return "\n".join(lines)


def _manual_publish(title: str, content: str, meta_description: str, tags: list) -> str:
    """Publish to Ghost CMS, returning result JSON string."""
    tool = GhostCMSTool()
    payload = json.dumps({
        "title": title,
        "content": content,
        "meta_description": meta_description,
        "tags": tags,
    })
    return tool._run(payload)


def _run_local_pipeline(topic: str) -> Dict[str, Any]:
    """
    Manual pipeline — runs when CrewAI is unavailable or returns nothing.
    Returns the same dict shape as _run_crewai_pipeline().

    Context passing: MathWizz pure Python dict pattern — typed return values
    passed explicitly as arguments to each successive stage.
    """
    from llm import llm as anthropic_llm

    print("\n[Manual Pipeline] Starting fallback pipeline...")

    strategy = _manual_strategy(topic, anthropic_llm)
    print(f"[Manual Pipeline] Strategy complete — {len(strategy.get('content_angles', []))} angles")

    seo = _manual_seo(topic, strategy, anthropic_llm)
    print(f"[Manual Pipeline] SEO brief complete — primary: {seo.get('primary_keyword', '?')}")

    research = _manual_research(topic, seo, anthropic_llm)
    print(f"[Manual Pipeline] Research complete — {len(research)} chars")

    article = _manual_write(topic, research, seo, anthropic_llm)
    print(f"[Manual Pipeline] Draft complete — {len(article)} chars")

    reviewed = _manual_review(article, topic, anthropic_llm)
    print(f"[Manual Pipeline] Review complete — {len(reviewed)} chars")

    formatted = _manual_format(reviewed)
    linked = _manual_internal_links(formatted, seo)
    print(f"[Manual Pipeline] Format + links complete")

    title = extract_title_from_content(linked) or topic
    meta = seo.get("meta_description") or extract_meta_description_from_content(linked)
    tags = ([seo.get("primary_keyword")] + seo.get("cluster_keywords", []))[:5]
    tags = [t for t in tags if t]

    ghost_result = _manual_publish(title, linked, meta, tags)
    print(f"[Manual Pipeline] Ghost publish complete")

    return {
        "final_result": linked,
        "strategy": strategy,
        "seo_brief": seo,
        "research": research,
        "markup_content": linked,
        "seo_content": seo.get("meta_description", ""),
        "content": article,
        "ghost_result": ghost_result,
        "pipeline": "manual",
    }


# ============================================================================
# CrewAI pipeline
# ============================================================================

def _run_crewai_pipeline(topic: str, rate_limit_handler) -> Optional[Dict[str, Any]]:
    """
    Run the full 8-stage CrewAI sequential pipeline.
    Returns result dict, or None if execution fails.
    """
    try:
        agents = SEOAgents()
        tasks_obj = SEOTasks()

        # Define all 8 tasks
        strategy_task = tasks_obj.strategy_task(topic)
        seo_task = tasks_obj.upstream_seo_task(topic)
        research_task = tasks_obj.research_task(topic)
        content_task = tasks_obj.content_creation_task(topic)
        review_task = tasks_obj.quality_review_task(topic)
        html_task = tasks_obj.html_formatting_task()
        link_task = tasks_obj.internal_link_task()
        ghost_task = tasks_obj.ghost_publication_task(topic)

        # Context chaining (Chris .context pattern)
        seo_task.context = [strategy_task]
        research_task.context = [seo_task]
        content_task.context = [research_task]
        review_task.context = [content_task]
        html_task.context = [review_task]
        link_task.context = [html_task, seo_task]   # linker needs SEO brief too
        ghost_task.context = [link_task]

        crew = Crew(
            agents=[
                agents.strategy_agent(),
                agents.seo_agent(),
                agents.research_agent(),
                agents.content_writer_agent(),
                agents.quality_reviewer_agent(),
                agents.html_formatter_agent(),
                agents.internal_linker_agent(),
                agents.ghost_publisher_agent(),
            ],
            tasks=[
                strategy_task, seo_task, research_task, content_task,
                review_task, html_task, link_task, ghost_task,
            ],
            process=Process.sequential,
            verbose=True,
        )

        result = rate_limit_handler.execute_with_retry(crew)

        # Extract per-task outputs
        task_results = []
        task_list = [strategy_task, seo_task, research_task, content_task,
                     review_task, html_task, link_task, ghost_task]

        for task in task_list:
            if hasattr(task, "output") and task.output:
                if hasattr(task.output, "raw_output"):
                    task_results.append(task.output.raw_output)
                elif hasattr(task.output, "result"):
                    task_results.append(task.output.result)
                else:
                    task_results.append(str(task.output))
            else:
                task_results.append(result)

        return {
            "final_result": result,
            "strategy": task_results[0] if len(task_results) > 0 else None,
            "seo_brief": task_results[1] if len(task_results) > 1 else None,
            "research": task_results[2] if len(task_results) > 2 else None,
            "content": task_results[3] if len(task_results) > 3 else None,
            "markup_content": task_results[4] if len(task_results) > 4 else None,
            "seo_content": task_results[1] if len(task_results) > 1 else None,
            "ghost_result": task_results[7] if len(task_results) > 7 else None,
            "pipeline": "crewai",
        }

    except Exception as e:
        print(f"\n[CrewAI Pipeline] Failed: {e}")
        return None


# ============================================================================
# Main orchestrator class
# ============================================================================

class SEOPipeline:
    """
    Main orchestrator for the semantic SEO pipeline.

    Execution strategy (Nimish dual-path):
      1. Try CrewAI sequential pipeline
      2. If it fails, fall back to manual pipeline (AnthropicLLM direct calls)
    """

    def __init__(self, profile: Optional[str] = None):
        try:
            Config.load(profile=profile)
            Config.validate_config()
            self.output_dir = Config.OUTPUT_DIR
            self.rate_limit_handler = RateLimitHandler(max_tpm=200000)
            self.progress_tracker = ProgressTracker()
            self._ensure_output_directory()
        except ValueError as e:
            print(f"Configuration error: {e}")
            print("\nRequired environment variables:")
            print("  LLM_API_KEY or OPENAI_API_KEY  — LLM provider key")
            print("  BRAVE_SEARCH_API_KEY            — Brave Search key")
            print("  GHOST_API_KEY                  — Ghost CMS admin API key")
            print("  GHOST_API_URL                  — Ghost CMS URL")
            print("\nOptional:")
            print("  ANTHROPIC_API_KEY  — enables manual fallback pipeline")
            print("  DEMO_MODE=true     — skip API calls (development mode)")
            sys.exit(1)

    def _ensure_output_directory(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_blog_post(self, topic: str) -> Optional[str]:
        """
        Generate a complete SEO-optimised blog post on the given topic.

        Returns the path to the saved output file, or None on failure.
        """
        print(f"\nStarting SEO pipeline for: '{topic}'")
        print("=" * SEPARATOR_LENGTH)
        print(f"Stages: {TOTAL_WORKFLOW_STEPS} | "
              f"Profile: {os.getenv('SEO_PROFILE', 'default')} | "
              f"Demo: {Config.DEMO_MODE}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            # ------------------------------------------------------------------
            # DEMO MODE — return a canned result without burning API credits
            # ------------------------------------------------------------------
            if Config.DEMO_MODE:
                print("\n[DEMO MODE] Returning canned output.")
                demo_content = f"# {topic}\n\n*Demo mode enabled — no API calls made.*\n\n"
                demo_content += "This is a placeholder article generated in DEMO_MODE.\n"
                crew_results = {
                    "markup_content": demo_content,
                    "content": demo_content,
                    "final_result": demo_content,
                    "seo_content": "",
                    "ghost_result": None,
                    "pipeline": "demo",
                }
                return self._save_and_report(topic, timestamp, crew_results)

            # ------------------------------------------------------------------
            # ATTEMPT 1: CrewAI pipeline
            # ------------------------------------------------------------------
            print("\nAttempting CrewAI pipeline...")
            crew_results = _run_crewai_pipeline(topic, self.rate_limit_handler)

            # ------------------------------------------------------------------
            # ATTEMPT 2: Manual fallback pipeline (Nimish dual-path)
            # ------------------------------------------------------------------
            if not crew_results:
                print("\nCrewAI pipeline returned nothing — switching to manual pipeline.")
                if not Config.ANTHROPIC_API_KEY and not Config.LLM_API_KEY:
                    print("ERROR: Manual fallback requires ANTHROPIC_API_KEY or LLM_API_KEY.")
                    return None
                crew_results = _run_local_pipeline(topic)

            return self._save_and_report(topic, timestamp, crew_results)

        except Exception as e:
            print(f"\nPipeline error: {e}")
            return None

    def _save_and_report(self, topic: str, timestamp: str, results: Dict) -> str:
        """Save output file and print summary. Returns file path."""
        markup_content = results.get("markup_content")
        content = results.get("content")
        final_result = results.get("final_result")
        seo_content = results.get("seo_content")
        ghost_result = results.get("ghost_result")
        pipeline_used = results.get("pipeline", "unknown")

        # Priority: reviewed content → draft → final result (Chris pattern)
        blog_content_to_save = (
            str(markup_content) if markup_content
            else str(content) if content
            else str(final_result) if final_result
            else f"# {topic}\n\n(No content generated.)"
        )
        blog_content_to_save = sanitize_output(blog_content_to_save, fallback=f"# {topic}")

        # Save to file (MathWizz timestamped filename)
        safe_topic = topic.replace(" ", "_").replace("/", "_")[:60]
        output_filename = f"blog_post_{timestamp}_{safe_topic}{OUTPUT_FILE_EXTENSION}"
        output_path = os.path.join(self.output_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(blog_content_to_save)

        print(f"\nPipeline complete [{pipeline_used}]")
        print(f"Output: {output_path}")

        if ghost_result:
            print("\nGhost CMS result:")
            print("=" * SEPARATOR_LENGTH)
            print(ghost_result)
            print("=" * SEPARATOR_LENGTH)

        title, meta_description, tags = extract_blog_metadata(markup_content, seo_content, topic)
        clean_content = clean_markdown_content(blog_content_to_save)
        show_content_preview(clean_content, title, meta_description, tags)

        return output_path

    # ------------------------------------------------------------------
    # List / publish existing posts (Chris pattern)
    # ------------------------------------------------------------------

    def list_generated_posts(self):
        """List all previously generated blog posts with interactive menu."""
        if not os.path.exists(self.output_dir):
            print("No output directory found. No posts have been generated yet.")
            return

        files = [f for f in os.listdir(self.output_dir) if f.endswith(OUTPUT_FILE_EXTENSION)]
        if not files:
            print("No blog posts found in the output directory.")
            return

        while True:
            print(f"\nGenerated Blog Posts ({len(files)} found):")
            print("=" * SEPARATOR_LENGTH)
            for i, filename in enumerate(sorted(files, reverse=True), 1):
                parts = filename.replace(OUTPUT_FILE_EXTENSION, "").split("_")
                if len(parts) >= 3:
                    date_part = parts[2]
                    topic_part = "_".join(parts[4:]) if len(parts) > 4 else "unknown_topic"
                    try:
                        formatted_date = datetime.strptime(date_part, "%Y%m%d").strftime("%Y-%m-%d")
                    except Exception:
                        formatted_date = date_part
                    print(f"{i:2d}. {topic_part.replace('_', ' ').title()}")
                    print(f"    Generated: {formatted_date}")
                    print(f"    File: {filename}")
                    print()

            print("=" * SEPARATOR_LENGTH)
            print("Options: 1. View  2. Delete  3. Exit")
            choice = input("\nSelect (1-3): ").strip()

            if choice == "1":
                self._view_post_menu(files)
            elif choice == "2":
                self._delete_post_menu(files)
                files = [f for f in os.listdir(self.output_dir) if f.endswith(OUTPUT_FILE_EXTENSION)]
                if not files:
                    print("No more posts.")
                    break
            elif choice == "3":
                break

    def _view_post_menu(self, files):
        try:
            post_num = input(f"\nPost number to view (1-{len(files)}): ").strip()
            post_index = int(post_num) - 1
            if 0 <= post_index < len(files):
                self._view_post_details(sorted(files, reverse=True)[post_index])
        except ValueError:
            print("Invalid number.")

    def _view_post_details(self, filename):
        file_path = os.path.join(self.output_dir, filename)
        if not os.path.exists(file_path):
            print(f"File not found: {filename}")
            return
        content_data = extract_content_from_file(file_path)
        show_content_preview(
            content_data["content"],
            content_data["title"],
            content_data["meta_description"],
            Config.GHOST_CONFIG["default_tags"],
        )
        while True:
            action = input("\n1. Post to Ghost CMS  2. Back: ").strip()
            if action == "1":
                self._publish_post_to_ghost(filename, content_data)
                break
            elif action == "2":
                break

    def _publish_post_to_ghost(self, filename, content_data):
        print("Publishing to Ghost CMS...")
        success = publish_to_ghost(
            title=content_data["title"],
            content=content_data["content"],
            meta_description=content_data["meta_description"],
            tags=Config.GHOST_CONFIG["default_tags"],
        )
        print("Published!" if success else "Publish failed.")

    def _delete_post_menu(self, files):
        try:
            post_num = input(f"\nPost number to delete (1-{len(files)}): ").strip()
            post_index = int(post_num) - 1
            if 0 <= post_index < len(files):
                filename = sorted(files, reverse=True)[post_index]
                confirmation = input(f"Type DELETE to confirm deletion of {filename}: ").strip()
                if confirmation == "DELETE":
                    os.remove(os.path.join(self.output_dir, filename))
                    print("Deleted.")
                else:
                    print("Cancelled.")
        except ValueError:
            print("Invalid number.")

    def publish_existing_post(self, filename: str):
        """Publish an existing output file to Ghost CMS."""
        if not filename.endswith(OUTPUT_FILE_EXTENSION):
            filename += OUTPUT_FILE_EXTENSION
        file_path = os.path.join(self.output_dir, filename)
        if not os.path.exists(file_path):
            print(f"File not found: {filename}")
            print("Use --list to see available posts.")
            return
        content_data = extract_content_from_file(file_path)
        show_content_preview(
            content_data["content"],
            content_data["title"],
            content_data["meta_description"],
            Config.GHOST_CONFIG["default_tags"],
        )
        if input("\nPublish to Ghost CMS? (y/n): ").lower().strip() in ("y", "yes"):
            success = publish_to_ghost(
                title=content_data["title"],
                content=content_data["content"],
                meta_description=content_data["meta_description"],
                tags=Config.GHOST_CONFIG["default_tags"],
            )
            print("Published!" if success else "Publish failed.")


# ---------------------------------------------------------------------------
# Backward-compatibility alias
# ---------------------------------------------------------------------------
BlogGenerationCrew = SEOPipeline


# ============================================================================
# CLI entry point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Semantic SEO Pipeline — generate and publish SEO-optimised articles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --topic "Ghost tours in New Orleans"
  python main.py --topic "Biblical archaeology discoveries 2025" --profile diggingscriptures
  python main.py --topic "Experiential dining in Tokyo" --profile devour_destinations
  python main.py --list
  python main.py --publish "blog_post_20260323_120000_Ghost_tours.md"
        """,
    )
    parser.add_argument("--topic", "-t", type=str, help="Topic to write about")
    parser.add_argument(
        "--profile", "-p", type=str, default=None,
        help="Site profile from pipeline.yaml (e.g. cursedtours, diggingscriptures)",
    )
    parser.add_argument("--list", "-l", action="store_true", help="List generated posts")
    parser.add_argument("--publish", type=str, help="Publish an existing post by filename")
    parser.add_argument(
        "--no-approval", action="store_true",
        help="(Legacy flag, kept for compatibility — approval step was removed)",
    )
    args = parser.parse_args()

    if args.profile:
        os.environ["SEO_PROFILE"] = args.profile

    pipeline = SEOPipeline(profile=args.profile)

    if args.list:
        pipeline.list_generated_posts()
        return

    if args.publish:
        pipeline.publish_existing_post(args.publish)
        return

    topic = args.topic
    if not topic:
        print("Semantic SEO Pipeline")
        print("=" * 40)
        topic = input("Enter topic: ").strip()
        if not topic:
            print("No topic provided. Exiting.")
            return

    result_path = pipeline.generate_blog_post(topic)
    if result_path:
        print(f"\nDone. Article at: {result_path}")
    else:
        print("\nPipeline failed. Check error messages above.")


if __name__ == "__main__":
    main()
