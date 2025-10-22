from crewai import Task
from agents import BlogAgents

class BlogTasks:
    """Define all tasks for the blog generation workflow"""
    
    def __init__(self):
        self.agents = BlogAgents()
    
    def research_task(self, topic: str):
        return Task(
            description=f"""Research "{topic}" using Brave Search tool. Execute 5-7 searches covering: overview, key concepts, recent trends, best practices, challenges/solutions, use cases, and future outlook. Compile findings into a structured report.""",
            agent=self.agents.research_agent(),
            expected_output="Comprehensive research report with key findings and sources"
        )
    
    def content_creation_task(self, topic: str):
        return Task(
            description=f"""Write complete 3500-word article on "{topic}". Structure: Introduction (400-500 words), Section 1 (600-700 words on foundations), Section 2 (600-700 words on details), Section 3 (600-700 words on advanced concepts), Section 4 (500-600 words on future trends), Conclusion (300-400 words). Write ALL sections in full with examples and smooth transitions.""",
            agent=self.agents.content_writer_agent(),
            expected_output="Complete 3500-word article with all sections fully written"
        )
    
    def seo_optimization_task(self, topic: str):
        return Task(
            description=f"""Optimize article for SEO on "{topic}". Create SEO title (50-60 chars), meta description (150-160 chars), optimize keywords (1.5-2% density), ensure proper H1/H2/H3 hierarchy, generate 5-8 relevant tags. Maintain readability and accuracy.""",
            agent=self.agents.seo_optimizer_agent(),
            expected_output="SEO-optimized article with title, meta description, keywords, and tags"
        )
    
    def html_formatting_task(self):
        return Task(
            description="""Use Content Formatter tool to convert content to clean Ghost CMS-compatible Markdown. Proper heading hierarchy (# ## ###), format lists/code blocks correctly, include title as H1, meta description as italics. Ensure accessibility and semantic structure.""",
            agent=self.agents.html_formatter_agent(),
            expected_output="Clean Markdown formatted for Ghost CMS"
        )
    
    def quality_review_task(self, topic: str):
        return Task(
            description=f"""Review article on "{topic}" for accuracy, structure, clarity, SEO effectiveness, and formatting. CRITICAL: Return the FINAL APPROVED CONTENT (complete article), NOT a review report.""",
            agent=self.agents.quality_reviewer_agent(),
            expected_output="Final approved article ready for publication"
        )
    
    def ghost_publication_task(self, topic: str):
        return Task(
            description=f"""Publish "{topic}" article to Ghost CMS. Extract title, content, meta description, and tags from previous tasks. Call Ghost CMS Publisher tool with these parameters. Report success/failure with draft URL or error details.""",
            agent=self.agents.ghost_publisher_agent(),
            expected_output="Ghost CMS publication result with draft URL or error"
        )
