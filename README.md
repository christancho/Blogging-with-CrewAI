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

## 🚀 Quick Start

### 1. Setup (5 minutes)

```bash
# Clone the repository
git clone https://git.christianmendieta.ca/christancho/Blogging-with-CrewAI.git
cd Blogging-with-CrewAI

# Install dependencies
pip install -r requirements.txt

# Set up your API keys
cp .env.example .env
```

### 2. Get Your API Keys

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
5. **Copy the Content API Key** (starts with something like `5d4c...`)
6. **Use your Ghost site URL** (e.g., `https://your-site.com`)

### 3. Configure Your Keys

Edit your `.env` file:

```env
# Required
OPENAI_API_KEY=sk-your-openai-key-here
BRAVE_SEARCH_API_KEY=your-brave-search-key-here
GHOST_API_KEY=your-ghost-api-key-here
GHOST_API_URL=https://your-ghost-site.com
```

### 4. Generate Your First Blog Post

```bash
# Interactive mode (recommended for first time)
python main.py

# Or specify a topic directly
python main.py --topic "How to start a successful blog"
```

## 💡 Important: TPM Limits & Model Recommendation

**⚠️ Due to OpenAI's TPM (Tokens Per Minute) limits, we strongly recommend using GPT-4o-mini instead of GPT-4:**

```env
# Add this to your .env file for better performance
OPENAI_MODEL_NAME=gpt-4o-mini
```

**Why GPT-4o-mini?**
- ✅ Higher TPM limits (much faster processing)
- ✅ Lower cost per token
- ✅ Still produces excellent quality content
- ✅ Less likely to hit rate limits

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
# Required
OPENAI_API_KEY=your-key-here
BRAVE_SEARCH_API_KEY=your-key-here
GHOST_API_KEY=your-key-here
GHOST_API_URL=https://your-site.com

# Optional
GHOST_AUTHOR_ID=1

# Model settings (recommended)
OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
```

## 🚨 Troubleshooting

### Common Issues

**"Configuration Error: Missing required environment variables"**
- Make sure your `.env` file exists and has valid API keys
- Check that all required keys are set: `OPENAI_API_KEY`, `BRAVE_SEARCH_API_KEY`, `GHOST_API_KEY`, `GHOST_API_URL`

**"Rate limit exceeded"**
- Switch to `gpt-4o-mini` model (see recommendation above)
- Wait a few minutes and try again
- Check your OpenAI billing status

**"Search failed with status code: 401"**
- Verify your Brave Search API key is correct
- Check if you've exceeded your 2000 free searches/month

**"Error during blog generation"**
- Check your OpenAI API key and billing status
- Ensure you have sufficient API credits
- Try with a simpler topic first

### Getting Help

1. **Check this README** - Most issues are covered here
2. **Check your API keys** - Make sure they're valid and have credits
3. **Try GPT-4o-mini** - Solves most rate limit issues
4. **Start simple** - Try a basic topic first to test the system

## 💰 Cost Estimates

**Per blog post (3500 words):**
- **OpenAI (GPT-4o-mini)**: ~$0.10-0.20
- **Brave Search**: Free (2000 searches/month)
- **Ghost CMS**: Free (if you have Ghost)

**Total: ~$0.10-0.20 per blog post** 🎉

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