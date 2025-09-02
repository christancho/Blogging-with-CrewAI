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
            # Handle complex input that might include previous results
            if isinstance(query, str) and query.startswith('['):
                try:
                    # Try to parse as JSON and extract the actual query
                    import json
                    parsed = json.loads(query)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        if isinstance(parsed[0], dict) and 'query' in parsed[0]:
                            query = parsed[0]['query']
                        else:
                            query = str(parsed[0])
                except:
                    # If parsing fails, use the original query
                    pass
            
            # Clean the query string
            query = str(query).strip()
            
            # Validate query
            if not query or len(query) < 3:
                return "Error: Query too short or empty"
            
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
                
                if not results:
                    return "No search results found for the query"
                
                return json.dumps(results, indent=2)
            elif response.status_code == 401:
                return "Error: Invalid Brave Search API key"
            elif response.status_code == 429:
                return "Error: Rate limit exceeded for Brave Search API"
            else:
                return f"Search failed with status code: {response.status_code}. Response: {response.text[:200]}"
                
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
            # Ghost CMS credentials are now mandatory, so this should always be configured
            
            # Prepare the post data
            post_data = {
                "posts": [{
                    "title": title,
                    "html": html_content,
                    "meta_description": meta_description,
                    "status": "draft",
                    "tags": tags or Config.GHOST_CONFIG["default_tags"],
                    "authors": [Config.GHOST_CONFIG["author_id"]]
                }]
            }
            
            headers = {
                "Authorization": f"Ghost {Config.GHOST_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Make actual API call to Ghost CMS
            api_url = f"{Config.GHOST_API_URL}/ghost/api/content/posts/"
            
            response = requests.post(
                api_url,
                headers=headers,
                json=post_data,
                timeout=30
            )
            
            if response.status_code == 201:
                post_response = response.json()
                created_post = post_response.get('posts', [{}])[0]
                
                response_data = {
                    "status": "success",
                    "message": "Draft successfully created in Ghost CMS",
                    "post_id": created_post.get('id'),
                    "post_url": created_post.get('url'),
                    "post_title": created_post.get('title'),
                    "draft_url": f"{Config.GHOST_API_URL.replace('/ghost', '')}/ghost/#/editor/post/{created_post.get('id')}"
                }
            else:
                response_data = {
                    "status": "error",
                    "message": f"Failed to create draft in Ghost CMS. Status: {response.status_code}",
                    "error_details": response.text,
                    "post_data": post_data
                }
            
            return json.dumps(response_data, indent=2)
            
        except Exception as e:
            return f"Error preparing Ghost CMS content: {str(e)}"

class TagExtractionTool(BaseTool):
    name: str = "Tag Extraction"
    description: str = "Extract generated tags from SEO optimization output"
    
    def _run(self, seo_output: str) -> str:
        """Extract tags from SEO optimization output"""
        try:
            import re
            import json
            
            # Look for tags in various formats
            tag_patterns = [
                r'tags?:\s*\[(.*?)\]',  # tags: ["tag1", "tag2"]
                r'generated tags?:\s*\[(.*?)\]',  # generated tags: ["tag1", "tag2"]
                r'#(\w+)',  # hashtag format
                r'Tags:\s*(.*?)(?:\n|$)',  # Tags: tag1, tag2, tag3
            ]
            
            tags = []
            for pattern in tag_patterns:
                matches = re.findall(pattern, seo_output, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    if '[' in match and ']' in match:
                        # JSON array format
                        try:
                            tag_list = json.loads(f'[{match}]')
                            tags.extend(tag_list)
                        except:
                            pass
                    else:
                        # Comma-separated format
                        tag_list = [tag.strip().strip('"\'') for tag in match.split(',')]
                        tags.extend(tag_list)
            
            # Clean and deduplicate tags
            clean_tags = []
            for tag in tags:
                if tag and len(tag) > 1 and tag not in clean_tags:
                    # Remove special characters and make lowercase
                    clean_tag = re.sub(r'[^\w\s-]', '', tag.lower().strip())
                    if clean_tag:
                        clean_tags.append(clean_tag)
            
            # Limit to 8 tags max
            clean_tags = clean_tags[:8]
            
            return json.dumps(clean_tags, indent=2)
            
        except Exception as e:
            return f"Error extracting tags: {str(e)}"

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
