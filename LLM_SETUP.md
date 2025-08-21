# Real LLM Integration Setup

The AI Video Generator now supports **real LLM APIs** for professional screenplay generation! Here's how to set it up:

## 🔧 Quick Setup

1. **Navigate to the API directory:**
   ```bash
   cd api
   ```

2. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

3. **Add your API keys to `.env`:**
   ```bash
   # At least one API key is required
   OPENAI_API_KEY=sk-your-openai-key-here
   ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
   GOOGLE_API_KEY=your-google-api-key-here
   ```

## 🔑 Getting API Keys

### OpenAI (GPT-4)
- Visit: https://platform.openai.com/api-keys
- Create account and generate API key
- **Best for**: Creative storytelling and detailed formatting

### Anthropic (Claude)
- Visit: https://console.anthropic.com/
- Sign up and create API key  
- **Best for**: Precise formatting and character consistency

### Google (Gemini)
- Visit: https://makersuite.google.com/app/apikey
- Generate API key
- **Best for**: Innovative scene structure and visual storytelling

## ✨ Features

### Professional Screenplay Formatting
- **Scene Headings**: `INT./EXT. LOCATION - TIME OF DAY`
- **Character Names**: ALL CAPS, properly positioned
- **Dialogue**: Industry-standard margins and spacing
- **Action Lines**: Present tense, concise descriptions
- **Proper Margins**: 1.5" left, 1" top/bottom

### Smart Fallback System
- If API keys aren't configured, system provides formatted fallback
- Shows clear error messages and instructions
- Maintains functionality even without API access

## 🧪 Testing

1. **Start the backend** (automatically loads .env)
2. **Upload a script** in the frontend
3. **Choose an LLM** (GPT-4, Claude, or Gemini)
4. **Watch real AI generation** with professional formatting!

## 🎬 What You Get

With proper API keys, you'll receive:
- **Industry-standard screenplay format**
- **Proper character introductions**
- **Professional scene transitions**
- **Correct dialogue formatting**
- **Action line optimization**
- **Scene structure improvements**

The system now calls **real LLM APIs** instead of showing simulated responses!

---

**Note**: API usage will incur costs based on your chosen provider's pricing. Start with shorter scripts to test the integration.