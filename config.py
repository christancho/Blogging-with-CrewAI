import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the blog generation crew"""
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
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
        required_vars = [
            "OPENAI_API_KEY",
            "BRAVE_SEARCH_API_KEY",
            "GHOST_API_KEY",
            "GHOST_API_URL"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
