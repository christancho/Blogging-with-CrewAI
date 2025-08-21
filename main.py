#!/usr/bin/env python3
"""
CrewAI Blog Generation System
Generates technical blog posts using AI agents with research, writing, SEO, and publishing capabilities.
"""

import os
import sys
import argparse
import time
import re
from datetime import datetime
from crewai import Crew, Process
from config import Config
from agents import BlogAgents
from tasks import BlogTasks

class RateLimitHandler:
    """Handles OpenAI rate limits by automatically waiting when needed"""
    
    def __init__(self, max_tpm=10000):
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
                    wait_time = 60  # Wait 1 minute
                    print(f"\n⚠️  Rate limit exceeded: {requested_tpm} TPM requested (limit: {self.max_tpm})")
                    print(f"⏳ Waiting {wait_time} seconds for rate limit to reset...")
                    
                    # Show countdown
                    for i in range(wait_time, 0, -1):
                        print(f"   ⏰ {i} seconds remaining...", end='\r')
                        time.sleep(1)
                    print("   ✅ Rate limit reset complete!                    ")
                    
                    return True  # Indicates we should retry
        return False
    
    def execute_with_retry(self, crew, max_retries=3):
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

class BlogGenerationCrew:
    """Main orchestrator for the blog generation crew"""
    
    def __init__(self):
        """Initialize the blog generation crew"""
        try:
            Config.validate_config()
            self.agents = BlogAgents()
            self.tasks = BlogTasks()
            self.output_dir = Config.OUTPUT_DIR
            self.rate_limit_handler = RateLimitHandler(max_tpm=10000)
            self._ensure_output_directory()
        except ValueError as e:
            print(f"Configuration Error: {e}")
            print("\nPlease ensure you have set the following environment variables:")
            print("- OPENAI_API_KEY: Your OpenAI API key")
            print("- BRAVE_SEARCH_API_KEY: Your Brave Search API key")
            print("- GHOST_API_KEY: Your Ghost CMS API key (optional)")
            print("- GHOST_API_URL: Your Ghost CMS API URL (optional)")
            sys.exit(1)
    
    def _ensure_output_directory(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created output directory: {self.output_dir}")
    
    def _classify_topic(self, topic: str) -> dict:
        """Classify the topic to help tailor the research approach"""
        topic_lower = topic.lower()
        
        # Define topic categories and keywords
        categories = {
            "software_development": ["programming", "coding", "development", "framework", "library", "api", "sdk"],
            "cloud_computing": ["cloud", "aws", "azure", "gcp", "kubernetes", "docker", "serverless"],
            "cybersecurity": ["security", "encryption", "vulnerability", "threat", "firewall", "authentication"],
            "data_science": ["data", "analytics", "machine learning", "ai", "artificial intelligence", "ml"],
            "devops": ["devops", "ci/cd", "deployment", "automation", "infrastructure", "monitoring"],
            "web_development": ["web", "frontend", "backend", "javascript", "react", "vue", "angular"],
            "mobile_development": ["mobile", "ios", "android", "react native", "flutter", "app development"],
            "database": ["database", "sql", "nosql", "mongodb", "postgresql", "mysql", "redis"],
            "networking": ["network", "tcp", "http", "dns", "routing", "protocol", "bandwidth"],
            "emerging_tech": ["blockchain", "iot", "quantum", "ar", "vr", "5g", "edge computing"]
        }
        
        # Find matching categories
        matched_categories = []
        for category, keywords in categories.items():
            if any(keyword in topic_lower for keyword in keywords):
                matched_categories.append(category)
        
        # Default to general technical if no specific match
        if not matched_categories:
            matched_categories = ["general_technical"]
        
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
            # Define the crew tasks
            research_task = self.tasks.research_task(topic)
            content_task = self.tasks.content_creation_task(topic)
            seo_task = self.tasks.seo_optimization_task(topic)
            html_task = self.tasks.html_formatting_task()
            review_task = self.tasks.quality_review_task(topic)
            publish_task = self.tasks.ghost_publication_task(topic)
            
            # Set up task dependencies
            content_task.context = [research_task]
            seo_task.context = [content_task]
            html_task.context = [seo_task]
            review_task.context = [html_task]
            publish_task.context = [review_task]
            
            # Create the crew
            crew = Crew(
                agents=[
                    self.agents.research_agent(),
                    self.agents.content_writer_agent(),
                    self.agents.seo_optimizer_agent(),
                    self.agents.html_formatter_agent(),
                    self.agents.quality_reviewer_agent(),
                    self.agents.ghost_publisher_agent()
                ],
                tasks=[
                    research_task,
                    content_task,
                    seo_task,
                    html_task,
                    review_task,
                    publish_task
                ],
                process=Process.sequential,
                verbose=True
            )
            
            print(f"\n🔄 Executing crew workflow...")
            print("This may take several minutes as each agent completes their specialized tasks.")
            print("💡 Rate limit protection enabled: Will automatically wait if TPM exceeds 10,000\n")
            
            # Execute the crew with rate limit handling
            result = self.rate_limit_handler.execute_with_retry(crew)
            
            # Save the result
            output_filename = f"blog_post_{timestamp}_{topic.replace(' ', '_').replace('/', '_')}.html"
            output_path = os.path.join(self.output_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(str(result))
            
            print(f"\n✅ Blog post generation completed!")
            print(f"📄 Output saved to: {output_path}")
            
            if user_approval:
                print(f"\n👀 REVIEW REQUIRED:")
                print("The blog post has been generated and saved as a draft.")
                print("Please review the content before publishing to Ghost CMS.")
                print(f"File location: {output_path}")
                
                # Ask for user approval
                approval = input("\nDo you approve this content for publication? (y/n): ").lower().strip()
                
                if approval == 'y' or approval == 'yes':
                    print("✅ Content approved! Ready for Ghost CMS publication.")
                    print("Note: You may need to manually import the HTML into Ghost CMS.")
                else:
                    print("❌ Content not approved. Please review and make necessary changes.")
                    return output_path
            
            return output_path
            
        except Exception as e:
            print(f"\n❌ Error during blog generation: {str(e)}")
            return None
    
    def list_generated_posts(self):
        """List all previously generated blog posts"""
        if not os.path.exists(self.output_dir):
            print("No output directory found. No posts have been generated yet.")
            return
        
        files = [f for f in os.listdir(self.output_dir) if f.endswith('.html')]
        
        if not files:
            print("No blog posts found in the output directory.")
            return
        
        print(f"\n📚 Generated Blog Posts ({len(files)} found):")
        print("=" * 50)
        
        for i, filename in enumerate(sorted(files, reverse=True), 1):
            # Extract info from filename
            parts = filename.replace('.html', '').split('_')
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

if __name__ == "__main__":
    main()
