# CrewAI Blog Generation System

🚀 **Generate high-quality blog posts on any topic using AI agents!**

This system uses 6 specialized AI agents to automatically research, write, optimize, and publish comprehensive blog posts. Perfect for content creators, bloggers, and businesses who need consistent, high-quality content.

## ✨ What It Does

- **🔍 Researches** any topic using real-time web search
- **✍️ Writes** comprehensive 3500-word articles with proper structure
- **🎯 Optimizes** content for SEO with auto-generated tags
- **🌐 Formats** content as clean HTML for Ghost CMS
- **✅ Reviews** quality and accuracy before publication
- **📝 Publishes** directly to Ghost CMS as drafts (automatic posting!)

## ⚠️ Requirements

**Python 3.10 or higher required** (Python 3.12 recommended)

CrewAI 0.5.0 uses modern type hints (`Type | None`) that require Python 3.10+. If you're using Python 3.9 or earlier, you'll need to upgrade.

## 🚀 Quick Start

### 1. Check Your Python Version

```bash
python3.12 --version  # Should show 3.12.x
```

**Don't have Python 3.12?** Install it:
- **macOS (Homebrew):** `brew install python@3.12`
- **Ubuntu/Debian:** `sudo apt install python3.12 python3.12-venv`
- **Windows:** Download from [python.org](https://www.python.org/downloads/)

### 2. Setup (5 minutes)

```bash
# Clone the repository
git clone https://git.christianmendieta.ca/christancho/Blogging-with-CrewAI.git
cd Blogging-with-CrewAI

# Create virtual environment with Python 3.12 (recommended)
python3.12 -m venv venv
source venv/bin/activate  # On macOS/Linux
# OR: venv\Scripts\activate  # On Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Set up your API keys
cp .env.example .env
```

### 3. Get Your API Keys

**Required:**
- **OpenAI API Key**: [Get it here](https://platform.openai.com/)
- **Brave Search API Key**: [Get it here](https://api.search.brave.com/) (2000 free searches/month)
- **Ghost CMS API Key**: Create in your Ghost admin panel
- **Ghost CMS URL**: Your Ghost site URL (e.g., https://your-site.com)

### Getting Your Ghost CMS API Key

1. **Log into your Ghost admin panel** (usually `https://your-site.com/ghost`)
2. **Go to Settings → Integrations**
3. **Click "Add custom integration"**
4. **Give it a name** (e.g., "Blog Generator")
5. **Copy the Admin API Key** (starts with something like `5d4c...`) - **NOT the Content API Key**
6. **Use your Ghost site URL** (e.g., `https://your-site.com`)

**⚠️ Important**: You need the **Admin API Key**, not the Content API Key, to create posts!

### 4. Configure Your Keys

Edit your `.env` file:

```env
# Required
OPENAI_API_KEY=sk-your-openai-key-here
BRAVE_SEARCH_API_KEY=your-brave-search-key-here
GHOST_API_KEY=your-ghost-api-key-here
GHOST_API_URL=https://your-ghost-site.com
```

### 5. Generate Your First Blog Post

```bash
# Interactive mode (recommended for first time)
python main.py

# Or specify a topic directly
python main.py --topic "How to start a successful blog"
```

## 💡 LLM Provider Configuration

**The system now supports ANY LLM provider!** Configure your preferred provider (OpenAI, Anthropic Claude, OpenRouter, local models, etc.)

### Quick Setup - OpenAI (Default):

```env
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-openai-api-key
LLM_MODEL_NAME=gpt-4o-mini
LLM_TEMPERATURE=0.7
```

### 🌟 Supported Providers

#### OpenAI (Recommended)
```env
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-key-here
LLM_MODEL_NAME=gpt-4o-mini  # 128K context, fast, cheap
LLM_TEMPERATURE=0.7
```

#### Anthropic Claude
```env
LLM_API_BASE_URL=https://api.anthropic.com/v1
LLM_API_KEY=sk-ant-your-key-here
LLM_MODEL_NAME=claude-3-5-sonnet-20241022  # 200K context
LLM_TEMPERATURE=0.7
```

#### OpenRouter (Access to Multiple Models)
```env
LLM_API_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-your-key-here
LLM_MODEL_NAME=anthropic/claude-3-5-sonnet  # or openai/gpt-4o-mini
LLM_TEMPERATURE=0.7
```

#### Local Models (Ollama)
```env
LLM_API_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=not-needed
LLM_MODEL_NAME=llama3:70b  # or mixtral:8x7b
LLM_TEMPERATURE=0.7
```

### ⚠️ Important Requirements

**Your model MUST have at least 128K context window** to avoid errors. Models with smaller context (like gpt-4 with 8K) will fail.

**Recommended Models:**
- ✅ `gpt-4o-mini` (OpenAI, 128K, fast, cheap)
- ✅ `gpt-4o` (OpenAI, 128K, most capable)
- ✅ `claude-3-5-sonnet-20241022` (Anthropic, 200K)
- ✅ `llama3:70b` (Local, 128K+ via Ollama)

**Avoid These:**
- ❌ `gpt-4` - Only 8K context
- ❌ `gpt-3.5-turbo` - Only 16K context
- ❌ Small local models with <128K context

## 📝 How It Works

The system uses 6 AI agents working together:

```
1. 🔍 Research Agent    → Finds current information about your topic
2. ✍️ Content Writer    → Creates a 3500-word structured article  
3. 🎯 SEO Optimizer     → Optimizes for search engines + generates tags
4. 🌐 HTML Formatter    → Converts to Ghost CMS-ready HTML
5. ✅ Quality Reviewer   → Checks accuracy and quality
6. 📝 Ghost Publisher   → Posts to Ghost CMS as draft (automatic!)
```

## 🎯 Example Topics

The system works with **any topic** - not just technical ones:

**Business & Marketing:**
- "Digital marketing strategies for small businesses"
- "How to build a successful startup"

**Lifestyle & Health:**
- "Sustainable living practices for urban dwellers"
- "Nutrition strategies for busy professionals"

**Technology:**
- "Python virtual environments best practices"
- "Docker containerization guide"

**Education:**
- "Effective online learning techniques"
- "Teaching coding to beginners"

**And many more!** Just provide any topic and the AI will research and write about it.

## 📊 Article Structure

Every generated article follows this structure:

- **Introduction** (400-500 words) - Hook, context, overview
- **Section 1** (600-700 words) - Foundational concepts
- **Section 2** (600-700 words) - Detailed information
- **Section 3** (600-700 words) - Advanced concepts & best practices
- **Section 4** (500-600 words) - Future trends & actionable insights
- **Conclusion** (300-400 words) - Key takeaways & next steps

**Total: ~3500 words** with SEO optimization and auto-generated tags

## 🛠️ Usage Examples

### Basic Usage
```bash
# Interactive mode - system will ask for your topic
python main.py

# Direct topic specification
python main.py --topic "Remote work productivity tips"

# Skip approval step (auto-approve)
python main.py --topic "Climate change solutions" --no-approval

# List all generated posts
python main.py --list
```

### Advanced Usage
```bash
# Generate multiple posts
python main.py --topic "AI in healthcare"
python main.py --topic "Sustainable energy solutions"
python main.py --topic "Digital nomad lifestyle"
```

## 📁 File Structure

```
Blogging-with-CrewAI/
├── main.py              # Main script - run this!
├── agents.py            # AI agent definitions
├── tasks.py             # What each agent does
├── tools.py             # Search, SEO, and publishing tools
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── .env                 # Your API keys (create this)
└── output/              # Generated blog posts (auto-created)
```

## 🔧 Configuration Options

You can customize the system by editing your `.env` file:

```env
# LLM Provider (supports ANY provider!)
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-key-here
LLM_MODEL_NAME=gpt-4o-mini
LLM_TEMPERATURE=0.7

# Search API
BRAVE_SEARCH_API_KEY=your-key-here

# Ghost CMS (for publishing)
GHOST_API_KEY=your-key-here
GHOST_API_URL=https://your-site.com
GHOST_AUTHOR_ID=1

# Legacy OpenAI vars (deprecated, use LLM_* above)
OPENAI_API_KEY=your-key-here
OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
```

### Example Configurations

**Using Anthropic Claude:**
```env
LLM_API_BASE_URL=https://api.anthropic.com/v1
LLM_API_KEY=sk-ant-your-key
LLM_MODEL_NAME=claude-3-5-sonnet-20241022
LLM_TEMPERATURE=0.7
```

**Using Local Ollama:**
```env
LLM_API_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=not-needed
LLM_MODEL_NAME=llama3:70b
LLM_TEMPERATURE=0.7
```

## 🚨 Troubleshooting

### Common Issues

**"Configuration Error: Missing required environment variables"**
- Make sure your `.env` file exists and has valid API keys
- Check that all required keys are set: `OPENAI_API_KEY`, `BRAVE_SEARCH_API_KEY`, `GHOST_API_KEY`, `GHOST_API_URL`

**`TypeError: unsupported operand type(s) for |`**
- **Cause:** You're using Python 3.9 or earlier
- **Solution:** Use Python 3.10 or higher (preferably 3.12)
```bash
# Check your Python version
python --version

# If it's < 3.10, recreate venv with Python 3.12
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**"Rate limit exceeded"**
- The system now has a very high TPM limit (200,000) to reduce rate limiting
- Switch to `gpt-4o-mini` model for even better performance
- Wait a few minutes and try again if needed
- Check your OpenAI billing status

**"Search failed with status code: 401"**
- Verify your Brave Search API key is correct
- Check if you've exceeded your 2000 free searches/month

**`cannot import name 'BaseTool' from 'crewai.tools'`**
- **Cause:** Import issue (already fixed in latest version)
- **Solution:** Make sure you have the latest code with imports from `langchain.tools`

**"Ghost CMS authentication failed"**
- Make sure you're using the **Admin API Key**, not the Content API Key
- Verify your Ghost CMS URL is correct (should end with your domain, not `/ghost`)
- Check that your Ghost site is accessible

**"Ghost CMS API endpoint not found"**
- Ensure your Ghost CMS URL is correct (e.g., `https://your-site.com`)
- Make sure your Ghost site is running and accessible
- Check that you have the correct permissions on your Ghost site

**"Error during blog generation"**
- Check your OpenAI API key and billing status
- Ensure you have sufficient API credits
- Try with a simpler topic first

**Warning: `Mixing V1 models and V2 models`**
- This is safe to ignore - it's a pydantic compatibility warning from CrewAI 0.5.0 and won't affect functionality

### Virtual Environment Activation

Every time you work on the project, remember to activate the virtual environment:

```bash
cd "/path/to/Blogging-with-CrewAI"
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows
```

When you're done: `deactivate`

### Getting Help

1. **Check this README** - Most issues are covered here
2. **Check your API keys** - Make sure they're valid and have credits
3. **Try GPT-4o-mini** - Solves most rate limit issues
4. **Start simple** - Try a basic topic first to test the system

## 💰 Cost Estimates

**Per blog post (3500 words):**

| Provider | Cost per Post | Notes |
|----------|---------------|-------|
| **OpenAI (gpt-4o-mini)** | ~$0.10-0.20 | ✅ Recommended |
| **OpenAI (gpt-4o)** | ~$0.50-1.00 | More capable but pricier |
| **Anthropic Claude** | ~$0.15-0.30 | Great alternative |
| **OpenRouter** | Varies | Pay-as-you-go from multiple providers |
| **Local (Ollama)** | FREE | Requires local GPU/CPU resources |
| **Brave Search** | FREE | 2000 searches/month included |
| **Ghost CMS** | FREE | If you have Ghost hosting |

**Most cost-effective setup: Local Ollama + Free Brave Search = $0.00 per post** 🎉

## 🎯 What You Get

After running the system, you'll have:

1. **📄 HTML file** in the `output/` folder
2. **📝 Draft in Ghost CMS** (automatically created!)
3. **🏷️ Auto-generated tags** for SEO
4. **📊 SEO-optimized content** ready for publication
5. **✅ Quality-reviewed article** that's ready to publish

## 🚀 Next Steps

1. **Generate your first post** using the Quick Start guide
2. **Check your Ghost CMS** for the automatically created draft
3. **Experiment with different topics** to see the system's versatility
4. **Customize the system** by modifying agent prompts in `agents.py`

## 📈 Tips for Best Results

- **Be specific with topics**: "Python async programming" vs "programming"
- **Use GPT-4o-mini** to avoid rate limits
- **Review the preview** before approving publication
- **Start with simpler topics** to test the system
- **Check your API credits** before generating multiple posts

---

**Ready to generate amazing blog content? Start with the Quick Start guide above!** 🚀