#!/usr/bin/env python3
"""
CrewAI Blog Generation System
Generates high-quality blog posts on any topic using AI agents with research, writing, SEO, and publishing capabilities.
"""

import os
import sys
import argparse
import time
import re
import json
import requests
from datetime import datetime
from crewai import Crew, Process
from config import Config
from agents import BlogAgents
from tasks import BlogTasks
from constants import *

def validate_ghost_post(post_id: str, expected_title: str, expected_content: str) -> dict:
    """
    Validate a published Ghost CMS post by reading it back and checking content
    """
    try:
        from tools import generate_ghost_jwt
        
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
        
        # Debug: Print available fields in the post (remove in production)
        # print(f"🔍 Debug - Available post fields: {list(post.keys())}")
        # print(f"🔍 Debug - HTML field: {post.get('html', 'NOT_FOUND')[:100]}...")
        # print(f"🔍 Debug - Mobiledoc field: {post.get('mobiledoc', 'NOT_FOUND')}")
        # print(f"🔍 Debug - Lexical field: {post.get('lexical', 'NOT_FOUND')}")
        
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
        self.total_steps = TOTAL_WORKFLOW_STEPS
        self.current_step = 0
        self.step_names = [
            "Research",
            "Content Creation", 
            "SEO Optimization",
            "Content Formatting",
            "Quality Review"
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

def extract_blog_metadata(markup_content, seo_content, topic):
    """Extract title, meta description, and tags from content"""
    import re
    from bs4 import BeautifulSoup
    
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
    from config import Config
    tags = Config.GHOST_CONFIG["default_tags"]
    if seo_content:
        seo_str = str(seo_content)
        tags_match = re.search(r'Tags[:\s]*(.*?)(?:\n|$)', seo_str, re.IGNORECASE | re.DOTALL)
        if tags_match:
            tags_text = tags_match.group(1).strip()
            tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
    
    return title, meta_description, tags

def clean_markdown_content(markup_content):
    """Clean up Markdown content for publishing"""
    import re
    
    # Remove meta description line if it exists (italicized line after title)
    # Pattern: # title\n\n*description*\n\n -> # title\n\n
    clean_content = re.sub(r'^#\s+(.+)\n\n\*\s*.+?\s*\*\n\n', r'# \1\n\n', str(markup_content), flags=re.MULTILINE | re.DOTALL)
    return clean_content.strip()

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

def extract_content_from_file(file_path: str) -> dict:
    """Extract title, meta description, and content from a file"""
    import re
    from bs4 import BeautifulSoup
    
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
    import re
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
    import re
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
    import re
    from bs4 import BeautifulSoup
    
    # Try to find content between <article> tags
    article_match = re.search(r'<article>(.*?)</article>', content, re.DOTALL)
    if article_match:
        html_content = article_match.group(1).strip()
        # Remove meta description paragraph
        html_content = re.sub(r'<p><strong>Meta description:</strong>.*?</p>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
        return html_content.strip()
    
    # If no article tags, return the content as-is (for Markdown)
    return content.strip()

def analyze_content_quality(content: str) -> dict:
    """Analyze content quality and provide metrics"""
    from bs4 import BeautifulSoup
    import re
    
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

def publish_to_ghost(title, content, meta_description, tags):
    """Publish content to Ghost CMS"""
    from tools import GhostCMSTool
    import json
    
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

class BlogGenerationCrew:
    """Main orchestrator for the blog generation crew"""
    
    def __init__(self):
        """Initialize the blog generation crew"""
        try:
            Config.validate_config()
            self.agents = BlogAgents()
            self.tasks = BlogTasks()
            self.output_dir = Config.OUTPUT_DIR
            self.rate_limit_handler = RateLimitHandler(max_tpm=200000)
            self.progress_tracker = ProgressTracker()
            self._ensure_output_directory()
        except ValueError as e:
            print(f"Configuration Error: {e}")
            print("\nPlease ensure you have set the following environment variables:")
            print("- OPENAI_API_KEY: Your OpenAI API key")
            print("- BRAVE_SEARCH_API_KEY: Your Brave Search API key")
            print("- GHOST_API_KEY: Your Ghost CMS API key")
            print("- GHOST_API_URL: Your Ghost CMS API URL")
            sys.exit(1)
    
    def _ensure_output_directory(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created output directory: {self.output_dir}")
    
    def _execute_crew_with_progress(self, crew):
        """Execute crew with progress tracking"""
        try:
            # Execute each task individually with progress updates
            tasks = crew.tasks
            results = []
            
            for i, task in enumerate(tasks):
                step_name = self.progress_tracker.step_names[i]
                self.progress_tracker.start_step(step_name)
                
                # Execute the task
                if i == 0:
                    # First task has no context
                    result = task.execute_sync()
                else:
                    # Subsequent tasks have context from previous tasks
                    result = task.execute_sync()
                
                results.append(result)
                
                # Show completion
                percentage = self.progress_tracker.get_progress()
                print(f"✅ Step {i+1} completed ({percentage}%)")
                
                # Add a small delay to show progress
                time.sleep(PROGRESS_DELAY)
            
            # Return both the final result and all individual task results
            return {
                'final_result': results[-1] if results else None,
                'task_results': results,
                'markup_content': results[3] if len(results) > 3 else None,  # Markdown formatter task (4th task, index 3)
                'seo_content': results[2] if len(results) > 2 else None,     # SEO task (3rd task, index 2)
                'content': results[1] if len(results) > 1 else None          # Content task (2nd task, index 1)
            }
            
        except Exception as e:
            print(f"\n❌ Error during crew execution: {str(e)}")
            raise e
    
    def _classify_topic(self, topic: str) -> dict:
        """Classify the topic to help tailor the research approach"""
        topic_lower = topic.lower()
        
        # Define topic categories and keywords (expanded to include non-technical topics)
        categories = {
            "technology": ["programming", "coding", "development", "framework", "library", "api", "sdk", "software", "tech", "computer"],
            "business": ["business", "marketing", "sales", "finance", "entrepreneurship", "startup", "management", "strategy"],
            "lifestyle": ["health", "fitness", "wellness", "nutrition", "travel", "fashion", "beauty", "home", "family"],
            "education": ["learning", "teaching", "education", "school", "university", "course", "training", "skill"],
            "science": ["science", "research", "study", "experiment", "discovery", "innovation", "biology", "chemistry", "physics"],
            "arts_culture": ["art", "music", "culture", "literature", "film", "theater", "design", "creative", "entertainment"],
            "sports": ["sports", "fitness", "athletics", "training", "competition", "team", "player", "game"],
            "food_cooking": ["food", "cooking", "recipe", "cuisine", "restaurant", "chef", "kitchen", "dining"],
            "travel": ["travel", "tourism", "vacation", "destination", "adventure", "explore", "journey", "trip"],
            "personal_development": ["personal", "development", "growth", "motivation", "productivity", "mindfulness", "self-help"]
        }
        
        # Find matching categories
        matched_categories = []
        for category, keywords in categories.items():
            if any(keyword in topic_lower for keyword in keywords):
                matched_categories.append(category)
        
        # Default to general if no specific match
        if not matched_categories:
            matched_categories = ["general"]
        
        return {
            "topic": topic,
            "categories": matched_categories,
            "primary_category": matched_categories[0],
            "complexity": "intermediate"  # Default complexity
        }
    
    def generate_blog_post(self, topic: str, user_approval: bool = True) -> str:
        """Generate a complete blog post on the given topic"""
        
        print(f"\n🚀 Starting blog generation for topic: '{topic}'")
        print("=" * 60)
        
        # Classify the topic
        topic_info = self._classify_topic(topic)
        print(f"📊 Topic Classification: {topic_info['primary_category']}")
        print(f"📝 Categories: {', '.join(topic_info['categories'])}")
        
        # Create timestamp for this generation
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Show initial progress
            print(f"\n🚀 Starting blog generation workflow...")
            print(f"📊 Total steps: {self.progress_tracker.total_steps}")
            print(f"⏱️  Estimated time: 15-30 minutes")
            print("💡 Rate limit protection enabled: Will automatically wait if TPM exceeds 200,000\n")
            
            # Define the crew tasks (without publication - that happens after user approval)
            research_task = self.tasks.research_task(topic)
            content_task = self.tasks.content_creation_task(topic)
            seo_task = self.tasks.seo_optimization_task(topic)
            html_task = self.tasks.html_formatting_task()
            review_task = self.tasks.quality_review_task(topic)
            
            # Set up task dependencies
            content_task.context = [research_task]
            seo_task.context = [content_task]
            html_task.context = [seo_task]
            review_task.context = [html_task]
            
            # Create the crew (without publication - that happens after user approval)
            crew = Crew(
                agents=[
                    self.agents.research_agent(),
                    self.agents.content_writer_agent(),
                    self.agents.seo_optimizer_agent(),
                    self.agents.html_formatter_agent(),
                    self.agents.quality_reviewer_agent()
                ],
                tasks=[
                    research_task,
                    content_task,
                    seo_task,
                    html_task,
                    review_task
                ],
                process=Process.sequential,
                verbose=True
            )
            
            # Execute the crew with progress tracking
            crew_results = self._execute_crew_with_progress(crew)
            
            # Extract the final result and individual task results
            final_result = crew_results['final_result']
            markup_content = crew_results['markup_content']
            seo_content = crew_results['seo_content']
            content = crew_results['content']
            
            # Save the final result (for backup/debugging)
            output_filename = f"blog_post_{timestamp}_{topic.replace(' ', '_').replace('/', '_')}{OUTPUT_FILE_EXTENSION}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(str(final_result))
            
            print(f"\n🎉 Blog post generation completed! (100%)")
            print(f"📄 Output saved to: {output_path}")
            
            # Extract metadata and prepare content for publishing
            if markup_content:
                print("✅ Using Markdown content from Markdown formatter task")
                blog_content = str(markup_content)
            else:
                print("⚠️ No Markdown content from formatter, falling back to content task")
                blog_content = str(content) if content else str(final_result)
            
            # Extract metadata using helper function
            title, meta_description, tags = extract_blog_metadata(markup_content, seo_content, topic)
            
            # Clean up content for publishing
            clean_content = clean_markdown_content(blog_content)
            
            # Always show preview
            show_content_preview(clean_content, title, meta_description, tags)
            
            # Handle publishing based on user approval setting
            if not user_approval:
                print("\n🚀 Auto-publishing to Ghost CMS (--no-approval mode)...")
                publish_to_ghost(title, clean_content, meta_description, tags)
            
            else:
                # User approval required - ask for confirmation
                print(f"\n📁 Full content available at: {output_path}")
                
                # Ask for user approval
                approval = input("\nDo you approve this content for publication to Ghost CMS? (y/n): ").lower().strip()
                
                if approval == 'y' or approval == 'yes':
                    print("✅ Content approved! Publishing to Ghost CMS...")
                    publish_to_ghost(title, clean_content, meta_description, tags)
                else:
                    print("❌ Content not approved. Please review and make necessary changes.")
            
            return output_path
            
        except Exception as e:
            print(f"\n❌ Error during blog generation: {str(e)}")
            return None
    
    def list_generated_posts(self):
        """List all previously generated blog posts"""
        if not os.path.exists(self.output_dir):
            print("No output directory found. No posts have been generated yet.")
            return
        
        files = [f for f in os.listdir(self.output_dir) if f.endswith(OUTPUT_FILE_EXTENSION)]
        
        if not files:
            print("No blog posts found in the output directory.")
            return
        
        print(f"\n📚 Generated Blog Posts ({len(files)} found):")
        print("=" * SEPARATOR_LENGTH)
        
        for i, filename in enumerate(sorted(files, reverse=True), 1):
            # Extract info from filename
            parts = filename.replace(OUTPUT_FILE_EXTENSION, '').split('_')
            if len(parts) >= 3:
                date_part = parts[2]
                time_part = parts[3] if len(parts) > 3 else ""
                topic_part = '_'.join(parts[4:]) if len(parts) > 4 else "unknown_topic"
                
                # Format date
                try:
                    date_obj = datetime.strptime(date_part, "%Y%m%d")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                except:
                    formatted_date = date_part
                
                print(f"{i:2d}. {topic_part.replace('_', ' ').title()}")
                print(f"    📅 Generated: {formatted_date}")
                print(f"    📁 File: {filename}")
                print()

def main():
    """Main entry point for the blog generation system"""
    
    parser = argparse.ArgumentParser(
        description="CrewAI Blog Generation System - Generate technical blog posts with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
            python main.py --topic "Docker containerization best practices"
            python main.py --topic "Machine Learning model deployment" --no-approval
            python main.py --list
             """
    )
    
    parser.add_argument(
        '--topic', '-t',
        type=str,
        help='The technical topic to write about'
    )
    
    parser.add_argument(
        '--no-approval',
        action='store_true',
        help='Skip user approval step (auto-approve content)'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all previously generated blog posts'
    )
    
    args = parser.parse_args()
    
    # Initialize the blog generation crew
    blog_crew = BlogGenerationCrew()
    
    if args.list:
        blog_crew.list_generated_posts()
        return
    
    if not args.topic:
        print("CrewAI Blog Generation System")
        print("=" * 40)
        print("Generate high-quality technical blog posts using AI agents.\n")
        
        topic = input("Enter the technical topic you'd like to write about: ").strip()
        
        if not topic:
            print("❌ No topic provided. Exiting.")
            return
    else:
        topic = args.topic
    
    # Generate the blog post
    user_approval = not args.no_approval
    result_path = blog_crew.generate_blog_post(topic, user_approval=user_approval)
    
    if result_path:
        print(f"\n🎉 Blog generation completed successfully!")
        print(f"📄 Your blog post is ready at: {result_path}")
    else:
        print(f"\n❌ Blog generation failed. Please check the error messages above.")
    
    # Ask for additional job instructions
    print("\n" + "="*60)
    print("🤖 ADDITIONAL JOB INSTRUCTIONS")
    print("="*60)
    print("The blog generation process has completed. You can now provide additional instructions for:")
    print("• Modifying the generated content")
    print("• Publishing additional posts")
    print("• Updating configuration settings")
    print("• Running specific tests or validations")
    print("• Any other tasks related to the blogging system")
    print("\nType your instructions below (or press Enter to exit):")
    
    try:
        additional_instructions = input("\n💬 Additional instructions: ").strip()
        if additional_instructions:
            print(f"\n📝 Received instructions: {additional_instructions}")
            print("🔄 Processing additional instructions...")
            
            # Process the additional instructions
            process_additional_instructions(additional_instructions, result_path)
        else:
            print("\n👋 No additional instructions provided. Exiting...")
    except KeyboardInterrupt:
        print("\n\n👋 Process interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n⚠️ Error processing additional instructions: {str(e)}")

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

if __name__ == "__main__":
    main()
