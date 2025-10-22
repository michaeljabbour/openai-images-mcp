# OpenAI Images MCP Server

A Model Context Protocol (MCP) server that enables Claude Desktop to generate and refine images using OpenAI's **GPT-Image-1** model through conversational interactions.

## 🎯 Key Features

### ✨ What Makes This Special
- **Full-Quality Images** - Always saves high-resolution PNGs (no compression)
- **Conversational Refinement** - Iteratively improve images through natural dialogue
- **Easy Access** - Direct file paths in chat, images saved to Downloads folder
- **Context Preservation** - Each conversation maintains full context for coherent refinements
- **Single Model Focus** - Uses GPT-Image-1 exclusively for consistent, high-quality results

## 🚀 Quick Start

### Installation

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set OpenAI API Key**:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

3. **Configure Claude Desktop**:

Add to your Claude Desktop config file:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "openai-images": {
      "command": "python3",
      "args": ["/full/path/to/openai_images_mcp.py"],
      "env": {
        "OPENAI_API_KEY": "your-openai-api-key-here"
      }
    }
  }
}
```

**Important**: Replace `/full/path/to/openai_images_mcp.py` with the actual absolute path to the file.

4. **Restart Claude Desktop** (Cmd+Q to fully quit, then reopen)

5. **Verify Installation**:

```bash
# Test the module loads
python3 -c "import openai_images_mcp; print('✅ Module loads successfully')"

# Run the test suite (optional - interactive, some tests require API calls)
python3 test_local.py
```

## 🧪 Testing

### Local Test Suite

The `test_local.py` script provides an interactive test suite:

```bash
python3 test_local.py
```

**What it tests**:
- ✅ API key configuration
- ✅ Input parameter validation
- 💰 Simple image generation (optional - costs money, prompts before running)
- 💰 Conversational refinement (optional - costs money, prompts before running)

**Running specific tests**:
```bash
# Just validation tests (free, no API calls)
python3 test_local.py
# When prompted, press 'N' to skip API tests

# Full test suite (makes real API calls - costs money)
python3 test_local.py
# When prompted, press 'y' for each test
```

### Troubleshooting Tests

If tests fail:
1. Check API key is set: `echo $OPENAI_API_KEY`
2. Verify module imports: `python3 -c "import openai_images_mcp"`
3. Check logs: `tail -f ~/Library/Logs/Claude/mcp-server-openai-images.log`

## 📚 Available Tools

### 1. `openai_conversational_image` (Primary Tool)

Generate and refine images through multi-turn conversation using the Responses API.

**Key Parameters**:
- `prompt`: Your image description or refinement instruction
- `conversation_id`: ID to continue a previous conversation (auto-generated if not provided)
- `input_image_file_id`: File ID from previous generation
- `input_image_path`: Local image file to refine
- `assistant_model`: GPT model for processing (gpt-4o, gpt-4-turbo)
- `size`: Image dimensions (**1024x1024**, **1024x1536**, **1536x1024** only)

**Note**: GPT-Image-1 only supports these 3 sizes. Quality, style, and transparency parameters are not available.

**Example Conversation Flow**:
```
User: "Generate a cozy coffee shop interior"
→ Returns file path: ~/Downloads/openai_image_20251021_143022_abc12345.png

User: "Make it more modern with industrial elements"
→ Returns new file path (conversation context maintained automatically)

User: "Add people working on laptops"
→ Returns refined image file path
```

### 2. `openai_generate_image`

Simplified wrapper for quick, single-request image generation. Internally uses the conversational API.

**Parameters**:
- `prompt`: Text description
- `size`: Image dimensions (1024x1024, 1024x1536, 1536x1024)

### 3. `openai_list_conversations`

List all active image generation conversations to continue previous sessions.

## 💡 Usage Examples in Claude

### Conversational Refinement (Best Experience)

```
"Create an image of a futuristic city at sunset"
→ Claude generates initial image

"Make the buildings taller and add flying vehicles"
→ Claude refines using same conversation

"Change the color palette to cyberpunk neon"
→ Claude continues refinement

"Add rain and reflections on the streets"
→ Final refined image
```

### Direct Generation

```
"Generate a photorealistic eagle in flight"
"Make a portrait in the style of Van Gogh"
"Create a minimalist logo for a tech company"
```

## 🎨 Advanced Features

### Conversation Management

The server maintains conversation context, allowing you to:
- Continue refinements across multiple interactions
- Reference previous generations
- Build complex images iteratively
- Upload and refine local images

### File ID System

When using the Responses API:
- Generated images receive File IDs
- Use File IDs to reference images in future refinements
- No need to re-upload or re-describe base images

### File Management

The server automatically:
- Saves full-quality PNG to ~/Downloads/ folder
- Returns direct file path in chat response
- Maintains conversation IDs for refinement
- Uses timestamped filenames for uniqueness

**File naming**:
- Format: `openai_image_YYYYMMDD_HHMMSS_XXXXXXXX.png`
- Example: `openai_image_20251021_143022_abc12345.png`
- Easy to find recent images by sorting Downloads by date

## 🔧 Troubleshooting

### Installation Issues

#### 1. **Module Not Loading / Import Errors**

```bash
# Test if module loads
python3 -c "import openai_images_mcp; print('✅ Works')"

# If you see import errors:
ModuleNotFoundError: No module named 'fastmcp'
```

**Solution**: Install all dependencies
```bash
pip3 install -r requirements.txt
```

**Critical packages**:
- `fastmcp>=2.12.5` (provides Image utilities)
- `mcp>=1.16.0` (MCP protocol support)

#### 2. **"spawn python ENOENT" Error**

**Problem**: Claude Desktop can't find Python

**Solution**: Use `python3` instead of `python` in your config:
```json
{
  "command": "python3",  // NOT "python"
  "args": ["/absolute/path/to/openai_images_mcp.py"]
}
```

#### 3. **Server Not Starting**

**Symptoms**: No tools appear in Claude Desktop's `/mcp` list

**Steps to debug**:
```bash
# 1. Check config file exists
ls -la ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 2. Verify the path is absolute (not relative)
# BAD:  "./openai_images_mcp.py"
# GOOD: "/Users/yourname/dev/openai-images-mcp/openai_images_mcp.py"

# 3. Check logs for errors
tail -20 ~/Library/Logs/Claude/mcp-server-openai-images.log

# 4. Restart Claude Desktop COMPLETELY
# Cmd+Q to quit, then reopen (not just close window)
```

### Runtime Issues

#### 4. **"Invalid value: '1024x1792'" Error**

**Problem**: Trying to use unsupported image size

**Supported sizes** (only these 3):
- ✅ `1024x1024` (square)
- ✅ `1024x1536` (portrait)
- ✅ `1536x1024` (landscape)

**NOT supported**:
- ❌ `1024x1792`
- ❌ `1792x1024`

#### 6. **"API key not found" Error**

**Solutions**:
```bash
# Option 1: Set in config file (recommended)
# Edit: ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "env": {
    "OPENAI_API_KEY": "sk-proj-your-actual-key-here"
  }
}

# Option 2: Set as environment variable
export OPENAI_API_KEY="sk-proj-your-key-here"

# Verify it's set:
echo $OPENAI_API_KEY
```

### Debug Mode

**Test module loads**:
```bash
python3 -c "import openai_images_mcp; print('✅ Module loads successfully')"
```

**Run validation tests** (no API calls):
```bash
python3 test_local.py
# Press 'N' when asked about API tests
```

**Monitor logs in real-time**:
```bash
# macOS
tail -f ~/Library/Logs/Claude/mcp-server-openai-images.log

# Success indicators:
# ✓ "Image saved to: /Users/.../Downloads/openai_image_... (XXX.X KB)"
# ✓ "Conversation ID: conv_..."

# Error indicators:
# ✗ "Invalid value: '1024x1792'"
# ✗ "API key not found"
# ✗ "ModuleNotFoundError"
```

**Check server is connected**:
```
# In Claude Desktop, type:
/mcp

# You should see:
# openai-images: ✓ Connected
```

### Still Having Issues?

1. **Verify installation**:
   ```bash
   # Check all dependencies
   pip3 list | grep -E "(mcp|fastmcp|pydantic|httpx|pillow)"
   ```

2. **Test locally** (no Claude Desktop):
   ```bash
   python3 test_local.py
   ```

3. **Check for conflicts**:
   ```bash
   # Make sure no old versions
   pip3 uninstall mcp fastmcp
   pip3 install -r requirements.txt
   ```

4. **Create an issue** with:
   - Your OS version
   - Python version (`python3 --version`)
   - Full error message
   - Last 50 lines of logs
   - Output of `pip3 list | grep -E "(mcp|fastmcp)"`

## 💰 Pricing Considerations

- **GPT-Image-1**: Check current Responses API pricing at [OpenAI's pricing page](https://openai.com/pricing)
- Iterative refinement may use multiple API calls

## 🔐 Security Notes

1. Store API keys securely as environment variables
2. Server only accesses files you explicitly specify
3. Conversation history is stored in memory (cleared on restart)
4. Follow OpenAI's usage policies for generated content

## 📝 Changelog

### Version 3.0.0 (Current)
- **✨ Full-quality images** - Always saves high-resolution PNGs (no compression)
- **📁 Easy access** - Direct file paths returned in chat response
- **🔧 Fixed base64 handling** - Correctly processes OpenAI's b64_json responses
- **📏 Updated size support** - Only the 3 sizes actually supported by the API
- **🎯 Simplified to GPT-Image-1 only** - Removed DALL-E 2/3 support
- **🧹 Streamlined codebase** - Reduced from 968 to ~550 lines
- **📝 Enhanced tool descriptions** for better Claude understanding

### Version 2.0.0
- Added GPT-Image-1 support with Responses API
- Implemented conversational image generation
- Added multi-turn editing capabilities
- File ID support for image references

### Version 1.0.0
- Initial release with DALL-E 3 and DALL-E 2
- Direct API image generation
- Image editing and variations

## 📄 License

MIT License - See LICENSE file for details

## 🏗️ Architecture

```
┌─────────────────┐
│ Claude Desktop  │
└────────┬────────┘
         │ MCP Protocol
┌────────▼────────────────────────┐
│   openai_images_mcp.py          │
│   (FastMCP Server)              │
├─────────────────────────────────┤
│ • openai_conversational_image   │
│ • openai_generate_image         │
│ • openai_list_conversations     │
│                                 │
│ Key Features:                   │
│ • Base64 → Full PNG             │
│ • Save to Downloads             │
│ • File path in response         │
└────────┬────────────────────────┘
         │ HTTPS
┌────────▼────────────────────────┐
│   OpenAI Responses API          │
│   (GPT-4 orchestration)         │
│        │                        │
│        ▼                        │
│   OpenAI Images API             │
│   (gpt-image-1 model)           │
└─────────────────────────────────┘
```

## 🆘 Support

For issues or questions:
1. Check this README and troubleshooting section
2. Check the logs: `~/Library/Logs/Claude/mcp-server-openai-images.log`
3. Run local tests: `python3 test_local.py`
4. Review `CHANGES.md` for detailed changelog
5. Check OpenAI's API documentation for GPT-Image-1
6. Submit issues with full error messages

## 🙏 Credits

Built with:
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [FastMCP](https://github.com/jlowin/fastmcp)
- [OpenAI API](https://platform.openai.com/)

---

**Happy image generating! 🎨✨**
