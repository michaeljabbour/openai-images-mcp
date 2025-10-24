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

# Import Phase 1 components
from dialogue_system import DialogueManager, DialogueMode, DialogueStage, DialogueQuestion
from prompt_enhancement import PromptEnhancer, ImageType
from storage import get_conversation_store
from image_verification import get_image_verifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================
# Helper Functions
# ============================

def get_downloads_directory() -> Path:
    """Get the appropriate downloads directory for images.

    Tries to use ~/Downloads/images/ for organization.
    If that directory already exists (user might be using it),
    falls back to ~/Downloads/images-mcp/ to avoid conflicts.
    """
    downloads_base = Path.home() / "Downloads"

    # Try preferred directory first
    preferred_dir = downloads_base / "images"
    fallback_dir = downloads_base / "images-mcp"

    # If preferred doesn't exist, create and use it
    if not preferred_dir.exists():
        preferred_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created images directory: {preferred_dir}")
        return preferred_dir

    # If preferred exists but is empty (we created it previously), use it
    if preferred_dir.is_dir() and not any(preferred_dir.iterdir()):
        return preferred_dir

    # If preferred exists and has non-openai-images content, use fallback
    # Check if directory has any files that aren't our openai_image_*.png pattern
    if preferred_dir.is_dir():
        files = list(preferred_dir.glob("*"))
        non_mcp_files = [f for f in files if not f.name.startswith("openai_image_")]

        if non_mcp_files:
            # User is using this directory for other stuff, use fallback
            fallback_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using fallback directory to avoid conflicts: {fallback_dir}")
            return fallback_dir

    # Default to preferred
    return preferred_dir

# Removed compression - always save full-quality PNG to organized Downloads folder

# Constants
API_BASE_URL = "https://api.openai.com/v1"
MAX_PROMPT_LENGTH = 4000
MAX_RETRIES = 3

# Initialize MCP server
mcp = FastMCP("openai_images_mcp")

# Store for conversation threads and file IDs (in-memory for quick access)
# Full conversations are persisted to disk via storage.py
conversation_store = {}
file_store = {}

# Initialize Phase 1 components
prompt_enhancer = PromptEnhancer()
storage = get_conversation_store()
image_verifier = get_image_verifier()

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
        extra='allow'  # Changed from 'forbid' to allow dialogue_responses
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

    # Phase 1: Dialogue System Parameters
    dialogue_mode: Optional[str] = Field(
        default="guided",
        description="Dialogue depth: 'quick' (1-2 questions), 'guided' (3-5 questions, recommended), 'explorer' (deep dive), 'skip' (direct generation)"
    )
    skip_dialogue: Optional[bool] = Field(
        default=False,
        description="Set to true to skip dialogue and generate immediately"
    )
    dialogue_responses: Optional[Dict[str, Any]] = Field(
        default=None,
        description="User responses to dialogue questions (internal use)"
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
        default=None,  # Will be auto-detected from prompt if not specified
        description="Image dimensions. Auto-detected if not specified. Options: 1024x1024 (square), 1024x1536 (portrait), 1536x1024 (landscape)."
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

                                # Store image data (actual save happens in tool function)
                                image_data = {
                                    "b64_json": image_b64,
                                    "b64_preview": image_b64[:100] + "..." if len(image_b64) > 100 else image_b64
                                }

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

    **USE THIS TOOL when:**
    - User gives a vague/incomplete prompt that needs refinement (e.g., "logo for my coffee shop")
    - User wants iterative refinement across multiple messages
    - User explicitly asks for guidance or suggestions

    Phase 1 Feature: Pre-generation dialogue system that guides you through questions
    to refine your vision before generating. Choose your dialogue depth:
    - "quick": 1-2 questions, fast path
    - "guided": 3-5 questions, balanced (DEFAULT - use if not specified)
    - "explorer": Deep exploration with 6+ questions
    - "skip": Direct generation, no dialogue (like openai_generate_image)

    Enables multi-turn image creation where each prompt builds on previous results.
    Maintains conversation context for natural refinements like "make the sky darker"
    or "add more trees". Best for exploratory creative work requiring multiple iterations.

    Images are displayed inline in Claude Desktop and also saved to ~/Downloads/images/
    (or ~/Downloads/images-mcp/ if images/ is already in use).

    Usage Pattern:
        1. Initial generation: "A cozy coffee shop interior"
           → System asks 3-5 dialogue questions (guided mode)
           → User answers to refine vision
           → Returns image inline and conversation_id
        2. Refine: "Add more plants and warmer lighting" (with same conversation_id)
           → No new dialogue, applies changes directly
           → Returns refined image inline
        3. Continue refining with the same conversation_id as needed

    When to Use:
        ✓ User provides vague/incomplete prompt like "create a logo" or "design a poster"
        ✓ Exploratory creative work needing multiple iterations
        ✓ When desired result requires back-and-forth refinement
        ✓ Building complex scenes incrementally

    When NOT to Use (use openai_generate_image instead):
        ✗ User provides detailed, complete prompt with all specifics
        ✗ User wants immediate generation without questions
        ✗ Prompt already includes style, colors, mood, composition details

    Args:
        params: Input parameters including prompt, conversation ID, and optional input image.

    Returns:
        ImageContent that displays inline in Claude Desktop, with conversation metadata.
    """
    try:
        api_key = get_api_key(params.api_key)

        # Generate or use existing conversation ID
        conversation_id = params.conversation_id or generate_conversation_id()

        # Load existing conversation from storage if available
        stored_conversation = storage.load_conversation(conversation_id)
        if stored_conversation:
            logger.info(f"Loaded existing conversation: {conversation_id}")

        # Phase 1: Check if dialogue is needed
        dialogue_mode_str = params.dialogue_mode or "guided"
        needs_dialogue = (
            dialogue_mode_str != "skip" and
            not params.skip_dialogue and
            not params.input_image_file_id  # Skip dialogue for refinements
        )

        if needs_dialogue:
            # Initialize dialogue manager
            try:
                dialogue_mode = DialogueMode(dialogue_mode_str.lower())
            except ValueError:
                dialogue_mode = DialogueMode.GUIDED

            dialogue_manager = DialogueManager(dialogue_mode)

            # Get dialogue responses from params or stored conversation
            dialogue_responses = params.dialogue_responses or {}
            if stored_conversation and "metadata" in stored_conversation:
                stored_responses = stored_conversation["metadata"].get("dialogue_responses", {})
                # Merge stored responses with new ones
                dialogue_responses = {**stored_responses, **dialogue_responses}

            # Get next question
            next_question = dialogue_manager.get_next_question(
                params.prompt,
                dialogue_responses
            )

            if next_question:
                # Still have questions - return question to user
                progress = dialogue_manager.get_stage_progress()

                # Save dialogue state to storage
                messages = stored_conversation.get("messages", []) if stored_conversation else []
                messages.append({
                    "role": "assistant",
                    "content": next_question.question,
                    "timestamp": datetime.now().isoformat(),
                    "stage": next_question.stage.value
                })

                storage.save_conversation(
                    conversation_id,
                    messages,
                    metadata={
                        "dialogue_mode": dialogue_mode_str,
                        "dialogue_responses": dialogue_responses,
                        "original_prompt": params.prompt,
                        "current_stage": next_question.stage.value
                    }
                )

                # Format question for user
                response_lines = [
                    f"## 💬 Let's Refine Your Vision",
                    f"",
                    f"**Progress:** {progress['completed_stages']}/{progress['total_stages']} questions ({progress['progress_percent']}%)",
                    f"**Stage:** {next_question.stage.value.replace('_', ' ').title()}",
                    f"",
                    f"### {next_question.question}",
                ]

                if next_question.options:
                    response_lines.append("")
                    response_lines.append("**Options:**")
                    for i, option in enumerate(next_question.options, 1):
                        response_lines.append(f"{i}. {option}")
                    response_lines.append("")
                    response_lines.append("*You can choose an option or provide your own answer.*")

                if next_question.context:
                    response_lines.append("")
                    response_lines.append(f"💡 **Why this matters:** {next_question.context}")

                response_lines.extend([
                    "",
                    f"🔗 **Conversation ID:** `{conversation_id}`",
                    "",
                    "*Once you answer, I'll continue with the next question or generate your image if we're done!*"
                ])

                return "\n".join(response_lines)

            # Dialogue complete - build enhanced prompt
            logger.info(f"Dialogue complete. Building enhanced prompt...")
            enhanced_prompt = dialogue_manager.build_enhanced_prompt(
                params.prompt,
                dialogue_responses
            )
            logger.info(f"Enhanced prompt: {enhanced_prompt}")

            # Use enhanced prompt for generation
            prompt_to_use = enhanced_prompt

            # Save dialogue completion to storage
            messages = stored_conversation.get("messages", []) if stored_conversation else []
            messages.append({
                "role": "assistant",
                "content": f"Dialogue complete! Generating image with enhanced prompt...",
                "timestamp": datetime.now().isoformat()
            })

            storage.save_conversation(
                conversation_id,
                messages,
                metadata={
                    "dialogue_mode": dialogue_mode_str,
                    "dialogue_responses": dialogue_responses,
                    "original_prompt": params.prompt,
                    "enhanced_prompt": enhanced_prompt,
                    "dialogue_complete": True
                }
            )
        else:
            # No dialogue - use original prompt
            prompt_to_use = params.prompt
            logger.info("Skipping dialogue, using original prompt")

        # Auto-detect image size if not specified
        if params.size is None:
            # Detect image type and suggest size
            image_type = prompt_enhancer.detect_image_type(prompt_to_use)
            suggested_size_str = prompt_enhancer.suggest_size_from_type(image_type, prompt_to_use)
            # Convert string to ImageSize enum
            size_map = {
                "1024x1024": ImageSize.SIZE_1024x1024,
                "1024x1536": ImageSize.SIZE_1024x1536,
                "1536x1024": ImageSize.SIZE_1536x1024
            }
            params.size = size_map.get(suggested_size_str, ImageSize.SIZE_1024x1024)
            logger.info(f"Auto-detected size: {params.size.value} for image type: {image_type.value}")

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
            prompt=prompt_to_use,
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

                    # Save full-quality PNG to organized Downloads folder
                    downloads_dir = get_downloads_directory()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"openai_image_{timestamp}_{uuid4().hex[:8]}.png"
                    save_path = downloads_dir / filename

                    # Decode and save full-quality PNG
                    img_bytes = base64.b64decode(image_b64)
                    save_path.write_bytes(img_bytes)

                    size_kb = len(img_bytes) / 1024
                    logger.info(f"Image saved to: {save_path} ({size_kb:.1f} KB)")
                    logger.info(f"Conversation ID: {conversation_id}")

                    # Phase 1: Verify image quality before returning
                    logger.info("Verifying generated image quality...")
                    verification = image_verifier.verify_image(
                        image_path=str(save_path),
                        original_prompt=params.prompt,
                        enhanced_prompt=prompt_to_use if 'prompt_to_use' in locals() else params.prompt,
                        dialogue_responses=dialogue_responses if 'dialogue_responses' in locals() else None,
                        image_type=image_type.value if 'image_type' in locals() else None
                    )
                    logger.info(f"Verification result: passed={verification.passed}, confidence={verification.confidence}")

                    # Save image info to storage (including verification)
                    image_info = {
                        "filename": filename,
                        "path": str(save_path),
                        "size_kb": round(size_kb, 1),
                        "timestamp": timestamp,
                        "size": params.size.value,
                        "prompt_used": prompt_to_use if 'prompt_to_use' in locals() else params.prompt,
                        "verification": {
                            "passed": verification.passed,
                            "confidence": verification.confidence,
                            "issues": verification.issues,
                            "timestamp": verification.timestamp
                        }
                    }

                    # Add to conversation storage
                    storage.add_generated_image(conversation_id, image_info)
                    logger.info(f"Image info saved to conversation storage")

                    # Build response message
                    response_parts = [
                        "✅ **Image Generated Successfully**",
                        "",
                        f"📁 **File saved to:** `{save_path}`",
                        f"📏 **Size:** {size_kb:.1f} KB",
                        f"🔗 **Conversation ID:** `{conversation_id}`",
                    ]

                    # Add verification report
                    if verification:
                        response_parts.extend([
                            "",
                            verification.analysis
                        ])

                        # Add warnings if issues detected
                        if verification.issues:
                            response_parts.extend([
                                "",
                                "⚠️ **Issues Detected:**"
                            ])
                            for issue in verification.issues:
                                response_parts.append(f"  • {issue}")

                    # Add dialogue info if dialogue was used
                    if needs_dialogue and 'enhanced_prompt' in locals():
                        quality_score = prompt_enhancer.analyze_prompt_quality(params.prompt)
                        response_parts.extend([
                            "",
                            "### 🎨 Prompt Enhancement",
                            f"**Original prompt quality:** {quality_score.score}/100",
                            f"**Enhanced with dialogue responses**",
                            "",
                            f"*Your answers helped create a more detailed prompt for better results!*"
                        ])

                    response_parts.extend([
                        "",
                        "To view the image, open the file from your Downloads folder.",
                        "",
                        "To refine this image, just describe what you'd like to change (e.g., \"make it darker\", \"add more detail\") and I'll use the conversation context automatically."
                    ])

                    return "\n".join(response_parts)

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

    **USE THIS TOOL when the user provides a detailed, well-defined prompt and wants direct generation.**
    NO dialogue questions will be asked. Image generates immediately.

    Quick, single-request image generation for straightforward requests. Images are
    displayed inline in Claude Desktop and also saved to ~/Downloads/images/ (or
    ~/Downloads/images-mcp/ if images/ is already in use). For iterative refinement
    across multiple prompts, use openai_conversational_image instead.

    Supported sizes: 1024x1024 (square), 1024x1536 (portrait), 1536x1024 (landscape)

    Examples of well-defined prompts (use this tool):
        • "A serene mountain lake at sunset, photorealistic style, golden hour lighting"
        • "Abstract geometric patterns in vibrant blues and purples, sharp edges"
        • "Minimalist tech company logo with circuit board patterns, clean design"
        • "TRON movie style scene, neon cyan and magenta, digital grid, cinematic"

    Args:
        params: Input parameters including prompt and optional size.

    Returns:
        ImageContent that displays inline in Claude Desktop.
    """
    try:
        # Convert to conversational parameters (skip dialogue for simple tool)
        conv_params = ConversationalImageInput(
            prompt=params.prompt,
            size=params.size,
            output_format=params.output_format,
            api_key=params.api_key,
            skip_dialogue=True  # Force direct generation without dialogue
        )
        return await openai_conversational_image(conv_params)

    except Exception as e:
        error_msg = f"Image generation failed: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg, "success": False})

@mcp.tool(name="openai_list_conversations")
async def openai_list_conversations() -> str:
    """List all saved image generation conversations for session management.

    Phase 1 Feature: Shows conversation IDs, message history, dialogue progress, and
    generated images from persistent local storage. Conversations persist across
    server restarts and are stored in ~/.openai-images-mcp/conversations/

    Useful for:
    - Finding a conversation_id from an earlier session
    - Seeing how many refinement iterations occurred
    - Tracking dialogue mode and responses
    - Viewing generated images history

    Returns:
        JSON with conversation summaries including IDs, message counts, first prompts,
        dialogue info, and generated images.
    """
    try:
        # Get recent conversations from persistent storage
        recent_conversations = storage.get_recent_conversations(limit=20)

        # Also include in-memory conversations that haven't been persisted yet
        in_memory_conv_ids = set(conversation_store.keys())
        persisted_conv_ids = set(conv["conversation_id"] for conv in recent_conversations)

        # Add in-memory conversations not yet persisted
        for conv_id in in_memory_conv_ids - persisted_conv_ids:
            messages = conversation_store[conv_id]
            # Extract first prompt safely
            first_prompt = "Unknown"
            if messages and "content" in messages[0]:
                content = messages[0]["content"]
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "text":
                            first_prompt = item.get("text", "Unknown")[:100]
                            break

            recent_conversations.append({
                "conversation_id": conv_id,
                "message_count": len(messages),
                "first_prompt": first_prompt,
                "dialogue_mode": None,
                "has_images": False,
                "updated_at": None,
                "source": "in-memory (not yet persisted)"
            })

        # Get storage stats
        stats = storage.get_storage_stats()

        return json.dumps({
            "total_conversations": stats["total_conversations"],
            "storage_size_mb": stats["total_size_mb"],
            "storage_directory": stats["storage_directory"],
            "recent_conversations": recent_conversations
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
