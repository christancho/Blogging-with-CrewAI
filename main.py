#!/usr/bin/env python3
"""
CrewAI Blog Generation System
Generates high-quality blog posts on any topic using AI agents with research, writing, SEO, and publishing capabilities.
"""

import os
import sys
import argparse
from datetime import datetime
from crewai import Crew, Process
from config import Config
from agents import BlogAgents
from tasks import BlogTasks
from constants import *
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
    process_additional_instructions
)

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
            # Execute the entire crew workflow
            print("\n🚀 Executing CrewAI workflow...")
            print("=" * SEPARATOR_LENGTH)
            
            # Use the rate limit handler to execute with retry logic
            result = self.rate_limit_handler.execute_with_retry(crew)
            
            # Extract individual task results from the crew execution
            # In CrewAI 0.5.0, we get the final result and can access task results
            task_results = []
            
            # Try to get individual task results if available
            if hasattr(crew, 'tasks') and crew.tasks:
                for i, task in enumerate(crew.tasks):
                    step_name = self.progress_tracker.step_names[i] if i < len(self.progress_tracker.step_names) else f"Task {i+1}"
                    print(f"\n✅ Step {i+1}/{len(crew.tasks)} ({step_name}) completed")
                    
                    # Try to get task result if available
                    if hasattr(task, 'output') and task.output:
                        task_results.append(task.output)
                    else:
                        # Fallback: use the final result for all tasks
                        task_results.append(result)
            
            # If we couldn't get individual results, use the final result
            if not task_results:
                task_results = [result] * len(crew.tasks) if hasattr(crew, 'tasks') else [result]
            
            # Update progress tracker
            self.progress_tracker.current_step = len(crew.tasks)
            percentage = self.progress_tracker.get_progress()
            print(f"\n🎉 All steps completed! ({percentage}%)")
            
            # Return both the final result and all individual task results
            return {
                'final_result': result,
                'task_results': task_results,
                'markup_content': task_results[3] if len(task_results) > 3 else None,  # Markdown formatter task (4th task, index 3)
                'seo_content': task_results[2] if len(task_results) > 2 else None,     # SEO task (3rd task, index 2)
                'content': task_results[1] if len(task_results) > 1 else None,         # Content task (2nd task, index 1)
                'ghost_result': task_results[5] if len(task_results) > 5 else None     # Ghost publishing task (6th task, index 5)
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
            
            # Define the crew tasks (including Ghost CMS publication)
            research_task = self.tasks.research_task(topic)
            content_task = self.tasks.content_creation_task(topic)
            seo_task = self.tasks.seo_optimization_task(topic)
            html_task = self.tasks.html_formatting_task()
            review_task = self.tasks.quality_review_task(topic)
            ghost_task = self.tasks.ghost_publication_task(topic)
            
            # Set up task dependencies
            content_task.context = [research_task]
            seo_task.context = [content_task]
            html_task.context = [seo_task]
            review_task.context = [html_task]
            ghost_task.context = [review_task]
            
            # Debug: Print task setup
            from debug_utils import debug_print_texts
            print("\n🔍 DEBUG: Task Dependencies Setup")
            print("="*50)
            print(f"Research Task: {research_task.description[:100]}...")
            print(f"Content Task Context: {len(content_task.context)} tasks")
            print(f"SEO Task Context: {len(seo_task.context)} tasks")
            print(f"HTML Task Context: {len(html_task.context)} tasks")
            print(f"Review Task Context: {len(review_task.context)} tasks")
            print(f"Ghost Task Context: {len(ghost_task.context)} tasks")
            
            # Create the crew (including Ghost CMS publication)
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
                    ghost_task
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
            ghost_result = crew_results['ghost_result']
            
            # Save the final result (for backup/debugging)
            output_filename = f"blog_post_{timestamp}_{topic.replace(' ', '_').replace('/', '_')}{OUTPUT_FILE_EXTENSION}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(str(final_result))
            
            print(f"\n🎉 Blog post generation completed! (100%)")
            print(f"📄 Output saved to: {output_path}")
            
            # Show Ghost CMS publishing result
            if ghost_result:
                print("\n📝 Ghost CMS Publishing Result:")
                print("=" * SEPARATOR_LENGTH)
                print(ghost_result)
                print("=" * SEPARATOR_LENGTH)
            else:
                print("\n⚠️ Ghost CMS publishing result not available")
            
            # Extract metadata and prepare content for preview
            if markup_content:
                print("✅ Using Markdown content from Markdown formatter task")
                blog_content = str(markup_content)
            else:
                print("⚠️ No Markdown content from formatter, falling back to content task")
                blog_content = str(content) if content else str(final_result)
            
            # Extract metadata using helper function
            title, meta_description, tags = extract_blog_metadata(markup_content, seo_content, topic)
            
            # Clean up content for preview
            clean_content = clean_markdown_content(blog_content)
            
            # Always show preview
            show_content_preview(clean_content, title, meta_description, tags)
            
            return output_path
            
        except Exception as e:
            print(f"\n❌ Error during blog generation: {str(e)}")
            return None
    
    def list_generated_posts(self):
        """List all previously generated blog posts with interactive menu"""
        if not os.path.exists(self.output_dir):
            print("No output directory found. No posts have been generated yet.")
            return
        
        files = [f for f in os.listdir(self.output_dir) if f.endswith(OUTPUT_FILE_EXTENSION)]
        
        if not files:
            print("No blog posts found in the output directory.")
            return
        
        while True:
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
            
            print("=" * SEPARATOR_LENGTH)
            print("Options:")
            print("1. View post details")
            print("2. Delete post")
            print("3. Exit")
            
            choice = input("\nSelect an option (1-3): ").strip()
            
            if choice == "1":
                self._view_post_menu(files)
            elif choice == "2":
                self._delete_post_menu(files)
                # Refresh files list after deletion
                files = [f for f in os.listdir(self.output_dir) if f.endswith(OUTPUT_FILE_EXTENSION)]
                if not files:
                    print("No more posts available.")
                    break
            elif choice == "3":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option. Please select 1, 2, or 3.")
    
    def _view_post_menu(self, files):
        """Show post view menu"""
        while True:
            try:
                post_num = input(f"\nEnter post number to view (1-{len(files)}): ").strip()
                post_index = int(post_num) - 1
                
                if 0 <= post_index < len(files):
                    filename = sorted(files, reverse=True)[post_index]
                    self._view_post_details(filename)
                    break
                else:
                    print(f"❌ Please enter a number between 1 and {len(files)}")
            except ValueError:
                print("❌ Please enter a valid number")
    
    def _view_post_details(self, filename):
        """View post details and show action menu"""
        file_path = os.path.join(self.output_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {filename}")
            return
        
        print(f"\n📄 Post Details: {filename}")
        print("=" * SEPARATOR_LENGTH)
        
        try:
            from config import Config
            # Extract content and metadata
            content_data = extract_content_from_file(file_path)
            
            # Show preview
            show_content_preview(
                content_data['content'],
                content_data['title'],
                content_data['meta_description'],
                Config.GHOST_CONFIG["default_tags"]
            )
            
            # Show action menu
            while True:
                print("\n" + "=" * SEPARATOR_LENGTH)
                print("Actions:")
                print("1. Post to Ghost CMS")
                print("2. Back to list")
                
                action = input("\nSelect an action (1-2): ").strip()
                
                if action == "1":
                    self._publish_post_to_ghost(filename, content_data)
                    break
                elif action == "2":
                    break
                else:
                    print("❌ Invalid option. Please select 1 or 2.")
                    
        except Exception as e:
            print(f"❌ Error viewing post: {str(e)}")
    
    def _publish_post_to_ghost(self, filename, content_data):
        """Publish post to Ghost CMS"""
        print("🚀 Publishing to Ghost CMS...")
        
        try:
            from config import Config
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
    
    def _delete_post_menu(self, files):
        """Show post deletion menu"""
        while True:
            try:
                post_num = input(f"\nEnter post number to delete (1-{len(files)}): ").strip()
                post_index = int(post_num) - 1
                
                if 0 <= post_index < len(files):
                    filename = sorted(files, reverse=True)[post_index]
                    self._delete_post(filename)
                    break
                else:
                    print(f"❌ Please enter a number between 1 and {len(files)}")
            except ValueError:
                print("❌ Please enter a valid number")
    
    def _delete_post(self, filename):
        """Delete a post file"""
        file_path = os.path.join(self.output_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {filename}")
            return
        
        # Show confirmation
        print(f"\n⚠️  Are you sure you want to delete: {filename}")
        confirmation = input("Type 'DELETE' to confirm: ").strip()
        
        if confirmation == "DELETE":
            try:
                os.remove(file_path)
                print(f"✅ Successfully deleted: {filename}")
            except Exception as e:
                print(f"❌ Error deleting file: {str(e)}")
        else:
            print("❌ Deletion cancelled")

    def publish_existing_post(self, filename: str):
        """Publish an existing blog post to Ghost CMS"""
        # Ensure filename has the correct extension
        if not filename.endswith(OUTPUT_FILE_EXTENSION):
            filename += OUTPUT_FILE_EXTENSION
        
        file_path = os.path.join(self.output_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {filename}")
            print(f"💡 Use --list to see available posts")
            return
        
        print(f"📄 Publishing existing post: {filename}")
        print("=" * SEPARATOR_LENGTH)
        
        try:
            # Extract content and metadata using helper function
            content_data = extract_content_from_file(file_path)
            
            # Show preview
            from config import Config
            show_content_preview(
                content_data['content'],
                content_data['title'],
                content_data['meta_description'],
                Config.GHOST_CONFIG["default_tags"]
            )
            
            # Ask for confirmation
            confirmation = input("\n🤔 Do you want to publish this post to Ghost CMS? (y/n): ").lower().strip()
            
            if confirmation in ['y', 'yes']:
                print("🚀 Publishing to Ghost CMS...")
                
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
            else:
                print("❌ Publication cancelled")
                
        except Exception as e:
            print(f"❌ Error publishing post: {str(e)}")

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
            python main.py --publish "blog_post_20250104_114033_What_is_Context_Window_in_LLMs_models_and_why_should_we_care?.md"
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
    
    parser.add_argument(
        '--publish', '-p',
        type=str,
        help='Publish an existing blog post by filename (use --list to see available posts)'
    )
    
    args = parser.parse_args()
    
    # Initialize the blog generation crew
    blog_crew = BlogGenerationCrew()
    
    if args.list:
        blog_crew.list_generated_posts()
        return
    
    if args.publish:
        blog_crew.publish_existing_post(args.publish)
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

if __name__ == "__main__":
    main()
