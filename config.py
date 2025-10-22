import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the blog generation crew"""

    # ============================================================================
    # LLM Provider Configuration
    # ============================================================================
    # New flexible LLM configuration (supports any provider)
    LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL", "https://api.openai.com/v1")
    LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")  # Fallback to OPENAI_API_KEY
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME") or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE") or os.getenv("OPENAI_TEMPERATURE", "0.7"))

    # Legacy OpenAI configuration (for backward compatibility)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # ============================================================================
    # Other API Keys
    # ============================================================================
    BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")
    GHOST_API_KEY = os.getenv("GHOST_API_KEY")
    GHOST_API_URL = os.getenv("GHOST_API_URL")
    
    # Blog Settings
    DEFAULT_WORD_COUNT = 3500
    BLOG_STRUCTURE = {
        "sections": 4,
        "include_intro": True,
        "include_conclusion": True
    }
    
    # SEO Settings
    SEO_CONFIG = {
        "target_keyword_density": 1.5,  # 1.5% keyword density
        "meta_description_length": 160,
        "title_length_max": 60,
        "h2_sections": 4,
        "include_meta_tags": True
    }
    
    # Output Settings
    OUTPUT_DIR = "output"
    OUTPUT_FORMAT = "html"
    
    # Ghost CMS Settings
    GHOST_CONFIG = {
        "publish_as_draft": True,
        "default_tags": ["blog", "auto-generated"]  # Fallback tags if none generated
    }
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        # Required: LLM API Key (either new LLM_API_KEY or legacy OPENAI_API_KEY)
        if not cls.LLM_API_KEY:
            raise ValueError("Missing LLM_API_KEY or OPENAI_API_KEY in environment variables")

        # Required: Brave Search API Key
        if not cls.BRAVE_SEARCH_API_KEY:
            raise ValueError("Missing BRAVE_SEARCH_API_KEY in environment variables")

        # Required: Ghost CMS configuration
        if not cls.GHOST_API_KEY:
            raise ValueError("Missing GHOST_API_KEY in environment variables")
        if not cls.GHOST_API_URL:
            raise ValueError("Missing GHOST_API_URL in environment variables")

        # Validate LLM configuration
        if not cls.LLM_MODEL_NAME:
            raise ValueError("Missing LLM_MODEL_NAME or OPENAI_MODEL_NAME in environment variables")

        if not cls.LLM_API_BASE_URL:
            raise ValueError("Missing LLM_API_BASE_URL in environment variables")

        print(f"✅ LLM Configuration:")
        print(f"   Provider: {cls.LLM_API_BASE_URL}")
        print(f"   Model: {cls.LLM_MODEL_NAME}")
        print(f"   Temperature: {cls.LLM_TEMPERATURE}")

        return True
