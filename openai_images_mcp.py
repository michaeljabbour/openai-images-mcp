#!/usr/bin/env python3
"""
OpenAI Images MCP Server

An MCP server that provides conversational image generation and refinement
using OpenAI's GPT-Image-1 model with the Responses API.

This server enables Claude Desktop to generate and refine images through
natural conversation with iterative improvements.
"""

import os
import json
import base64
import httpx
import logging
import asyncio
from typing import Optional, List, Dict, Any
from enum import Enum
from pathlib import Path
from io import BytesIO
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================
# Helper Functions
# ============================

# Removed compression - always save full-quality PNG to Downloads

# Constants
API_BASE_URL = "https://api.openai.com/v1"
MAX_PROMPT_LENGTH = 4000
MAX_RETRIES = 3

# Initialize MCP server
mcp = FastMCP("openai_images_mcp")

# Store for conversation threads and file IDs
conversation_store = {}
file_store = {}

# ============================
# Pydantic Models
# ============================

class ImageSize(str, Enum):
    """Supported image sizes for GPT-Image-1 (verified from API)."""
    SIZE_1024x1024 = "1024x1024"  # Square
    SIZE_1024x1536 = "1024x1536"  # Portrait
    SIZE_1536x1024 = "1536x1024"  # Landscape

class OutputFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"

# ============================
# Input Models
# ============================

class ConversationalImageInput(BaseModel):
    """Input model for conversational image generation using GPT-Image-1."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    prompt: str = Field(
        ...,
        description="Text description for new image or refinement instruction for existing conversation. For refinements, use natural language like 'make it darker' or 'add more detail'.",
        min_length=1,
        max_length=4000
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Conversation ID from previous generation to continue refining that image. Omit to start a new conversation. Auto-generated if not provided."
    )
    input_image_file_id: Optional[str] = Field(
        default=None,
        description="File ID from OpenAI of a previously generated image to refine. Obtained from prior tool responses. Cannot be used with input_image_path."
    )
    input_image_path: Optional[str] = Field(
        default=None,
        description="Absolute path to local image file to upload and refine. Use to start from an existing image. Cannot be used with input_image_file_id."
    )
    assistant_model: Optional[str] = Field(
        default="gpt-4o",
        description="GPT model for understanding refinement instructions. Recommended: gpt-4o for best results. Options: gpt-4o, gpt-4-turbo."
    )
    size: Optional[ImageSize] = Field(
        default=ImageSize.SIZE_1024x1024,
        description="Image dimensions. Options: 1024x1024 (square), 1024x1536 (portrait), 1536x1024 (landscape)."
    )
    output_format: Optional[OutputFormat] = Field(
        default=OutputFormat.MARKDOWN,
        description="Output format for the tool response"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key (uses environment variable if not provided)"
    )

class GenerateImageInput(BaseModel):
    """Input model for simple image generation (wrapper for conversational API)."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    prompt: str = Field(
        ...,
        description="Text description of the desired image",
        min_length=1,
        max_length=4000
    )
    size: Optional[ImageSize] = Field(
        default=ImageSize.SIZE_1024x1024,
        description="Size of the generated image (1024x1024, 1024x1536, or 1536x1024)"
    )
    output_format: Optional[OutputFormat] = Field(
        default=OutputFormat.MARKDOWN,
        description="Output format for the tool response"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key (uses environment variable if not provided)"
    )

# ============================
# Utility Functions
# ============================

def get_api_key(provided_key: Optional[str] = None) -> str:
    """Get OpenAI API key from provided value or environment."""
    api_key = provided_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenAI API key not found. Please provide it as a parameter or set the OPENAI_API_KEY environment variable."
        )
    return api_key

def generate_conversation_id() -> str:
    """Generate a unique conversation ID."""
    return f"conv_{uuid4().hex[:12]}"

async def upload_image_file(image_path: str, api_key: str) -> str:
    """Upload an image file to OpenAI and return its file ID."""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()

        # Validate it's a valid image
        img = Image.open(BytesIO(image_data))

        # Upload to OpenAI Files API
        files = {"file": ("image.png", image_data, "image/png")}
        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/files",
                headers=headers,
                files=files,
                data={"purpose": "assistants"}
            )
            response.raise_for_status()
            file_data = response.json()
            return file_data["id"]

    except FileNotFoundError:
        raise ValueError(f"Image file not found: {image_path}")
    except Exception as e:
        raise ValueError(f"Failed to upload image: {str(e)}")

async def make_api_request(
    endpoint: str,
    api_key: str,
    json_data: Optional[Dict[str, Any]] = None,
    method: str = "POST"
) -> Dict[str, Any]:
    """Make an API request to OpenAI with retry logic."""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        for attempt in range(MAX_RETRIES):
            try:
                if method == "POST":
                    response = await client.post(url, headers=headers, json=json_data)
                else:
                    response = await client.request(method, url, headers=headers, json=json_data)

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                error_detail = e.response.text
                raise ValueError(f"OpenAI API error ({e.response.status_code}): {error_detail}")
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(1)
                    continue
                raise ValueError(f"API request failed: {str(e)}")

async def call_responses_api(
    prompt: str,
    api_key: str,
    conversation_id: str,
    assistant_model: str = "gpt-4o",
    input_image_file_id: Optional[str] = None,
    image_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Call the OpenAI Responses API for conversational image generation."""

    # Build messages for the conversation
    messages = []

    # Retrieve conversation history if exists
    if conversation_id in conversation_store:
        messages.extend(conversation_store[conversation_id])

    # Build the current message
    current_message = {"role": "user", "content": []}

    # Add image input if provided
    if input_image_file_id:
        current_message["content"].append({
            "type": "image_file",
            "image_file": {"file_id": input_image_file_id}
        })

    # Add text prompt
    current_message["content"].append({
        "type": "text",
        "text": prompt
    })

    messages.append(current_message)

    # Build the request payload for Responses API
    payload = {
        "model": assistant_model,
        "messages": messages,
        "tools": [{
            "type": "function",
            "function": {
                "name": "generate_image",
                "description": "Generate an image based on a text prompt using gpt-image-1",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "enum": ["gpt-image-1"],
                            "default": "gpt-image-1"
                        },
                        "prompt": {
                            "type": "string",
                            "description": "The prompt for image generation"
                        },
                        "size": {
                            "type": "string",
                            "enum": ["1024x1024", "1024x1536", "1536x1024"],
                            "default": "1024x1024"
                        }
                    },
                    "required": ["prompt"]
                }
            }
        }],
        "tool_choice": {
            "type": "function",
            "function": {"name": "generate_image"}
        },
        "parallel_tool_calls": False,
        "max_tokens": 1000
    }

    # Make the API call
    response = await make_api_request(
        endpoint="/chat/completions",
        api_key=api_key,
        json_data=payload
    )

    # Store the conversation for future reference
    if conversation_id not in conversation_store:
        conversation_store[conversation_id] = []

    conversation_store[conversation_id].append(current_message)

    # Process response to extract image information
    if "choices" in response and response["choices"]:
        choice = response["choices"][0]
        if "message" in choice:
            assistant_message = choice["message"]
            conversation_store[conversation_id].append(assistant_message)

            # Check for tool calls (image generation)
            if "tool_calls" in assistant_message:
                for tool_call in assistant_message["tool_calls"]:
                    if tool_call["function"]["name"] == "generate_image":
                        # Parse the tool call arguments
                        tool_args = json.loads(tool_call["function"]["arguments"]) if isinstance(tool_call["function"].get("arguments"), str) else tool_call["function"].get("arguments", {})

                        logger.info(f"Tool call arguments: {tool_args}")

                        # Actually execute the image generation by calling the Images API
                        # Note: gpt-image-1 only supports model, prompt, and size parameters
                        image_payload = {
                            "model": "gpt-image-1",
                            "prompt": tool_args.get("prompt", prompt),
                            "size": tool_args.get("size", image_params.get("size", "1024x1024") if image_params else "1024x1024"),
                            "n": 1
                        }

                        # Call the actual image generation endpoint
                        logger.info(f"Calling Images API with payload: {image_payload}")
                        image_response = await make_api_request(
                            endpoint="/images/generations",
                            api_key=api_key,
                            json_data=image_payload
                        )

                        # Extract image data from response
                        # IMPORTANT: gpt-image-1 returns base64-encoded images, NOT URLs
                        image_data = None
                        image_b64 = None

                        if "data" in image_response and image_response["data"]:
                            first_image = image_response["data"][0]

                            # gpt-image-1 returns b64_json, not url
                            if "b64_json" in first_image:
                                image_b64 = first_image["b64_json"]
                                logger.info(f"Received base64 image data (length: {len(image_b64)} chars)")

                                # Save to Downloads folder for easy access
                                import tempfile
                                from pathlib import Path

                                # Get user's Downloads folder
                                downloads_dir = Path.home() / "Downloads"
                                downloads_dir.mkdir(exist_ok=True)

                                # Create unique filename with timestamp
                                from datetime import datetime
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f"openai_image_{timestamp}_{uuid4().hex[:8]}.png"
                                save_path = downloads_dir / filename

                                # Decode and save
                                save_path.write_bytes(base64.b64decode(image_b64))

                                image_data = {
                                    "save_path": str(save_path),
                                    "filename": filename,
                                    "b64_preview": image_b64[:100] + "..." if len(image_b64) > 100 else image_b64
                                }
                                logger.info(f"Image saved to: {save_path}")

                            # Fallback for url (shouldn't happen with gpt-image-1 but keeping for safety)
                            elif "url" in first_image:
                                logger.warning("Received URL instead of base64 (unexpected for gpt-image-1)")
                                image_data = {"url": first_image["url"]}

                        logger.info(f"Image extraction complete. Data available: {image_data is not None}")

                        return {
                            "conversation_id": conversation_id,
                            "response": response,
                            "image_response": image_response,
                            "image_data": image_data,
                            "tool_calls": assistant_message["tool_calls"],
                            "full_message": assistant_message
                        }

    return response

def format_response_markdown(data: Dict[str, Any], operation: str) -> str:
    """Format API response as markdown."""
    lines = [f"# Image {operation} Results\n"]
    lines.append("**Status:** ✅ Success\n")

    # Handle image_data (new field for base64 images)
    if "image_data" in data and data["image_data"]:
        img_data = data["image_data"]
        lines.append("## Generated Image\n")

        if "save_path" in img_data:
            lines.append(f"📁 **Image Saved:** `{img_data['save_path']}`")
            lines.append(f"**Filename:** `{img_data.get('filename', 'N/A')}`")
            lines.append("*Image saved to your Downloads folder. You can view it there!*\n")
        elif "url" in img_data:
            lines.append(f"🖼️ **Image URL:** {img_data['url']}\n")

    # Handle Responses API format
    if "conversation_id" in data:
        lines.append("\n## Continue Refining\n")
        lines.append(f"**Conversation ID:** `{data['conversation_id']}`")
        lines.append("*Provide this ID in your next request to refine this image further.*\n")

    # Check full_message for content
    if "full_message" in data:
        message = data["full_message"]
        if "content" in message and message["content"]:
            content = message["content"]
            if isinstance(content, str) and content.strip():
                lines.append("\n## Assistant Notes\n")
                lines.append(f"{content}\n")

    # Handle direct API format (fallback)
    if "data" in data:
        images = data["data"]
        lines.append(f"Generated **{len(images)}** image(s):\n")

        for i, img in enumerate(images, 1):
            if len(images) > 1:
                lines.append(f"## Image {i}\n")

            if "url" in img:
                lines.append(f"🖼️ **Image URL:** {img['url']}\n")
            elif "b64_json" in img:
                lines.append(f"🖼️ **Image:** Base64 encoded (length: {len(img['b64_json'])} chars)\n")

            if "revised_prompt" in img:
                lines.append(f"📝 **Revised Prompt:** {img['revised_prompt']}\n")

            # Store file ID if available
            if "file_id" in img:
                lines.append(f"📁 **File ID:** `{img['file_id']}`")
                lines.append("*Use this File ID for further refinements*\n")

    if "created" in data:
        created_time = datetime.fromtimestamp(data["created"]).strftime("%Y-%m-%d %H:%M:%S UTC")
        lines.append(f"\n⏰ **Created:** {created_time}")

    return "\n".join(lines)

def format_response_json(data: Dict[str, Any]) -> str:
    """Format API response as JSON."""
    # Truncate base64 data if present to avoid overwhelming output
    if "data" in data:
        for img in data["data"]:
            if "b64_json" in img and len(img["b64_json"]) > 100:
                img["b64_json"] = img["b64_json"][:100] + "...[truncated]"

    return json.dumps(data, indent=2)

# ============================
# MCP Tools
# ============================

@mcp.tool(name="openai_conversational_image")
async def openai_conversational_image(params: ConversationalImageInput):
    """Generate images conversationally with iterative refinement using GPT-Image-1.

    Enables multi-turn image creation where each prompt builds on previous results.
    Maintains conversation context for natural refinements like "make the sky darker"
    or "add more trees". Best for exploratory creative work requiring multiple iterations.

    Images are displayed inline in Claude Desktop and also saved to ~/Downloads/.

    Usage Pattern:
        1. Initial generation: "A cozy coffee shop interior"
           → Returns image inline and conversation_id
        2. Refine: "Add more plants and warmer lighting" (with same conversation_id)
           → Returns refined image inline
        3. Continue refining with the same conversation_id as needed

    When to Use:
        ✓ Exploratory creative work needing multiple iterations
        ✓ When desired result requires back-and-forth refinement
        ✓ Building complex scenes incrementally

    When Not to Use:
        ✗ Single well-defined requests (use openai_generate_image instead)

    Args:
        params: Input parameters including prompt, conversation ID, and optional input image.

    Returns:
        ImageContent that displays inline in Claude Desktop, with conversation metadata.
    """
    try:
        api_key = get_api_key(params.api_key)

        # Generate or use existing conversation ID
        conversation_id = params.conversation_id or generate_conversation_id()

        # Handle input image if provided
        input_file_id = params.input_image_file_id
        if params.input_image_path and not input_file_id:
            # Upload the image to get a file ID
            input_file_id = await upload_image_file(params.input_image_path, api_key)
            logger.info(f"Uploaded image with file ID: {input_file_id}")

        # Prepare image generation parameters (gpt-image-1 only supports size)
        image_params = {
            "size": params.size.value
        }

        # Call the Responses API
        result = await call_responses_api(
            prompt=params.prompt,
            api_key=api_key,
            conversation_id=conversation_id,
            assistant_model=params.assistant_model,
            input_image_file_id=input_file_id,
            image_params=image_params
        )

        # Check if we have image data
        if "image_response" in result and result["image_response"]:
            image_response = result["image_response"]
            if "data" in image_response and image_response["data"]:
                first_image = image_response["data"][0]
                if "b64_json" in first_image:
                    image_b64 = first_image["b64_json"]

                    # Save full-quality PNG to Downloads
                    downloads_dir = Path.home() / "Downloads"
                    downloads_dir.mkdir(exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"openai_image_{timestamp}_{uuid4().hex[:8]}.png"
                    save_path = downloads_dir / filename

                    # Decode and save full-quality PNG
                    img_bytes = base64.b64decode(image_b64)
                    save_path.write_bytes(img_bytes)

                    size_kb = len(img_bytes) / 1024
                    logger.info(f"Image saved to: {save_path} ({size_kb:.1f} KB)")
                    logger.info(f"Conversation ID: {conversation_id}")

                    # Return text with file path (no inline image display)
                    return f"""✅ **Image Generated Successfully**

📁 **File saved to:** `{save_path}`
📏 **Size:** {size_kb:.1f} KB
🔗 **Conversation ID:** `{conversation_id}`

To view the image, open the file from your Downloads folder.

To refine this image, just describe what you'd like to change (e.g., "make it darker", "add more detail") and I'll use the conversation context automatically."""

        # Fallback to text response if no image
        if params.output_format == OutputFormat.MARKDOWN:
            return format_response_markdown(result, "Conversational Generation")
        else:
            return format_response_json(result)

    except Exception as e:
        error_msg = f"Conversational image generation failed: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg, "success": False})

@mcp.tool(name="openai_generate_image")
async def openai_generate_image(params: GenerateImageInput):
    """Generate a single image from a text description using GPT-Image-1.

    Quick, single-request image generation for straightforward requests. Images are
    displayed inline in Claude Desktop and also saved to ~/Downloads/. For iterative
    refinement across multiple prompts, use openai_conversational_image instead.

    Supported sizes: 1024x1024 (square), 1024x1536 (portrait), 1536x1024 (landscape)

    Examples:
        • "A serene mountain lake at sunset, photorealistic style"
        • "Abstract geometric patterns in vibrant blues and purples"
        • "Minimalist tech company logo with circuit board patterns"
        • "A cozy reading nook with bookshelves and warm lighting"

    Args:
        params: Input parameters including prompt and optional size.

    Returns:
        ImageContent that displays inline in Claude Desktop.
    """
    try:
        # Convert to conversational parameters
        conv_params = ConversationalImageInput(
            prompt=params.prompt,
            size=params.size,
            output_format=params.output_format,
            api_key=params.api_key
        )
        return await openai_conversational_image(conv_params)

    except Exception as e:
        error_msg = f"Image generation failed: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg, "success": False})

@mcp.tool(name="openai_list_conversations")
async def openai_list_conversations() -> str:
    """List all active image generation conversations for session management.

    Shows conversation IDs and message history so you can continue refining
    images from previous requests. Useful when you need to find a conversation_id
    from an earlier session or see how many refinement iterations have occurred.

    Note: Conversations are stored in memory and cleared when the server restarts.

    Returns:
        JSON with active conversation count, IDs, message counts, and first prompts.
    """
    try:
        conversations = []
        for conv_id, messages in conversation_store.items():
            # Extract first prompt safely
            first_prompt = "Unknown"
            if messages and "content" in messages[0]:
                content = messages[0]["content"]
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "text":
                            first_prompt = item.get("text", "Unknown")[:100]
                            break

            conversations.append({
                "conversation_id": conv_id,
                "message_count": len(messages),
                "first_prompt": first_prompt
            })

        return json.dumps({
            "active_conversations": len(conversations),
            "conversations": conversations
        }, indent=2)

    except Exception as e:
        error_msg = f"Failed to list conversations: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg, "success": False})

# ============================
# Server Entry Point
# ============================

if __name__ == "__main__":
    import asyncio

    # Run the MCP server
    asyncio.run(mcp.run())
