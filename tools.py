import requests
import json
import re
from typing import Dict, List, Optional, Union
from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from config import Config

class BraveSearchTool(BaseTool):
    name: str = "Brave Search"
    description: str = "Search the web using Brave Search API for comprehensive technical information"
    
    def _run(self, query: str, count: int = 10) -> str:
        """Execute a search query using Brave Search API"""
        try:
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": Config.BRAVE_SEARCH_API_KEY
            }
            
            params = {
                "q": query,
                "count": count,
                "search_lang": "en",
                "country": "US",
                "safesearch": "moderate",
                "freshness": "py"  # Past year for technical content
            }
            
            response = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                if "web" in data and "results" in data["web"]:
                    for result in data["web"]["results"]:
                        results.append({
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "description": result.get("description", ""),
                            "published": result.get("age", "")
                        })
                
                return json.dumps(results, indent=2)
            else:
                return f"Search failed with status code: {response.status_code}"
                
        except Exception as e:
            return f"Error performing search: {str(e)}"

class SEOAnalysisTool(BaseTool):
    name: str = "SEO Analysis"
    description: str = "Analyze and optimize content for SEO including keywords, meta tags, and structure"
    
    def _run(self, content: str, target_keyword: str) -> str:
        """Analyze content for SEO optimization"""
        try:
            # Basic SEO analysis
            word_count = len(content.split())
            keyword_count = content.lower().count(target_keyword.lower())
            keyword_density = (keyword_count / word_count) * 100 if word_count > 0 else 0
            
            # Count headers
            h1_count = content.count('<h1>')
            h2_count = content.count('<h2>')
            h3_count = content.count('<h3>')
            
            # Generate SEO recommendations
            recommendations = []
            
            if keyword_density < 1.0:
                recommendations.append(f"Increase keyword density for '{target_keyword}' (current: {keyword_density:.2f}%)")
            elif keyword_density > 3.0:
                recommendations.append(f"Reduce keyword density for '{target_keyword}' (current: {keyword_density:.2f}%)")
            
            if h1_count == 0:
                recommendations.append("Add an H1 tag for the main title")
            elif h1_count > 1:
                recommendations.append("Use only one H1 tag per page")
            
            if h2_count < 3:
                recommendations.append("Add more H2 tags for better content structure")
            
            analysis = {
                "word_count": word_count,
                "keyword_density": f"{keyword_density:.2f}%",
                "keyword_occurrences": keyword_count,
                "header_structure": {
                    "h1": h1_count,
                    "h2": h2_count,
                    "h3": h3_count
                },
                "recommendations": recommendations
            }
            
            return json.dumps(analysis, indent=2)
            
        except Exception as e:
            return f"Error analyzing SEO: {str(e)}"

class HTMLFormatterTool(BaseTool):
    name: str = "HTML Formatter"
    description: str = "Format content as HTML suitable for Ghost CMS publication"
    
    def _run(self, content: str, title: str, meta_description: str = "") -> str:
        """Format content as HTML for Ghost CMS"""
        try:
            # Clean and structure the content
            formatted_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{meta_description}">
</head>
<body>
    <article>
        {content}
    </article>
</body>
</html>"""
            
            return formatted_html
            
        except Exception as e:
            return f"Error formatting HTML: {str(e)}"

class GhostCMSTool(BaseTool):
    name: str = "Ghost CMS Publisher"
    description: str = "Publish content to Ghost CMS as a draft"
    
    def _run(self, title: str, html_content: str, meta_description: str = "", tags: List[str] = None) -> str:
        """Publish content to Ghost CMS as draft"""
        try:
            if not Config.GHOST_API_KEY or not Config.GHOST_API_URL:
                return "Ghost CMS credentials not configured. Content prepared for manual upload."
            
            # Prepare the post data
            post_data = {
                "posts": [{
                    "title": title,
                    "html": html_content,
                    "meta_description": meta_description,
                    "status": "draft",
                    "tags": tags or Config.GHOST_CONFIG["tags"],
                    "authors": [Config.GHOST_CONFIG["author_id"]]
                }]
            }
            
            headers = {
                "Authorization": f"Ghost {Config.GHOST_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # This is a placeholder for actual Ghost CMS API integration
            # In a real implementation, you would make the API call here
            response_data = {
                "status": "draft_prepared",
                "message": "Content formatted and ready for Ghost CMS upload",
                "post_data": post_data
            }
            
            return json.dumps(response_data, indent=2)
            
        except Exception as e:
            return f"Error preparing Ghost CMS content: {str(e)}"

class ContentAnalysisTool(BaseTool):
    name: str = "Content Analysis"
    description: str = "Analyze content quality, readability, and technical accuracy"
    
    def _run(self, content: str) -> str:
        """Analyze content for quality metrics"""
        try:
            # Basic content analysis
            word_count = len(content.split())
            sentence_count = len(re.findall(r'[.!?]+', content))
            paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
            
            # Calculate readability metrics
            avg_words_per_sentence = word_count / sentence_count if sentence_count > 0 else 0
            avg_sentences_per_paragraph = sentence_count / paragraph_count if paragraph_count > 0 else 0
            
            # Check for technical indicators
            code_blocks = content.count('```') // 2
            technical_terms = len(re.findall(r'\b(?:API|SDK|framework|library|database|server|client|protocol|algorithm)\b', content, re.IGNORECASE))
            
            analysis = {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "paragraph_count": paragraph_count,
                "avg_words_per_sentence": round(avg_words_per_sentence, 2),
                "avg_sentences_per_paragraph": round(avg_sentences_per_paragraph, 2),
                "code_blocks": code_blocks,
                "technical_terms_found": technical_terms,
                "readability": "Good" if 10 <= avg_words_per_sentence <= 20 else "Needs improvement"
            }
            
            return json.dumps(analysis, indent=2)
            
        except Exception as e:
            return f"Error analyzing content: {str(e)}"
