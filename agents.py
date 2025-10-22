from crewai import Agent
from tools import BraveSearchTool, SEOAnalysisTool, HTMLFormatterTool, GhostCMSTool, ContentAnalysisTool, TagExtractionTool

class BlogAgents:
    """Define all agents for the blog generation crew"""
    
    def research_agent(self):
        return Agent(
            role="Research Specialist",
            goal="Conduct comprehensive research to gather authoritative, current information",
            backstory="Expert researcher who gathers credible, up-to-date information from multiple sources and synthesizes it into structured insights for content creation.",
            tools=[BraveSearchTool()],
            verbose=True,
            allow_delegation=False,
            max_iter=15
        )
    
    def content_writer_agent(self):
        return Agent(
            role="Content Creator",
            goal="Create engaging, informative 3500-word articles with proper structure and clarity",
            backstory="Experienced writer who creates clear, well-structured articles with introduction, four main sections, and conclusion. Balances depth with readability for engaging content.",
            tools=[ContentAnalysisTool()],
            verbose=True,
            allow_delegation=False,
            max_iter=15
        )
    
    def seo_optimizer_agent(self):
        return Agent(
            role="SEO Specialist",
            goal="Optimize content for search engines while maintaining readability",
            backstory="SEO expert who optimizes keywords, meta tags, and content structure for maximum search visibility without sacrificing quality.",
            tools=[SEOAnalysisTool()],
            verbose=True,
            allow_delegation=False,
            max_iter=10
        )
    
    def html_formatter_agent(self):
        return Agent(
            role="Markdown Formatter",
            goal="Format content as clean Markdown suitable for Ghost CMS publication",
            backstory="Markdown formatting specialist who creates clean, Ghost CMS-compatible content with proper structure, accessibility, and web standards.",
            tools=[HTMLFormatterTool()],
            verbose=True,
            allow_delegation=False,
            max_iter=10
        )
    
    def quality_reviewer_agent(self):
        return Agent(
            role="Quality Reviewer",
            goal="Review content quality and return the final approved article",
            backstory="Senior editor who checks accuracy, structure, clarity, and SEO. CRITICAL: Return the FINAL APPROVED CONTENT ready for publication, not a review report.",
            tools=[ContentAnalysisTool(), SEOAnalysisTool()],
            verbose=True,
            allow_delegation=False,
            max_iter=10
        )
    
    def ghost_publisher_agent(self):
        return Agent(
            role="Ghost Publisher",
            goal="Publish content to Ghost CMS using the available tools",
            backstory="Publication manager who uses Ghost CMS Publisher tool to create drafts. CRITICAL: Actually call the tools with extracted content, title, meta description, and tags.",
            tools=[GhostCMSTool(), HTMLFormatterTool(), TagExtractionTool()],
            verbose=True,
            allow_delegation=False,
            max_iter=10
        )
