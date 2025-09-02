from crewai import Task
from agents import BlogAgents

class BlogTasks:
    """Define all tasks for the blog generation workflow"""
    
    def __init__(self):
        self.agents = BlogAgents()
    
    def research_task(self, topic: str):
        return Task(
            description=f"""Conduct comprehensive research on the topic: "{topic}"
            
            Your research should include:
            1. Current state and overview of the topic
            2. Key concepts, technologies, and terminology
            3. Recent developments and trends (within the last year)
            4. Best practices and industry standards
            5. Common challenges and solutions
            6. Real-world applications and use cases
            7. Future outlook and emerging trends
            
            Use multiple search queries to gather diverse perspectives and ensure comprehensive coverage.
            Focus on authoritative sources like official documentation, reputable tech blogs, research papers, and industry publications.
            
            Compile your findings into a structured research report that will serve as the foundation for creating a 3500-word article.""",
            agent=self.agents.research_agent(),
            expected_output="A comprehensive research report with key findings, sources, and structured information ready for content creation"
        )
    
    def content_creation_task(self, topic: str):
        return Task(
            description=f"""Create a comprehensive 3500-word article on "{topic}" using the research provided.
            
            Structure the article as follows:
            1. **Introduction** (400-500 words)
               - Hook the reader with an engaging opening
               - Provide context and background
               - Clearly state what the article will cover
               - Explain why this topic is important/relevant
            
            2. **Section 1** (600-700 words)
               - Cover the foundational concepts
               - Explain key terminology and basic principles
               - Provide necessary background information
            
            3. **Section 2** (600-700 words)
               - Dive deeper into details and concepts
               - Discuss approaches or methodologies
               - Include practical examples where appropriate
            
            4. **Section 3** (600-700 words)
               - Explore advanced concepts or applications
               - Discuss best practices and common pitfalls
               - Share real-world use cases or case studies
            
            5. **Section 4** (500-600 words)
               - Cover future trends and developments
               - Discuss challenges and opportunities
               - Provide actionable insights for readers
            
            6. **Conclusion** (300-400 words)
               - Summarize key takeaways
               - Reinforce the importance of the topic
               - Provide next steps or recommendations for readers
            
            Writing Guidelines:
            - Write for the appropriate audience based on the topic
            - Use clear, engaging language that maintains accuracy
            - Include specific examples, case studies, or relevant details where appropriate
            - Ensure smooth transitions between sections
            - Maintain consistent tone and style throughout
            - Target approximately 3500 words total""",
            agent=self.agents.content_writer_agent(),
            expected_output="A well-structured 3500-word article with introduction, four main sections, and conclusion"
        )
    
    def seo_optimization_task(self, topic: str):
        return Task(
            description=f"""Optimize the technical article for SEO while maintaining its technical accuracy and readability.
            
            Your optimization should include:
            
            1. **Keyword Strategy**
               - Identify primary keyword from the topic: "{topic}"
               - Find 3-5 related secondary keywords
               - Ensure 1.5-2% keyword density throughout the content
               - Place keywords naturally in headings and content
            
            2. **Title Optimization**
               - Create an SEO-friendly title (50-60 characters)
               - Include the primary keyword
               - Make it compelling and click-worthy
            
            3. **Meta Description**
               - Write a compelling meta description (150-160 characters)
               - Include primary keyword
               - Summarize the article's value proposition
            
            4. **Header Structure**
               - Ensure proper H1, H2, H3 hierarchy
               - Include keywords in headers naturally
               - Make headers descriptive and scannable
            
            5. **Content Optimization**
               - Add keyword variations throughout the content
               - Optimize for semantic search and related terms
               - Ensure content answers common questions about the topic
               - Add internal linking opportunities (mark with [INTERNAL_LINK] placeholder)
            
            6. **Technical SEO**
               - Ensure content is structured for featured snippets
               - Optimize for voice search queries
               - Include FAQ-style sections where appropriate
            
            7. **Tag Generation**
               - Generate 5-8 relevant tags based on the content
               - Include primary topic tags, related concepts, and audience-specific tags
               - Ensure tags are SEO-friendly and descriptive
            
            Provide the optimized content along with SEO analysis, recommendations, and generated tags.""",
            agent=self.agents.seo_optimizer_agent(),
            expected_output="SEO-optimized article with title, meta description, proper header structure, keyword optimization analysis, and generated tags"
        )
    
    def html_formatting_task(self):
        return Task(
            description="""Convert the SEO-optimized content into clean Markdown and HTML suitable for Ghost CMS publication.
            
            Content Formatting Requirements:
            1. **Markdown Format (Primary)**
               - Convert content to clean, semantic Markdown
               - Use proper heading hierarchy (# ## ###)
               - Format lists, code blocks, and emphasis correctly
               - Ensure Ghost CMS compatibility
            
            2. **HTML Format (Fallback)**
               - Create clean, semantic HTML5 structure
               - Implement correct heading hierarchy (H1, H2, H3)
               - Use appropriate tags for different content types
            
            3. **Ghost CMS Compatibility**
               - Format content for Ghost CMS editor
               - Use Ghost-compatible structure
               - Ensure proper paragraph and section formatting
            
            4. **Technical Content Formatting**
               - Format code blocks with proper syntax
               - Use appropriate formatting for technical terms
               - Ensure lists and tables are properly structured
            
            5. **SEO Elements**
               - Include meta title and description
               - Ensure proper header structure is maintained
               - Add schema markup hints where appropriate
            
            6. **Accessibility**
               - Include alt text placeholders for images
               - Ensure proper semantic structure
               - Use descriptive link text
            
            The output should be clean Markdown (preferred) and HTML (fallback) that can be directly imported into Ghost CMS.""",
            agent=self.agents.html_formatter_agent(),
            expected_output="Clean Markdown and HTML formatted for Ghost CMS with proper structure and SEO elements"
        )
    
    def quality_review_task(self, topic: str):
        return Task(
            description=f"""Conduct a comprehensive quality review of the technical article on "{topic}" before publication.
            
            Review Criteria:
            
            1. **Content Quality**
               - Verify technical accuracy and factual correctness
               - Check for logical flow and coherent structure
               - Ensure all sections contribute to the overall narrative
               - Validate that the content meets the 3500-word target
            
            2. **Technical Writing Standards**
               - Assess clarity and readability for the target audience
               - Check for consistent terminology and style
               - Verify that complex concepts are explained clearly
               - Ensure examples and use cases are relevant and helpful
            
            3. **SEO Effectiveness**
               - Verify keyword optimization is natural and effective
               - Check title and meta description quality
               - Ensure header structure supports SEO goals
               - Validate that content answers target search queries
            
            4. **HTML and Formatting**
               - Check HTML structure and semantic correctness
               - Verify Ghost CMS compatibility
               - Ensure proper formatting of technical elements
               - Validate accessibility considerations
            
            5. **Publication Readiness**
               - Confirm all sections are complete and polished
               - Check for any placeholder content or missing elements
               - Ensure content is ready for user review and approval
            
            Provide detailed feedback and recommendations for any improvements needed.""",
            agent=self.agents.quality_reviewer_agent(),
            expected_output="Comprehensive quality review report with approval status and any recommended improvements"
        )
    
    def ghost_publication_task(self, topic: str):
        return Task(
            description=f"""Publish the article on "{topic}" to Ghost CMS as a draft using the Ghost CMS Publisher tool.
            
            IMPORTANT: You MUST use the Ghost CMS Publisher tool to actually publish the content.
            
            Publication Steps:
            
            1. **Extract Content and Metadata**
               - Get the final formatted content from previous tasks
               - Extract the article title from the content
               - Get the meta description from SEO optimization
               - Extract auto-generated tags from SEO optimization output
            
            2. **Call Ghost CMS Publisher Tool**
               - Use the Ghost CMS Publisher tool with these parameters:
                 * title: The article title
                 * content: The final formatted content (HTML or Markdown)
                 * meta_description: The SEO meta description
                 * tags: The auto-generated tags from SEO optimization
            
            3. **Verify Publication**
               - Check the tool response for success/failure
               - Report the publication status to the user
               - Provide the draft URL if successful
            
            4. **Error Handling**
               - If publication fails, report the specific error
               - Provide troubleshooting guidance if needed
            
            CRITICAL: You must actually call the Ghost CMS Publisher tool - do not just describe what should be done.""",
            agent=self.agents.ghost_publisher_agent(),
            expected_output="Ghost CMS publication result with draft URL or error message"
        )
