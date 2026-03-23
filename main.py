#!/usr/bin/env python3
"""
Semantic SEO Pipeline — CLI entry point.

All pipeline logic lives in orchestrator.py and stages/.
This module handles CLI arg parsing, config loading, and output persistence.

Usage:
  python main.py --topic "Ghost tours in New Orleans"
  python main.py --topic "Biblical archaeology" --profile diggingscriptures
  python main.py --list
  python main.py --publish "blog_post_20260323_120000_Ghost_tours.md"
"""

import argparse
import os
import sys
from datetime import datetime
from typing import Optional

from config import Config
from constants import OUTPUT_FILE_EXTENSION, SEPARATOR_LENGTH
from context import PipelineContext
from orchestrator import build_pipeline
from tools import sanitize_output
from utils import (
    RateLimitHandler,
    show_content_preview,
    extract_blog_metadata,
    extract_content_from_file,
    clean_markdown_content,
    publish_to_ghost,
)


# ============================================================================
# Output helpers
# ============================================================================

def _save_output(ctx: PipelineContext, output_dir: str) -> str:
    """Save pipeline output to a timestamped Markdown file. Returns the path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = ctx.topic.replace(" ", "_").replace("/", "_")[:60]
    filename = f"blog_post_{timestamp}_{safe_topic}{OUTPUT_FILE_EXTENSION}"
    path = os.path.join(output_dir, filename)

    os.makedirs(output_dir, exist_ok=True)

    content = ctx.final_content or f"# {ctx.topic}\n\n(No content generated.)"
    content = sanitize_output(content, fallback=f"# {ctx.topic}")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return path


def _print_summary(ctx: PipelineContext, output_path: str) -> None:
    """Print a structured pipeline summary to the console."""
    print(f"\nPipeline complete [{ctx.pipeline_path}]")
    print(f"Output: {output_path}")

    # Stage timings table
    if ctx.stage_timings:
        print(f"\n{'Stage':<16} {'Time':>6}")
        print("-" * 24)
        for name, elapsed in ctx.stage_timings.items():
            print(f"  {name:<14} {elapsed:>5.1f}s")
        total = sum(ctx.stage_timings.values())
        print(f"  {'total':<14} {total:>5.1f}s")

    # SEO score from optimizer
    if ctx.seo_score is not None:
        print(f"\nSEO score: {ctx.seo_score:.0f}/100")

    # Audit report summary
    if ctx.audit_report:
        score = ctx.audit_report.get("score", 0)
        issues = ctx.audit_report.get("issues", [])
        recs = ctx.audit_report.get("recommendations", [])
        print(f"Audit score: {score:.0f}/100")
        if issues:
            print(f"Issues ({len(issues)}):")
            for issue in issues[:5]:
                print(f"  - {issue}")
        if recs:
            print(f"Recommendations:")
            for rec in recs[:3]:
                print(f"  → {rec}")

    # Ghost CMS result
    if ctx.publish_result:
        if ctx.publish_result.get("status") == "success":
            print(f"\nGhost CMS: draft created")
            print(f"  {ctx.publish_result.get('draft_url', '?')}")
        else:
            print(f"\nGhost CMS: {ctx.publish_result.get('message', 'error')}")

    # Any pipeline errors
    if ctx.errors:
        print(f"\nPipeline issues ({len(ctx.errors)}):")
        for err in ctx.errors:
            print(f"  {err}")

    # Content preview
    content = ctx.final_content or ""
    clean = clean_markdown_content(content)
    title, meta, tags = extract_blog_metadata(content, "", ctx.topic)
    show_content_preview(clean, title, meta, tags)


# ============================================================================
# Main pipeline class — thin wrapper around Orchestrator + output handling
# ============================================================================

class SEOPipeline:
    """
    User-facing pipeline wrapper.

    Handles config loading, LLM construction, output saving, and the interactive
    list/publish CLI features. The actual pipeline execution is delegated entirely
    to orchestrator.build_pipeline().
    """

    def __init__(self, profile: Optional[str] = None):
        try:
            Config.load(profile=profile)
            Config.validate_config()
            self.output_dir = Config.OUTPUT_DIR
            self._profile = profile
        except ValueError as e:
            print(f"Configuration error: {e}")
            print("\nRequired environment variables:")
            print("  LLM_API_KEY or OPENAI_API_KEY  — LLM provider key")
            print("  BRAVE_SEARCH_API_KEY            — Brave Search key")
            print("  GHOST_API_KEY                  — Ghost CMS admin API key")
            print("  GHOST_API_URL                  — Ghost CMS URL")
            print("\nOptional:")
            print("  ANTHROPIC_API_KEY  — enables Anthropic model fallback chain")
            print("  DEMO_MODE=true     — skip API calls (development mode)")
            print("  INTERNAL_LINKER_URL — Cloudflare Worker for real internal links")
            sys.exit(1)

    def generate_blog_post(self, topic: str) -> Optional[str]:
        """
        Generate a complete SEO-optimised blog post on the given topic.
        Returns the path to the saved output file, or None on failure.
        """
        print(f"\nStarting SEO pipeline for: '{topic}'")
        print("=" * SEPARATOR_LENGTH)
        print(f"Profile: {self._profile or 'default'} | Demo: {Config.DEMO_MODE}")

        # Demo mode — no API calls
        if Config.DEMO_MODE:
            print("\n[DEMO MODE] Returning canned output.")
            ctx = PipelineContext(
                topic=topic, profile=self._profile, pipeline_path="demo"
            )
            ctx.draft = f"# {topic}\n\n*Demo mode enabled — no API calls made.*\n"
            path = _save_output(ctx, self.output_dir)
            _print_summary(ctx, path)
            return path

        try:
            from llm import AnthropicLLM
            llm = AnthropicLLM()

            pipeline = build_pipeline(llm=llm)
            ctx = pipeline.run(topic, profile=self._profile)
            ctx.pipeline_path = "manual"

            path = _save_output(ctx, self.output_dir)
            _print_summary(ctx, path)
            return path

        except Exception as e:
            print(f"\nPipeline error: {e}")
            return None

    # ------------------------------------------------------------------
    # List / view / delete previously generated posts
    # ------------------------------------------------------------------

    def list_generated_posts(self) -> None:
        """List all previously generated blog posts with interactive menu."""
        if not os.path.exists(self.output_dir):
            print("No output directory found. No posts have been generated yet.")
            return

        files = sorted(
            [f for f in os.listdir(self.output_dir) if f.endswith(OUTPUT_FILE_EXTENSION)],
            reverse=True,
        )
        if not files:
            print("No blog posts found in the output directory.")
            return

        while True:
            print(f"\nGenerated Blog Posts ({len(files)} found):")
            print("=" * SEPARATOR_LENGTH)
            for i, filename in enumerate(files, 1):
                print(f"  {i:2d}. {filename}")
            print("\nOptions: 1. View  2. Delete  3. Exit")
            choice = input("\nSelect (1-3): ").strip()

            if choice == "1":
                self._view_post_menu(files)
            elif choice == "2":
                self._delete_post_menu(files)
                files = sorted(
                    [f for f in os.listdir(self.output_dir)
                     if f.endswith(OUTPUT_FILE_EXTENSION)],
                    reverse=True,
                )
                if not files:
                    print("No more posts.")
                    break
            elif choice == "3":
                break

    def _view_post_menu(self, files):
        try:
            idx = int(input(f"Post number (1-{len(files)}): ").strip()) - 1
            if 0 <= idx < len(files):
                path = os.path.join(self.output_dir, files[idx])
                data = extract_content_from_file(path)
                show_content_preview(
                    data["content"], data["title"], data["meta_description"], []
                )
        except ValueError:
            print("Invalid number.")

    def _delete_post_menu(self, files):
        try:
            idx = int(input(f"Post number to delete (1-{len(files)}): ").strip()) - 1
            if 0 <= idx < len(files):
                filename = files[idx]
                if input(f"Type DELETE to confirm deletion of {filename}: ").strip() == "DELETE":
                    os.remove(os.path.join(self.output_dir, filename))
                    print("Deleted.")
                else:
                    print("Cancelled.")
        except ValueError:
            print("Invalid number.")

    def publish_existing_post(self, filename: str) -> None:
        """Publish an existing output file to Ghost CMS."""
        if not filename.endswith(OUTPUT_FILE_EXTENSION):
            filename += OUTPUT_FILE_EXTENSION
        path = os.path.join(self.output_dir, filename)
        if not os.path.exists(path):
            print(f"File not found: {filename}")
            print("Use --list to see available posts.")
            return
        data = extract_content_from_file(path)
        show_content_preview(
            data["content"], data["title"], data["meta_description"], []
        )
        if input("\nPublish to Ghost CMS? (y/n): ").lower().strip() in ("y", "yes"):
            success = publish_to_ghost(
                title=data["title"],
                content=data["content"],
                meta_description=data["meta_description"],
                tags=Config.GHOST_CONFIG["default_tags"],
            )
            print("Published!" if success else "Publish failed.")


# Backward-compatibility alias
BlogGenerationCrew = SEOPipeline


# ============================================================================
# CLI entry point
# ============================================================================

def main() -> None:
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
