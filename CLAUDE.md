# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python MCP (Model Context Protocol) server that provides conversational image generation capabilities to Claude Desktop using OpenAI's GPT-Image-1 model.

**Phase 1 Features**:
- **Pre-Generation Dialogue** - Guided questions refine vision before generating (4 modes: quick/guided/explorer/skip)
- **Automatic Prompt Enhancement** - AI quality analysis and improvement (0-100 scoring)
- **Image Quality Verification** - Type-specific checklists before delivery
- **Persistent Conversations** - Local storage in ~/.openai-images-mcp/conversations/
- **Smart Size Detection** - Auto-suggests dimensions based on image type
- **Conversational Refinement** - Multi-turn editing with context preservation
- **Full-quality images** - High-resolution PNGs saved to ~/Downloads/

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set API key (required)
export OPENAI_API_KEY="your-api-key-here"
```

### Testing
```bash
# Test module loads
python3 -c "import openai_images_mcp; print('✅ Module loads')"

# Run local test suite (interactive)
python3 test_local.py

# Check logs in real-time
tail -f ~/Library/Logs/Claude/mcp-server-openai-images.log
```

### Claude Desktop Configuration
After changes, restart Claude Desktop to reload the server. Config location:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Log location:
- macOS: `~/Library/Logs/Claude/mcp-server-openai-images.log`

## Architecture

### Single-API Model (Simplified)

The server uses **only** the Responses API with GPT-Image-1 for all image generation:

- **Conversational approach**: All image generation goes through `/chat/completions` with tool calling
- **Stateful**: Maintains conversation state in `conversation_store`
- **Forced tool calling**: Uses `tool_choice` to ensure GPT-4 calls the `generate_image` tool
- **File ID support**: Images can be uploaded and referenced in subsequent refinements

### State Management

```python
conversation_store = {}  # conversation_id → [message_history]
file_store = {}          # file_path → openai_file_id (currently unused)
```

Both stores are **in-memory only** and cleared on server restart. Conversations are not persisted to disk.

### Request Flow

All tools follow this pattern:
1. Pydantic validates input parameters
2. `get_api_key()` extracts API key from parameter or environment
3. API call via `call_responses_api()` or `make_api_request()` with retry logic
4. Response formatted as markdown or JSON based on `output_format`
5. Errors returned as JSON with `error` field

### HTTP Layer (openai_images_mcp.py:216-251)

`make_api_request()` provides:
- Exponential backoff retry for 429 rate limit errors (max 3 attempts)
- 120s timeout for Responses API calls
- Unified error handling for all API calls

### Image Handling

**Simple and Clean Approach**:

The server returns a formatted text string with file information:
```python
return f"""✅ **Image Generated Successfully**

📁 **File saved to:** `{save_path}`
📏 **Size:** {size_kb:.1f} KB
🔗 **Conversation ID:** `{conversation_id}`

To view the image, open the file from your Downloads folder."""
```

**Image Processing Pipeline**:
1. **Receive base64** from OpenAI (`b64_json` field, NOT `url`)
2. **Decode to bytes**: `img_bytes = base64.b64decode(image_b64)`
3. **Save full PNG** to `~/Downloads/openai_image_[timestamp]_[uuid].png`
4. **Return file path** as formatted text

**Upload for Conversation** (`upload_image_file`):
- Uploads to Files API with `purpose="assistants"`
- Returns file_id for use in conversation messages
- Used when user provides `input_image_path`

## Key Implementation Details

### Responses API Conversation Flow (openai_images_mcp.py:253-367)

```python
1. Retrieve conversation history from conversation_store
2. Append new user message with prompt + optional image file_id
3. Build messages array with conversation history
4. Define generate_image tool specification
5. Call /chat/completions with tool_choice forcing generate_image tool
6. Extract tool_calls from response (image generated inside tool call)
7. Store full conversation (user message + assistant response) in conversation_store
8. Return formatted response with conversation_id for next turn
```

The `tool_choice` parameter (lines 329-332) ensures GPT-4 always calls the image generation tool rather than just describing what it would do.

### Tool Responsibilities

| Tool | Purpose |
|------|---------|
| `openai_conversational_image` | Multi-turn refinement with context (primary tool) |
| `openai_generate_image` | Simple wrapper that calls conversational_image |
| `openai_list_conversations` | Browse active conversations |

**Note**: `openai_generate_image` is just a convenience wrapper. It converts `GenerateImageInput` to `ConversationalImageInput` and calls `openai_conversational_image` internally (openai_images_mcp.py:538-548).

## Important Constraints

### GPT-Image-1 Requirements
- Prompt length: 4000 characters maximum
- **Sizes: ONLY 1024x1024, 1024x1536, or 1536x1024** (not 1024x1792 or 1792x1024!)
- **No quality/style parameters** (removed in v3.0 - not supported by API)
- Always generates exactly 1 image per call
- Returns **base64-encoded PNG** in `b64_json` field (not URL)

Critical: The tool definition sent to OpenAI (lines 297-300) must only list the 3 supported sizes, or OpenAI will choose unsupported sizes and fail.

### Response Formats

**For successful image generation**:
Returns formatted markdown string with:
- ✅ Success indicator
- 📁 Full file path to Downloads
- 📏 File size in KB
- 🔗 Conversation ID for refinement
- Instructions for viewing

**For errors**:
Returns JSON string with `{"error": "...", "success": false}`

**For list operations**:
Returns formatted markdown or JSON based on `output_format` parameter

## Common Development Tasks

### Adding a New Tool

1. Define Pydantic input model in "Input Models" section
2. Implement tool function with `@mcp.tool()` decorator
3. Follow the standard pattern: validate → get_api_key → call_responses_api → format_response
4. Add tests to `test_mcp_server.py`

### Modifying Conversation Logic

Conversation state is managed in `call_responses_api()` (openai_images_mcp.py:253-367). Key considerations:
- Messages array must maintain user/assistant alternation
- File IDs must be uploaded before referencing in messages
- Tool choice must force `generate_image` to guarantee image generation
- Conversation history grows unbounded (consider memory implications for long sessions)

### Error Handling

All API errors should be caught and returned as JSON:
```python
return json.dumps({"error": "Description of error"})
```

Retry logic for rate limits is automatic via `make_api_request()`.

## Testing Notes

Test file uses direct function imports rather than MCP protocol:
```python
from openai_images_mcp import openai_generate_image, GenerateImageInput
```

For full MCP protocol testing, use the MCP inspector or Claude Desktop directly.

## Version 3.0 Changes

### Added Features
- ✨ **Full-quality PNG output** - No compression, always high resolution
- 📁 **Direct file paths** - File location returned in text response
- 🔧 **Fixed base64 handling** - Correctly extracts `b64_json` from responses
- 📏 **Corrected size enum** - Only the 3 actually supported sizes
- 🧹 **Simplified codebase** - Removed ~100 lines of compression logic

### Removed Features
The following were removed to simplify the codebase:
- **DALL-E 2/3 support**: All Direct Image API code paths
- **`openai_edit_image` tool**: Mask-based editing
- **`openai_create_variations` tool**: Variation generation
- **Quality/Style parameters**: Not supported by GPT-Image-1
- **1024x1792 and 1792x1024 sizes**: Not actually supported by API
- **Image compression**: Removed complexity, always full quality

### Key Bug Fixes
1. **Tool definition size enum**: Fixed to list only supported sizes
2. **Base64 extraction**: Changed from looking for `url` to `b64_json`
3. **Return format**: Simple text string with file path (no MCP content list complexity)

## Dependencies

Core dependencies (requirements.txt):
- `mcp>=1.16.0`: MCP SDK for protocol implementation
- `fastmcp>=2.12.5`: FastMCP framework
- `pydantic>=2.12.3`: Input validation with Field descriptions
- `httpx>=0.24.0`: Async HTTP client for OpenAI API

**Note**: Pillow removed in v3.0 (no longer compressing images)

## Configuration

API key sources (in priority order):
1. `api_key` parameter in tool call
2. `OPENAI_API_KEY` environment variable

The server will error if no API key is found.

## Troubleshooting

Common issues:

### "Invalid value: '1024x1792'"
- **Root cause**: Tool definition lists unsupported size
- **Fix**: Ensure enum only has: 1024x1024, 1024x1536, 1536x1024
- OpenAI will choose from listed sizes, so listing unsupported ones causes errors

### File Not Found in Downloads
- Check the full path returned in the response
- Verify Downloads folder exists: `ls ~/Downloads/`
- Check logs for actual save location

### Other Issues
- **"spawn python ENOENT"**: Use `python3` in config
- **Wrong path**: Use absolute path to `openai_images_mcp.py`
- **API key not found**: Set in config file's `env` section
- **Conversation not found**: Use `openai_list_conversations` tool

**Log locations**:
- macOS: `~/Library/Logs/Claude/mcp-server-openai-images.log`
- Windows: Check Claude logs directory

**Success indicators in logs**:
```
✓ "Image saved to: /Users/.../Downloads/openai_image_... (XXX.X KB)"
✓ "Conversation ID: conv_..."
```
