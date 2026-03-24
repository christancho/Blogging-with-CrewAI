import requests
import json
import re
import jwt
import datetime
import markdown
from typing import Any, Dict, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from langchain.tools import BaseTool  # CrewAI 0.5.0 uses LangChain's BaseTool
from config import Config


# ============================================================================
# Output Sanitization — Nimish (Nimish-0070/AI-CONTENT-GENERATOR-AGENT) pattern
# Strips raw API error traces before they propagate downstream or reach the UI.
# ============================================================================

_ERROR_SIGNALS = (
    "rate_limit", "rate limit", "429", "503", "service_unavailable",
    "overloaded", "overload", "resource_exhausted", "llm_unavailable",
    "[anthropic error]", "[gemini error]", "api error", "connection error",
)


def sanitize_output(text: Any, fallback: str = "") -> str:
    """
    Sanitize an LLM or tool output before passing it downstream.

    - Converts non-string values to str
    - Replaces raw API error traces with an empty string (or a custom fallback)
    - Normalises excessive whitespace

    Use this whenever an agent output is about to be passed as input to the
    next pipeline stage, so error traces never corrupt downstream prompts.
    """
    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            return fallback

    low = text.lower()
    if any(signal in low for signal in _ERROR_SIGNALS):
        return fallback

    # Collapse 3+ consecutive blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def generate_ghost_jwt(api_key: str, api_url: str) -> str:
    """Generate JWT token for Ghost Admin API"""
    try:
        # Split the API key (format: key_id:key_secret)
        key_id, key_secret = api_key.split(':')
        
        # Parse the API URL to get the audience
        parsed_url = urlparse(api_url)
        audience = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Create JWT payload
        iat = datetime.datetime.now(datetime.timezone.utc)
        exp = iat + datetime.timedelta(minutes=5)  # Token expires in 5 minutes
        
        payload = {
            'iat': int(iat.timestamp()),
            'exp': int(exp.timestamp()),
            'aud': f"{audience}/ghost/api/admin/"
        }
        
        # Generate JWT token
        token = jwt.encode(payload, bytes.fromhex(key_secret), algorithm='HS256', headers={'kid': key_id})
        return token
    except Exception as e:
        print(f"⚠️ JWT generation error: {e}")
        return ""

class BraveSearchTool(BaseTool):
    name: str = "Brave Search"
    description: str = "Search the web using Brave Search API for comprehensive technical information"
    
    def _run(self, query: str, count: int = 10) -> str:
        """Execute a search query using Brave Search API"""
        try:
            import json
            import re
            
            # Debug: Log the input
            print(f"🔍 Brave Search Input: {str(query)[:200]}...")
            
            # Handle complex input that might include previous results
            if isinstance(query, str) and query.startswith('['):
                try:
                    # Try to parse as JSON and extract the actual query
                    parsed = json.loads(query)
                    print(f"🔍 Parsed JSON structure: {type(parsed)} with {len(parsed) if isinstance(parsed, list) else 'N/A'} elements")
                    print(f"🔍 First element type: {type(parsed[0]) if isinstance(parsed, list) and len(parsed) > 0 else 'N/A'}")
                    if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict):
                        print(f"🔍 First element keys: {list(parsed[0].keys())}")
                    
                    if isinstance(parsed, list) and len(parsed) > 0:
                        # Check if first element is a dict with query
                        if isinstance(parsed[0], dict) and 'query' in parsed[0]:
                            query = parsed[0]['query']
                            print(f"🔍 Extracted query from dict: {query}")
                        # Check if first element is a string
                        elif isinstance(parsed[0], str):
                            query = parsed[0]
                            print(f"🔍 Using first string element: {query}")
                        # Check if it's a nested structure
                        elif isinstance(parsed[0], list) and len(parsed[0]) > 0:
                            if isinstance(parsed[0][0], dict) and 'query' in parsed[0][0]:
                                query = parsed[0][0]['query']
                                print(f"🔍 Extracted query from nested structure: {query}")
                            else:
                                query = str(parsed[0][0])
                                print(f"🔍 Using first nested element: {query}")
                        else:
                            query = str(parsed[0])
                            print(f"🔍 Using first element as string: {query}")
                    elif isinstance(parsed, dict):
                        # Handle case where the input is a single dict
                        if 'query' in parsed:
                            query = parsed['query']
                            print(f"🔍 Extracted query from single dict: {query}")
                        else:
                            query = str(parsed)
                            print(f"🔍 Using dict as string: {query}")
                    else:
                        print(f"🔍 Not a list or dict, using original query")
                        
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON parsing failed: {e}")
                    # If JSON parsing fails, try to extract query from string using regex
                    query_match = re.search(r'"query":\s*"([^"]+)"', query)
                    if query_match:
                        query = query_match.group(1)
                        print(f"🔍 Extracted query via regex: {query}")
                    else:
                        # Try to extract the first quoted string as query
                        first_quote = re.search(r'"([^"]+)"', query)
                        if first_quote:
                            query = first_quote.group(1)
                            print(f"🔍 Extracted first quoted string: {query}")
                except Exception as e:
                    print(f"⚠️ Unexpected parsing error: {e}")
                    # If all parsing fails, use the original query
                    pass
            
            # Clean the query string
            query = str(query).strip()
            
            # Remove any remaining JSON artifacts
            query = re.sub(r'^["\']|["\']$', '', query)
            
            print(f"🔍 Extracted Query: {query}")
            
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
    description: str = "Analyze and optimize content for SEO including keywords, meta tags, and structure. Input should be the content to analyze."

    def _run(self, content: str) -> str:
        """Analyze content for SEO optimization"""
        try:
            # Extract potential keywords from content (most common meaningful words)
            words = content.lower().split()
            word_freq = {}
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}

            for word in words:
                if len(word) > 4 and word not in stop_words and word.isalpha():
                    word_freq[word] = word_freq.get(word, 0) + 1

            # Get top keyword as target
            if word_freq:
                # Use a lambda to avoid typing overload issues with dict.get
                target_keyword = max(word_freq, key=lambda k: word_freq[k])
            else:
                target_keyword = "content"

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
                "target_keyword": target_keyword,
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
    name: str = "Content Formatter"
    description: str = "Format content as Markdown suitable for Ghost CMS publication"
    
    def _run(self, content: str, title: str = "", meta_description: str = "") -> str:
        """Format content as Markdown for Ghost CMS"""
        try:
            # If no title provided, try to extract it from content
            if not title:
                title = self._extract_title_from_content(content)
            
            # If no meta description provided, try to extract it from content
            if not meta_description:
                meta_description = self._extract_meta_description_from_content(content)
            
            # Create clean Markdown content directly
            markdown_content = self._create_markdown_content(content, title, meta_description)
            
            # Return Markdown as primary format
            return markdown_content
            
        except Exception as e:
            return f"Error formatting content: {str(e)}"
    
    def _extract_title_from_content(self, content: str) -> str:
        """Extract title from content"""
        import re
        from bs4 import BeautifulSoup
        
        # Try to find title in content
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE)
        if title_match:
            return BeautifulSoup(title_match.group(1), 'html.parser').get_text().strip()
        
        # Try Markdown format
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()
        
        return "Generated Blog Post"
    
    def _extract_meta_description_from_content(self, content: str) -> str:
        """Extract meta description from content"""
        import re
        from bs4 import BeautifulSoup
        
        # Try HTML format
        meta_desc_match = re.search(r'<p><strong>Meta description:</strong>\s*(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
        if meta_desc_match:
            return BeautifulSoup(meta_desc_match.group(1), 'html.parser').get_text().strip()
        
        # Try Markdown format
        meta_desc_match = re.search(r'^#\s+.+\n\n\*\s*(.+?)\s*\*', content, re.MULTILINE | re.DOTALL)
        if meta_desc_match:
            return meta_desc_match.group(1).strip()
        
        return "A comprehensive blog post generated by CrewAI"

    def _create_markdown_content(self, content: str, title: str, meta_description: str = "") -> str:
        """Create clean Markdown content for Ghost CMS"""
        try:
            from bs4 import BeautifulSoup
            import re
            
            # Parse the content
            soup = BeautifulSoup(content, 'html.parser')
            
            # Start with title and meta description
            markdown = f"# {title}\n\n"
            
            if meta_description:
                markdown += f"*{meta_description}*\n\n"
            
            # Convert content to Markdown
            markdown += self._html_to_markdown(content)
            
            return markdown.strip()

        except Exception:
            # Fallback: return content as-is with title
            return f"# {title}\n\n{content}"
    
    def _html_to_markdown(self, html_content: str) -> str:
        """Convert HTML content to Markdown"""
        try:
            from bs4 import BeautifulSoup
            import re
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove HTML wrapper tags if present
            article = soup.find('article')
            if article:
                content = article
            else:
                content = soup
            
            # Convert to Markdown
            markdown = ""
            
            for element in content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li', 'strong', 'em', 'code', 'pre', 'blockquote']):
                if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    level = int(element.name[1])
                    markdown += f"{'#' * level} {element.get_text().strip()}\n\n"
                elif element.name == 'p':
                    text = element.get_text().strip()
                    if text:
                        markdown += f"{text}\n\n"
                elif element.name == 'ul':
                    for li in element.find_all('li'):
                        markdown += f"- {li.get_text().strip()}\n"
                    markdown += "\n"
                elif element.name == 'ol':
                    for i, li in enumerate(element.find_all('li'), 1):
                        markdown += f"{i}. {li.get_text().strip()}\n"
                    markdown += "\n"
                elif element.name == 'li':
                    # Handle nested lists
                    text = element.get_text().strip()
                    if text:
                        markdown += f"- {text}\n"
                elif element.name == 'strong':
                    markdown += f"**{element.get_text().strip()}**"
                elif element.name == 'em':
                    markdown += f"*{element.get_text().strip()}*"
                elif element.name == 'code':
                    markdown += f"`{element.get_text().strip()}`"
                elif element.name == 'pre':
                    code_text = element.get_text().strip()
                    markdown += f"```\n{code_text}\n```\n\n"
                elif element.name == 'blockquote':
                    quote_text = element.get_text().strip()
                    markdown += f"> {quote_text}\n\n"
            
            # Clean up extra newlines
            markdown = re.sub(r'\n{3,}', '\n\n', markdown)
            return markdown.strip()
            
        except Exception:
            # Fallback: return plain text
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text().strip()

class GhostCMSTool(BaseTool):
    name: str = "Ghost CMS Publisher"
    description: str = """Publish content to Ghost CMS as a draft. Input should be a JSON string with keys: 'title', 'content', 'meta_description', and optionally 'tags'.
    Example: {"title": "My Post", "content": "Post content here", "meta_description": "Description", "tags": ["blog", "tech"]}"""

    def _run(self, input_data: str) -> str:
        """Publish content to Ghost CMS as draft using direct API calls"""
        try:
            # DEBUG: Show exactly what the agent is sending
            print("\n" + "="*80)
            print("🔍 DEBUG: RAW INPUT_DATA RECEIVED BY GHOST CMS TOOL")
            print("="*80)
            print(f"Type: {type(input_data)}")
            print(f"Length: {len(input_data)} characters")
            print(f"First 500 chars:\n{input_data[:500]}")
            print(f"Last 500 chars:\n{input_data[-500:]}")
            print("="*80 + "\n")

            # Parse input JSON
            try:
                data = json.loads(input_data)
                title = data.get('title', 'Untitled Post')
                content = data.get('content', '')
                meta_description = data.get('meta_description', '')
                tags = data.get('tags', None)
            except (json.JSONDecodeError, AttributeError):
                # If not JSON, treat as plain content and extract title from first line
                lines = input_data.split('\n', 1)
                title = lines[0].strip('#').strip() if lines else 'Untitled Post'
                content = input_data
                meta_description = ''
                tags = None

            if not content:
                return json.dumps({
                    "status": "error",
                    "message": "No content provided for publishing"
                })
            # Generate JWT token for Ghost Admin API
            if not Config.GHOST_API_KEY or not Config.GHOST_API_URL:
                return json.dumps({
                    "status": "error",
                    "message": "Ghost CMS API key or URL is not configured"
                })
            jwt_token = generate_ghost_jwt(Config.GHOST_API_KEY, Config.GHOST_API_URL)
            if not jwt_token:
                return json.dumps({
                    "status": "error",
                    "message": "Failed to generate JWT token for Ghost CMS authentication"
                })
            
            # Convert Markdown to HTML for Ghost CMS
            # Since we use ?source=html, Ghost expects HTML content, not Markdown
            html_content = markdown.markdown(
                content,
                extensions=['extra', 'codehilite', 'toc', 'nl2br']
            )

            # Prepare the post data following official Ghost CMS API format
            post_data = {
                "posts": [{
                    "title": title,
                    "html": html_content,  # Converted from Markdown to HTML
                    "status": "draft",
                    "excerpt": meta_description,
                    "meta_title": title,
                    "meta_description": meta_description,
                    "tags": tags or Config.GHOST_CONFIG["default_tags"]
                }]
            }

            # DEBUG: Show what we're sending to Ghost
            print("\n" + "="*80)
            print("📤 DEBUG: DATA BEING SENT TO GHOST CMS API")
            print("="*80)
            print(f"Title: {title}")
            print(f"Original Markdown length: {len(content)} chars")
            print(f"Converted HTML length: {len(html_content)} chars")
            print(f"HTML first 300 chars: {html_content[:300]}")
            print(f"Meta description: {meta_description}")
            print(f"Tags: {tags}")
            print("="*80 + "\n")
            
            headers = {
                "Authorization": f"Ghost {jwt_token}",
                "Content-Type": "application/json"
            }
            
            # Make actual API call to Ghost CMS Admin API
            # CRITICAL: ?source=html tells Ghost to process the html field as HTML content
            api_url = f"{Config.GHOST_API_URL}/ghost/api/admin/posts/?source=html"
            
            # Debug information
            print(f"🔗 Ghost CMS API URL: {api_url}")
            print(f"🔑 Using API Key: {Config.GHOST_API_KEY[:10]}...")
            print(f"🔑 Generated JWT Token: {jwt_token[:20]}...")
            print(f"📝 Creating post: {title}")
            
            response = requests.post(
                api_url,
                headers=headers,
                json=post_data,
                timeout=30
            )
            
            # DEBUG: Show Ghost's full response
            print("\n" + "="*80)
            print("📥 DEBUG: GHOST CMS API RESPONSE")
            print("="*80)
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Full Response Text:\n{response.text}")
            print("="*80 + "\n")
            
            if response.status_code == 201:
                post_response = response.json()
                created_post = post_response.get('posts', [{}])[0]
                
                response_data = {
                    "status": "success",
                    "message": "Draft successfully created in Ghost CMS",
                    "post_id": created_post.get('id'),
                    "post_url": created_post.get('url'),
                    "post_title": created_post.get('title'),
                    "draft_url": f"{Config.GHOST_API_URL}/ghost/#/editor/post/{created_post.get('id')}"
                }
                print(f"✅ Ghost CMS post created successfully: {created_post.get('title')}")
                print(f"✅ Post ID: {created_post.get('id')}")
                print(f"✅ Draft URL: {response_data['draft_url']}")
            elif response.status_code == 401:
                response_data = {
                    "status": "error",
                    "message": "Authentication failed - check your Ghost CMS Admin API key",
                    "error_details": response.text,
                    "api_url": api_url
                }
                print(f"❌ Ghost CMS authentication failed")
            elif response.status_code == 404:
                response_data = {
                    "status": "error",
                    "message": "API endpoint not found - check your Ghost CMS URL",
                    "error_details": response.text,
                    "api_url": api_url
                }
                print(f"❌ Ghost CMS API endpoint not found")
            else:
                response_data = {
                    "status": "error",
                    "message": f"Failed to create draft in Ghost CMS. Status: {response.status_code}",
                    "error_details": response.text,
                    "api_url": api_url,
                    "post_data": post_data
                }
                print(f"❌ Ghost CMS request failed with status {response.status_code}")
                print(f"❌ Error details: {response.text}")
                print(f"❌ API URL used: {api_url}")
                print(f"❌ Post data sent: {json.dumps(post_data, indent=2)}")
            
            return json.dumps(response_data, indent=2)
                
        except Exception as e:
            print(f"❌ Error publishing to Ghost CMS: {str(e)}")
            return json.dumps({
                "status": "error",
                "message": f"Error publishing to Ghost CMS: {str(e)}"
            })

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
