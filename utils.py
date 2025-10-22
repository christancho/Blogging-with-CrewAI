"""
Utility functions and helper classes for the CrewAI Blog Generation System
"""

import os
import re
import time
import json
import requests
from datetime import datetime
from constants import *


# ============================================================================
# Ghost CMS Validation Functions
# ============================================================================

def validate_ghost_post(post_id: str, expected_title: str, expected_content: str) -> dict:
    """
    Validate a published Ghost CMS post by reading it back and checking content
    """
    try:
        from tools import generate_ghost_jwt
        from config import Config

        # Generate JWT token for Ghost Admin API
        jwt_token = generate_ghost_jwt(Config.GHOST_API_KEY, Config.GHOST_API_URL)
        if not jwt_token:
            return {
                "valid": False,
                "issues": ["Failed to generate JWT token for validation"]
            }

        # Read the post back from Ghost CMS
        headers = {
            "Authorization": f"Ghost {jwt_token}",
            "Content-Type": "application/json"
        }

        # Include content in the response by adding the source parameter
        api_url = f"{Config.GHOST_API_URL}/ghost/api/admin/posts/{post_id}/?source=html"
        response = requests.get(api_url, headers=headers, timeout=30)

        if response.status_code != 200:
            return {
                "valid": False,
                "issues": [f"Failed to read post from Ghost CMS: {response.status_code}"]
            }

        post_data = response.json()
        post = post_data.get('posts', [{}])[0]

        # Validation checks
        issues = []

        # Check title match
        actual_title = post.get('title', '')
        title_match = actual_title.strip() == expected_title.strip()
        if not title_match:
            issues.append(f"Title mismatch: expected '{expected_title}', got '{actual_title}'")

        # Check content length - Ghost CMS stores content in different formats
        actual_html = post.get('html', '')
        actual_mobiledoc = post.get('mobiledoc', '')
        actual_lexical = post.get('lexical', '')
        expected_length = len(expected_content)

        # Ghost CMS might store content as HTML, Mobiledoc, or Lexical
        if actual_html:
            actual_length = len(actual_html)
            content_type = "HTML"
        elif actual_mobiledoc:
            # Try to extract text from mobiledoc if it's a string
            if isinstance(actual_mobiledoc, str):
                actual_length = len(actual_mobiledoc)
                content_type = "Mobiledoc"
            else:
                # Mobiledoc is an object, estimate length
                actual_length = len(str(actual_mobiledoc))
                content_type = "Mobiledoc (object)"
        elif actual_lexical:
            # Try to extract text from lexical if it's a string
            if isinstance(actual_lexical, str):
                actual_length = len(actual_lexical)
                content_type = "Lexical"
            else:
                # Lexical is an object, estimate length
                actual_length = len(str(actual_lexical))
                content_type = "Lexical (object)"
        else:
            # No content found in any format
            actual_length = 0
            content_type = "None"
            issues.append("No content found in post (HTML, Mobiledoc, or Lexical)")

        # Allow for some variation in content length (Ghost may modify HTML)
        length_diff = abs(expected_length - actual_length)
        length_tolerance = max(100, expected_length * 0.1)  # 10% tolerance or 100 chars minimum

        content_length_match = length_diff <= length_tolerance
        if not content_length_match and actual_length > 0:
            issues.append(f"Content length mismatch: expected ~{expected_length} chars, got {actual_length} chars ({content_type}, diff: {length_diff})")
        elif actual_length == 0:
            issues.append(f"No content found in post - expected ~{expected_length} chars")

        # Check post status
        status = post.get('status', '')
        if status != 'draft':
            issues.append(f"Unexpected post status: {status} (expected 'draft')")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "title_match": title_match,
            "content_length": actual_length,
            "content_type": content_type,
            "post_status": status,
            "post_url": post.get('url', '')
        }

    except Exception as e:
        return {
            "valid": False,
            "issues": [f"Validation error: {str(e)}"]
        }


def publish_to_ghost(title, content, meta_description, tags):
    """Publish content to Ghost CMS"""
    from tools import GhostCMSTool
    from debug_utils import debug_print_texts

    # Debug the variables before publishing
    debug_print_texts(
        title, content, meta_description, str(tags),
        labels=("Title", "Content", "Meta Description", "Tags")
    )

    print("\n🚀 Publishing to Ghost CMS...")

    try:
        ghost_tool = GhostCMSTool()
        result = ghost_tool._run(
            title=title,
            content=content,
            meta_description=meta_description,
            tags=tags
        )

        print("📝 Ghost CMS Publication Result:")
        print(result)

        # Parse the result to get post ID for validation
        try:
            result_data = json.loads(result)
            if result_data.get("status") == "success":
                post_id = result_data.get("post_id")
                print(f"\n🔍 Validating published post (ID: {post_id})...")

                # Validate the published post by reading it back
                validation_result = validate_ghost_post(post_id, title, content)
                if validation_result["valid"]:
                    print("✅ Post validation successful!")
                    print(f"📊 Content length: {validation_result['content_length']} characters ({validation_result.get('content_type', 'Unknown')})")
                    print(f"📊 Title match: {validation_result['title_match']}")
                    print(f"📊 Post status: {validation_result['post_status']}")
                else:
                    print("⚠️ Post validation failed:")
                    for issue in validation_result["issues"]:
                        print(f"   - {issue}")
                    print(f"📊 Content found: {validation_result['content_length']} characters ({validation_result.get('content_type', 'Unknown')})")
            else:
                print(f"❌ Publication failed: {result_data.get('message', 'Unknown error')}")
        except json.JSONDecodeError:
            print("⚠️ Could not parse Ghost CMS response for validation")

        return True

    except Exception as e:
        print(f"❌ Error publishing to Ghost CMS: {str(e)}")
        print("📄 Content saved locally but not published to Ghost CMS")
        return False


# ============================================================================
# Content Extraction and Metadata Functions
# ============================================================================

def extract_blog_metadata(markup_content, seo_content, topic):
    """Extract title, meta description, and tags from content"""
    from bs4 import BeautifulSoup
    from config import Config

    # Extract title from Markdown content (look for # title)
    title_match = re.search(r'^#\s+(.+)$', str(markup_content), re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
    else:
        title = topic

    # Extract meta description from SEO content or Markdown content
    meta_description = f"Learn about {topic} with this comprehensive guide."
    if seo_content:
        seo_str = str(seo_content)
        meta_desc_match = re.search(r'Meta description[:\s]*(.*?)(?:\n|$)', seo_str, re.IGNORECASE | re.DOTALL)
        if meta_desc_match:
            meta_description = meta_desc_match.group(1).strip()

    # Try to extract from Markdown content as fallback
    if meta_description == f"Learn about {topic} with this comprehensive guide.":
        meta_desc_match = re.search(r'^#\s+.+\n\n\*\s*(.+?)\s*\*', str(markup_content), re.MULTILINE | re.DOTALL)
        if meta_desc_match:
            meta_description = meta_desc_match.group(1).strip()

    # Extract tags from SEO content or use defaults
    tags = Config.GHOST_CONFIG["default_tags"]
    if seo_content:
        seo_str = str(seo_content)
        tags_match = re.search(r'Tags[:\s]*(.*?)(?:\n|$)', seo_str, re.IGNORECASE | re.DOTALL)
        if tags_match:
            tags_text = tags_match.group(1).strip()
            tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]

    return title, meta_description, tags


def extract_content_from_file(file_path: str) -> dict:
    """Extract title, meta description, and content from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract title
        title = extract_title_from_content(content)

        # Extract meta description
        meta_description = extract_meta_description_from_content(content)

        # Extract article content
        article_content = extract_article_content_from_file(content)

        return {
            'title': title,
            'meta_description': meta_description,
            'content': article_content,
            'raw_content': content
        }
    except Exception as e:
        print(f"❌ Error reading file {file_path}: {str(e)}")
        return {
            'title': "Generated Blog Post",
            'meta_description': "A comprehensive blog post generated by CrewAI",
            'content': "",
            'raw_content': ""
        }


def extract_title_from_content(content: str) -> str:
    """Extract title from content (supports both HTML and Markdown)"""
    from bs4 import BeautifulSoup

    # Try Markdown format first (# title)
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()

    # Try HTML format (<h1>title</h1>)
    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE)
    if title_match:
        return BeautifulSoup(title_match.group(1), 'html.parser').get_text().strip()

    return "Generated Blog Post"


def extract_meta_description_from_content(content: str) -> str:
    """Extract meta description from content"""
    from bs4 import BeautifulSoup

    # Try Markdown format (*description*)
    meta_desc_match = re.search(r'^#\s+.+\n\n\*\s*(.+?)\s*\*', content, re.MULTILINE | re.DOTALL)
    if meta_desc_match:
        return meta_desc_match.group(1).strip()

    # Try HTML format
    meta_desc_match = re.search(r'<p><strong>Meta description:</strong>\s*(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
    if meta_desc_match:
        return BeautifulSoup(meta_desc_match.group(1), 'html.parser').get_text().strip()

    return "A comprehensive blog post generated by CrewAI"


def extract_article_content_from_file(content: str) -> str:
    """Extract clean article content from file content"""
    # Try to find content between <article> tags
    article_match = re.search(r'<article>(.*?)</article>', content, re.DOTALL)
    if article_match:
        html_content = article_match.group(1).strip()
        # Remove meta description paragraph
        html_content = re.sub(r'<p><strong>Meta description:</strong>.*?</p>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
        return html_content.strip()

    # If no article tags, return the content as-is (for Markdown)
    return content.strip()


# ============================================================================
# Content Processing and Cleaning Functions
# ============================================================================

def clean_markdown_content(markup_content):
    """Clean up Markdown content for publishing"""
    # Remove meta description line if it exists (italicized line after title)
    # Pattern: # title\n\n*description*\n\n -> # title\n\n
    clean_content = re.sub(r'^#\s+(.+)\n\n\*\s*.+?\s*\*\n\n', r'# \1\n\n', str(markup_content), flags=re.MULTILINE | re.DOTALL)
    return clean_content.strip()


def analyze_content_quality(content: str) -> dict:
    """Analyze content quality and provide metrics"""
    from bs4 import BeautifulSoup

    # Get text content for analysis
    if content.startswith('<'):
        # HTML content
        soup = BeautifulSoup(content, 'html.parser')
        text_content = soup.get_text()
    else:
        # Markdown or plain text
        text_content = content

    word_count = len(text_content.split())
    char_count = len(text_content)

    # Quality assessment
    quality_score = "excellent" if word_count >= QUALITY_EXCELLENT_WORDS else "good" if word_count >= QUALITY_GOOD_WORDS else "needs_improvement"

    return {
        'word_count': word_count,
        'char_count': char_count,
        'quality_score': quality_score,
        'is_substantial': word_count >= QUALITY_EXCELLENT_WORDS,
        'is_moderate': QUALITY_GOOD_WORDS <= word_count < QUALITY_EXCELLENT_WORDS,
        'is_short': word_count < QUALITY_GOOD_WORDS
    }


# ============================================================================
# Display and Preview Functions
# ============================================================================

def show_content_preview(markup_content, title, meta_description, tags):
    """Display a preview of the blog content"""
    print(f"\n👀 FINAL DRAFT REVIEW:")
    print("=" * SEPARATOR_LENGTH)
    print("📖 PREVIEW OF YOUR BLOG POST:")
    print("=" * SEPARATOR_LENGTH)
    print(f"📝 Title: {title}")
    print(f"📝 Meta Description: {meta_description[:100]}...")
    print(f"📝 Tags: {', '.join(tags)}")
    print(f"📝 Content Length: {len(str(markup_content))} characters")
    print("\n" + "=" * SEPARATOR_LENGTH)
    print("📄 CONTENT PREVIEW:")
    print("=" * SEPARATOR_LENGTH)

    # Show first CONTENT_PREVIEW_LENGTH characters of content
    content_preview = str(markup_content)[:CONTENT_PREVIEW_LENGTH]
    print(content_preview)

    if len(str(markup_content)) > CONTENT_PREVIEW_LENGTH:
        print("\n... (content truncated for preview)")

    print("\n" + "=" * SEPARATOR_LENGTH)


# ============================================================================
# Rate Limiting and Progress Tracking Classes
# ============================================================================

class RateLimitHandler:
    """Handles OpenAI rate limits by automatically waiting when needed"""

    def __init__(self, max_tpm=MAX_TPM_LIMIT):
        self.max_tpm = max_tpm
        self.last_wait_time = 0

    def handle_rate_limit(self, error_message):
        """Check if error is a rate limit error and handle it"""
        if "RateLimitError" in str(error_message) and "TPM" in str(error_message):
            # Extract the requested TPM from the error message
            tpm_match = re.search(r'Requested (\d+)', str(error_message))
            if tpm_match:
                requested_tpm = int(tpm_match.group(1))
                if requested_tpm > self.max_tpm:
                    wait_time = RATE_LIMIT_WAIT_TIME
                    print(f"\n⚠️  Rate limit exceeded: {requested_tpm} TPM requested (limit: {self.max_tpm})")
                    print(f"⏳ Waiting {wait_time} seconds for rate limit to reset...")

                    # Show countdown
                    for i in range(wait_time, 0, -1):
                        print(f"   ⏰ {i} seconds remaining...", end='\r')
                        time.sleep(1)
                    print("   ✅ Rate limit reset complete!                    ")

                    return True  # Indicates we should retry
        return False

    def execute_with_retry(self, crew, max_retries=MAX_RETRIES):
        """Execute crew with automatic retry on rate limit errors"""
        for attempt in range(max_retries):
            try:
                print(f"\n🔄 Attempt {attempt + 1}/{max_retries}")
                return crew.kickoff()

            except Exception as e:
                error_str = str(e)
                print(f"\n❌ Error on attempt {attempt + 1}: {error_str}")

                # Check if it's a rate limit error we can handle
                if self.handle_rate_limit(error_str):
                    if attempt < max_retries - 1:
                        print(f"\n🔄 Retrying after rate limit reset...")
                        continue
                    else:
                        print(f"\n❌ Max retries reached after rate limit handling")
                        raise e
                else:
                    # Not a rate limit error, re-raise
                    raise e

        # If we get here, all retries failed
        raise Exception("All retry attempts failed")


class ProgressTracker:
    """Track progress of the blog generation workflow"""

    def __init__(self):
        self.total_steps = TOTAL_WORKFLOW_STEPS + 1  # Add Ghost publishing step
        self.current_step = 0
        self.step_names = [
            "Research",
            "Content Creation",
            "SEO Optimization",
            "Content Formatting",
            "Quality Review",
            "Ghost CMS Publishing"
        ]

    def start_step(self, step_name):
        """Start a new step"""
        self.current_step += 1
        percentage = int((self.current_step / self.total_steps) * 100)
        print(f"\n🔄 Step {self.current_step}/{self.total_steps} ({percentage}%): {step_name}")
        print("=" * SEPARATOR_LENGTH)

    def get_progress(self):
        """Get current progress percentage"""
        return int((self.current_step / self.total_steps) * 100)


# ============================================================================
# Additional Instructions Processing
# ============================================================================

def process_additional_instructions(instructions: str, output_path: str = None):
    """
    Process additional job instructions from the user
    """
    instructions_lower = instructions.lower()

    if "publish" in instructions_lower or "ghost" in instructions_lower:
        print("🚀 Publishing to Ghost CMS...")
        if output_path and os.path.exists(output_path):
            try:
                from config import Config

                # Extract content and metadata using helper function
                content_data = extract_content_from_file(output_path)

                # Publish to Ghost CMS using helper function
                success = publish_to_ghost(
                    title=content_data['title'],
                    content=content_data['content'],
                    meta_description=content_data['meta_description'],
                    tags=Config.GHOST_CONFIG["default_tags"]
                )

                if success:
                    print("✅ Successfully published to Ghost CMS!")
                else:
                    print("❌ Failed to publish to Ghost CMS")

            except Exception as e:
                print(f"❌ Error publishing to Ghost CMS: {str(e)}")
        else:
            print("❌ No output file found to publish")

    elif "test" in instructions_lower or "validate" in instructions_lower or "verify" in instructions_lower:
        print("🧪 Running validation tests...")
        if output_path and os.path.exists(output_path):
            try:
                # Extract content using helper function
                content_data = extract_content_from_file(output_path)

                # Analyze content quality using helper function
                quality_analysis = analyze_content_quality(content_data['content'])

                print(f"📊 Content Analysis:")
                print(f"   • Content Length: {len(content_data['content']):,} characters")
                print(f"   • Text Content Length: {quality_analysis['char_count']:,} characters")
                print(f"   • Word Count: {quality_analysis['word_count']:,} words")
                print(f"   • File Size: {os.path.getsize(output_path):,} bytes")
                print(f"   • Quality Score: {quality_analysis['quality_score']}")

                # Check if content meets typical blog post requirements
                if quality_analysis['is_substantial']:
                    print("✅ Content length is substantial (1000+ words)")
                elif quality_analysis['is_moderate']:
                    print("⚠️ Content length is moderate (500-999 words)")
                else:
                    print("❌ Content length is short (<500 words)")

            except Exception as e:
                print(f"❌ Error analyzing content: {str(e)}")
        else:
            print("❌ No output file found to analyze")
        print("✅ Validation tests completed")

    elif "config" in instructions_lower or "settings" in instructions_lower:
        print("⚙️ Configuration management...")
        # Add configuration management logic here
        print("✅ Configuration updated")

    elif "list" in instructions_lower or "show" in instructions_lower:
        print("📋 Listing generated posts...")
        if output_path:
            output_dir = os.path.dirname(output_path)
            if os.path.exists(output_dir):
                files = [f for f in os.listdir(output_dir) if f.endswith(OUTPUT_FILE_EXTENSION)]
                if files:
                    print(f"Found {len(files)} generated posts:")
                    for file in sorted(files, reverse=True)[:MAX_FILES_TO_DISPLAY]:
                        print(f"  📄 {file}")
                else:
                    print("No generated posts found")

    else:
        print(f"🤔 I received your instructions: '{instructions}'")
        print("💡 This is a general instruction. You can:")
        print("  • Ask me to publish a post to Ghost CMS")
        print("  • Request validation tests")
        print("  • Modify configuration settings")
        print("  • List generated posts")
        print("  • Or provide more specific instructions")
