"""
Configuration for the semantic SEO pipeline.

Loads settings in priority order:
  1. Environment variables (highest priority)
  2. pipeline.yaml profile (if --profile is set)
  3. pipeline.yaml defaults
  4. Hard-coded defaults (lowest priority)

YAML config pattern from MissMathWizz/Multi-Agent-Blog-Generator.
Env-var provider-agnostic pattern from christancho/Blogging-with-CrewAI.
"""

import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


def _load_yaml(path: str = "pipeline.yaml") -> Dict[str, Any]:
    """Load pipeline.yaml, returning empty dict if file is absent."""
    try:
        import yaml
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Warning: could not load {path}: {e}")
        return {}


def _merge_profile(base: Dict, profile_name: Optional[str]) -> Dict:
    """Deep-merge a named site profile over the base config."""
    if not profile_name:
        return base
    profiles = base.get("profiles", {})
    if profile_name not in profiles:
        print(f"Warning: profile '{profile_name}' not found in pipeline.yaml")
        return base
    import copy
    merged = copy.deepcopy(base)
    profile = profiles[profile_name]
    for section, values in profile.items():
        if isinstance(values, dict) and isinstance(merged.get(section), dict):
            merged[section].update(values)
        else:
            merged[section] = values
    return merged


class Config:
    """
    Configuration settings for the semantic SEO pipeline.

    Usage:
        Config.load(profile="cursedtours")   # call once at startup
    """

    # ============================================================================
    # LLM Provider Configuration
    # Works with any OpenAI-compatible endpoint (OpenAI, Anthropic proxy, Ollama).
    # For native Anthropic SDK (llm.py fallback), set ANTHROPIC_API_KEY.
    # ============================================================================
    LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL", "https://api.openai.com/v1")
    LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME") or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE") or os.getenv("OPENAI_TEMPERATURE", "0.7"))

    # Native Anthropic SDK key (used by llm.py manual fallback path)
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Legacy compatibility
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # ============================================================================
    # Other API Keys
    # ============================================================================
    BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")
    GHOST_API_KEY = os.getenv("GHOST_API_KEY")
    GHOST_API_URL = os.getenv("GHOST_API_URL")

    # ============================================================================
    # Demo / Development Mode (Nimish pattern)
    # Set DEMO_MODE=true to skip API calls and return canned responses.
    # ============================================================================
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() in ("1", "true", "yes")

    # ============================================================================
    # Content Settings (defaults; overridden by pipeline.yaml)
    # ============================================================================
    DEFAULT_WORD_COUNT = 3500
    BLOG_STRUCTURE = {
        "sections": 4,
        "include_intro": True,
        "include_conclusion": True,
    }

    # ============================================================================
    # SEO Settings
    # ============================================================================
    SEO_CONFIG = {
        "target_keyword_density": 1.5,
        "meta_description_length": 160,
        "title_length_max": 60,
        "h2_sections": 4,
        "include_meta_tags": True,
        "primary_keywords": 3,
        "secondary_keywords": 8,
        "lsi_keywords": 5,
    }

    # ============================================================================
    # Output Settings
    # ============================================================================
    OUTPUT_DIR = "output"
    OUTPUT_FORMAT = "markdown"

    # ============================================================================
    # Ghost CMS Settings
    # ============================================================================
    GHOST_CONFIG = {
        "publish_as_draft": True,
        "default_tags": ["blog", "auto-generated"],
    }

    # ============================================================================
    # YAML-derived pipeline config (populated by Config.load())
    # ============================================================================
    PIPELINE: Dict[str, Any] = {}

    @classmethod
    def load(cls, profile: Optional[str] = None, yaml_path: str = "pipeline.yaml") -> None:
        """
        Load pipeline.yaml and optionally apply a named site profile.
        Call once at startup: Config.load(profile="cursedtours")
        """
        base = _load_yaml(yaml_path)
        merged = _merge_profile(base, profile)
        cls.PIPELINE = merged

        # Sync content settings
        content = merged.get("content", {})
        if content.get("word_count_target"):
            cls.DEFAULT_WORD_COUNT = content["word_count_target"]

        # Sync SEO settings
        seo = merged.get("seo", {})
        if seo:
            cls.SEO_CONFIG.update({k: v for k, v in seo.items() if v is not None})

        if profile:
            print(f"Config: loaded profile '{profile}' from {yaml_path}")

    @classmethod
    def validate_config(cls) -> bool:
        """Validate required configuration. Raises ValueError on missing keys."""
        if not cls.LLM_API_KEY:
            raise ValueError("Missing LLM_API_KEY or OPENAI_API_KEY in environment variables")

        if not cls.BRAVE_SEARCH_API_KEY:
            raise ValueError("Missing BRAVE_SEARCH_API_KEY in environment variables")

        if not cls.GHOST_API_KEY:
            raise ValueError("Missing GHOST_API_KEY in environment variables")

        if not cls.GHOST_API_URL:
            raise ValueError("Missing GHOST_API_URL in environment variables")

        if not cls.LLM_MODEL_NAME:
            raise ValueError("Missing LLM_MODEL_NAME or OPENAI_MODEL_NAME in environment variables")

        if not cls.LLM_API_BASE_URL:
            raise ValueError("Missing LLM_API_BASE_URL in environment variables")

        print("Config: LLM settings")
        print(f"  Provider: {cls.LLM_API_BASE_URL}")
        print(f"  Model:    {cls.LLM_MODEL_NAME}")
        print(f"  Temp:     {cls.LLM_TEMPERATURE}")
        if cls.ANTHROPIC_API_KEY:
            print("  Anthropic native SDK key: present (manual fallback enabled)")
        if cls.DEMO_MODE:
            print("  DEMO_MODE: enabled — API calls will be skipped")

        return True
