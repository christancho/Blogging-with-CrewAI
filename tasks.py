from crewai import Task
from agents import BlogAgents

class BlogTasks:
    """Define all tasks for the blog generation workflow"""
    
    def __init__(self):
        self.agents = BlogAgents()
    
    def research_task(self, topic: str):
        return Task(
            description=f"""Research "{topic}" using Brave Search tool. Execute 5-7 searches covering: overview, key concepts, recent trends, best practices, challenges/solutions, use cases, and future outlook.

IMPORTANT: For each search result, note the SOURCE URLs of authoritative websites, official documentation, research papers, and reputable articles. Collect 5-10 credible source URLs that can be used as references in the article.

Compile findings into a structured report including:
- Key findings and insights
- Source URLs with titles (format: [Title](URL))
- Date/recency of information
- Credibility assessment of sources""",
            agent=self.agents.research_agent(),
            expected_output="Comprehensive research report with key findings, sources with URLs, and credibility notes"
        )
    
    def content_creation_task(self, topic: str):
        return Task(
            description=f"""Write a COMPLETE 3500-word article on "{topic}". CRITICAL: Write FULL PARAGRAPHS for each section, NOT just titles or one-liners.

Structure with FULL CONTENT for each section:
1. Introduction (400-500 words): Write 4-5 full paragraphs with hook, context, overview, and importance
2. Section 1 (600-700 words): Write 6-7 full paragraphs on foundational concepts with explanations and examples
3. Section 2 (600-700 words): Write 6-7 full paragraphs diving deeper with methodologies and practical examples
4. Section 3 (600-700 words): Write 6-7 full paragraphs on advanced concepts, best practices, and use cases
5. Section 4 (500-600 words): Write 5-6 full paragraphs on future trends, challenges, and actionable insights
6. Conclusion (300-400 words): Write 3-4 full paragraphs summarizing takeaways and next steps

CRITICAL: Each section MUST contain multiple detailed paragraphs. DO NOT write just section titles with one sentence. Write the actual article content with full paragraphs, explanations, examples, and details.

MANDATORY INLINE HYPERLINKS - YOU MUST INCLUDE THESE:
YOU MUST add 10-15 inline hyperlinks DIRECTLY WITHIN the article text. This is NOT optional.

RULES FOR INLINE HYPERLINKS:
1. USE the actual URLs from the research task's findings - review the research output and extract the URLs
2. Add links NATURALLY in sentences where you mention tools, concepts, frameworks, companies, or research
3. DO NOT save all links for the References section - they MUST appear inline in the text
4. Every major concept, tool, or framework mentioned should link to its official site or documentation

EXAMPLES OF INLINE HYPERLINKS (you must add similar links in your article):
- "According to [OpenAI's documentation](https://platform.openai.com/docs), the API..."
- "Tools like [Docker](https://docker.com) and [Kubernetes](https://kubernetes.io) enable..."
- "Research from [MIT](https://mit.edu/research) shows that..."
- "The [Python programming language](https://python.org) offers..."

WHERE TO ADD INLINE LINKS:
- Introduction: 2-3 links to key concepts or background sources
- Body sections: 2-3 links per section to relevant tools, documentation, or research
- Throughout the text when mentioning specific technologies, frameworks, or studies

FORMAT: All inline links must use Markdown format: [link text](https://url.com)

REFERENCES SECTION:
- Add a "## References" section at the very end
- List all sources cited in the article
- Format: numbered list with titles and URLs
- Include 5-10 credible sources

VERIFICATION: Before finishing, count your inline hyperlinks. You must have at least 10 links embedded in the article text.""",
            agent=self.agents.content_writer_agent(),
            expected_output="Complete 3500-word article with ALL sections containing multiple full paragraphs, AT LEAST 10 inline hyperlinks throughout the text, and a References section"
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
            description=f"""Review the article on "{topic}" for accuracy, structure, clarity, SEO, and formatting. After review, return the COMPLETE ARTICLE with all sections and full paragraphs.

MANDATORY QUALITY CHECKS:
1. Verify that the article contains AT LEAST 10 inline hyperlinks in the text (not just in References section)
2. If inline hyperlinks are missing, ADD THEM NOW - use the research URLs or find appropriate official documentation/sources
3. Ensure hyperlinks are distributed throughout the article (introduction, body sections, conclusion)
4. Verify all links use proper Markdown format: [link text](https://url.com)
5. Check that links are relevant and add value (link to official docs, research, authoritative sources)

INLINE HYPERLINK EXAMPLES YOU SHOULD ADD IF MISSING:
- Link technology names to their official websites
- Link research findings to original sources
- Link tools/frameworks to their documentation
- Link companies/organizations to their main sites

CRITICAL: Your output MUST be the entire article content (3500+ words with all sections fully written), NOT a review report or summary. Return the actual blog post content that will be published with all inline hyperlinks included.""",
            agent=self.agents.quality_reviewer_agent(),
            expected_output="Complete article with all sections, full paragraphs, and AT LEAST 10 inline hyperlinks throughout the text (NOT a review report)"
        )
    
    def ghost_publication_task(self, topic: str):
        return Task(
            description=f"""Publish "{topic}" article to Ghost CMS using the Ghost CMS Publisher tool.

CRITICAL - You MUST format the input as a JSON string with these keys:
1. Extract the article TITLE from the content (H1 heading or first line)
2. Extract the FULL CONTENT (entire article with all paragraphs and formatting)
3. Extract the META DESCRIPTION from SEO optimization
4. Extract TAGS from SEO optimization (as array)

Format your tool input as JSON like this:
{{
    "title": "Article Title Here",
    "content": "FULL ARTICLE CONTENT HERE with all sections and paragraphs",
    "meta_description": "SEO description",
    "tags": ["tag1", "tag2"]
}}

IMPORTANT: The 'content' field must contain the COMPLETE article text, not just the title. Include all sections, paragraphs, and formatting.

Then call the Ghost CMS Publisher tool with this JSON string. Report success with draft URL or error details.""",
            agent=self.agents.ghost_publisher_agent(),
            expected_output="Ghost CMS publication result with draft URL or error"
        )
