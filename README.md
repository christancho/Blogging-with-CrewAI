# CrewAI Blog Generation System

An advanced AI-powered blog generation system that creates high-quality technical articles using CrewAI agents. The system leverages specialized AI agents for research, writing, SEO optimization, HTML formatting, quality review, and Ghost CMS publishing.

## Features

- **🔍 Intelligent Research**: Uses Brave Search API to gather comprehensive, up-to-date information on any technical topic
- **✍️ Expert Writing**: Creates well-structured 2500-word technical articles with introduction, 4 main sections, and conclusion
- **🎯 SEO Optimization**: Automatically optimizes content for search engines with keyword analysis and meta tags
- **🌐 HTML Formatting**: Generates clean, semantic HTML suitable for Ghost CMS publication
- **✅ Quality Review**: Built-in quality assurance with technical accuracy and readability checks
- **📝 Draft Management**: Creates drafts for user review before publication
- **🏷️ Topic Classification**: Automatically categorizes topics for tailored content generation
- **👤 User Approval Workflow**: Requires user approval before final publication

## System Architecture

The system uses 6 specialized AI agents working in sequence:

1. **Research Agent** - Conducts comprehensive web research using Brave Search
2. **Content Writer Agent** - Creates structured technical articles
3. **SEO Optimizer Agent** - Optimizes content for search engines
4. **HTML Formatter Agent** - Converts content to Ghost CMS-ready HTML
5. **Quality Reviewer Agent** - Reviews content for accuracy and quality
6. **Ghost Publisher Agent** - Prepares content for Ghost CMS publication

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Blogging-with-CrewAI
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   BRAVE_SEARCH_API_KEY=your_brave_search_api_key_here
   GHOST_API_KEY=your_ghost_cms_api_key_here  # Optional
   GHOST_API_URL=https://your-ghost-site.com  # Optional
   ```

## Required API Keys

### OpenAI API Key (Required)
- Sign up at [OpenAI](https://platform.openai.com/)
- Create an API key in your dashboard
- Add billing information (pay-per-use)

### Brave Search API Key (Required)
- Sign up at [Brave Search API](https://api.search.brave.com/)
- Get your free API key (2000 queries/month free tier)
- Upgrade for higher limits if needed

### Ghost CMS API Key (Optional)
- Only needed if you want automatic publishing to Ghost CMS
- Create an integration in your Ghost admin panel
- Copy the Content API key

## Usage

### Command Line Interface

**Generate a blog post interactively**:
```bash
python main.py
```

**Generate a blog post with a specific topic**:
```bash
python main.py --topic "Docker containerization best practices"
```

**Generate without user approval (auto-approve)**:
```bash
python main.py --topic "Machine Learning model deployment" --no-approval
```

**List all generated blog posts**:
```bash
python main.py --list
```

### Example Topics

The system works with any technical topic, including:

- **Software Development**: "Python async programming patterns", "React hooks best practices"
- **Cloud Computing**: "AWS Lambda serverless architecture", "Kubernetes deployment strategies"
- **Cybersecurity**: "Zero-trust security implementation", "API security best practices"
- **Data Science**: "MLOps pipeline automation", "Real-time data processing with Apache Kafka"
- **DevOps**: "CI/CD with GitHub Actions", "Infrastructure as Code with Terraform"
- **Web Development**: "Progressive Web Apps development", "GraphQL API design patterns"

## Output Structure

Generated blog posts follow this structure:

1. **Introduction** (300-400 words) - Context, background, and article overview
2. **Section 1** (500-600 words) - Foundational concepts and terminology
3. **Section 2** (500-600 words) - Technical details and implementation
4. **Section 3** (500-600 words) - Advanced concepts and best practices
5. **Section 4** (400-500 words) - Future trends and actionable insights
6. **Conclusion** (200-300 words) - Key takeaways and recommendations

**Total**: ~2500 words with SEO optimization and HTML formatting

## File Structure

```
Blogging-with-CrewAI/
├── main.py              # Main orchestration script
├── agents.py            # AI agent definitions
├── tasks.py             # Task definitions for each agent
├── tools.py             # Custom tools (Brave Search, SEO, etc.)
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── README.md           # This file
└── output/             # Generated blog posts (created automatically)
```

## Configuration

The system can be configured through environment variables:

```env
# Required
OPENAI_API_KEY=your_key_here
BRAVE_SEARCH_API_KEY=your_key_here

# Optional
GHOST_API_KEY=your_key_here
GHOST_API_URL=https://your-site.com
GHOST_AUTHOR_ID=1
OPENAI_MODEL_NAME=gpt-4
OPENAI_TEMPERATURE=0.7
```

## Workflow

1. **Topic Input**: User provides a technical topic
2. **Research Phase**: Agent searches web for comprehensive information
3. **Content Creation**: Agent writes structured 2500-word article
4. **SEO Optimization**: Agent optimizes for search engines
5. **HTML Formatting**: Agent converts to Ghost CMS-ready HTML
6. **Quality Review**: Agent reviews for accuracy and quality
7. **User Approval**: User reviews and approves content
8. **Publication**: Content prepared for Ghost CMS (manual or automatic)

## Troubleshooting

### Common Issues

**"Configuration Error: Missing required environment variables"**
- Ensure `.env` file exists with valid API keys
- Check that `OPENAI_API_KEY` and `BRAVE_SEARCH_API_KEY` are set

**"Search failed with status code: 401"**
- Verify your Brave Search API key is correct
- Check if you've exceeded your API quota

**"Error during blog generation"**
- Check your OpenAI API key and billing status
- Ensure you have sufficient API credits

### API Limits

- **OpenAI**: Pay-per-use, check your billing dashboard
- **Brave Search**: 2000 free queries/month, then paid tiers
- **Ghost CMS**: Depends on your Ghost plan

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the GitHub issues
3. Create a new issue with detailed information

## Roadmap

- [ ] Support for additional search engines
- [ ] Integration with more CMS platforms
- [ ] Custom writing style templates
- [ ] Batch processing for multiple topics
- [ ] Advanced SEO analytics
- [ ] Image generation and integration
- [ ] Multi-language support
