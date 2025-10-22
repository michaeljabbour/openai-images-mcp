#!/usr/bin/env python3
"""
Local Testing Script for OpenAI Images MCP Server

This script allows you to test the MCP server functionality locally
without needing Claude Desktop. It directly calls the tool functions
with mock or real API calls.
"""

import asyncio
import json
import os
from openai_images_mcp import (
    openai_generate_image,
    openai_conversational_image,
    openai_list_conversations,
    GenerateImageInput,
    ConversationalImageInput,
    ImageSize,
    OutputFormat
)

# ANSI color codes for pretty output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} {text}")

def print_error(text):
    print(f"{Colors.FAIL}✗{Colors.ENDC} {text}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ{Colors.ENDC} {text}")

def print_result(result):
    print(f"\n{Colors.OKBLUE}Result:{Colors.ENDC}")
    print(result)

async def test_api_key_check():
    """Test 1: Check if API key is configured"""
    print_header("Test 1: API Key Configuration")

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print_success(f"API key found (length: {len(api_key)} chars)")
        print_info(f"Key prefix: {api_key[:10]}...")
        return True
    else:
        print_error("API key not found in environment!")
        print_info("Set it with: export OPENAI_API_KEY='your-key-here'")
        return False

async def test_simple_generation():
    """Test 2: Simple single-shot image generation"""
    print_header("Test 2: Simple Image Generation")

    try:
        print_info("Generating image: 'A red apple on a wooden table'")

        params = GenerateImageInput(
            prompt="A red apple on a wooden table, photorealistic",
            size=ImageSize.SIZE_1024x1024,
            output_format=OutputFormat.MARKDOWN
        )

        result = await openai_generate_image(params)

        # Check if it's an error
        if '"error"' in result:
            print_error("Generation failed!")
            print_result(result)
            return False
        else:
            print_success("Image generated successfully!")
            print_result(result)

            # Try to extract temp file path
            if "temp_path" in result or "/tmp/" in result or "/var/" in result:
                print_success("Temporary file created")

            return True

    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_conversational_refinement():
    """Test 3: Conversational image refinement"""
    print_header("Test 3: Conversational Image Refinement")

    try:
        # Step 1: Initial generation
        print_info("Step 1: Initial generation - 'A mountain landscape at sunset'")

        params1 = ConversationalImageInput(
            prompt="A mountain landscape at sunset",
            size=ImageSize.SIZE_1024x1024,
            output_format=OutputFormat.MARKDOWN
        )

        result1 = await openai_conversational_image(params1)

        if '"error"' in result1:
            print_error("Initial generation failed!")
            print_result(result1)
            return False

        print_success("Initial image generated")

        # Extract conversation ID
        conversation_id = None
        if "conversation_id" in result1:
            # Parse the result to find conversation_id
            import re
            match = re.search(r'`(conv_[a-f0-9]+)`', result1)
            if match:
                conversation_id = match.group(1)
                print_success(f"Conversation ID: {conversation_id}")

        if not conversation_id:
            print_error("Could not extract conversation_id from result")
            print_result(result1)
            return False

        # Step 2: Refinement
        print_info("Step 2: Refining - 'Add more dramatic clouds'")

        params2 = ConversationalImageInput(
            prompt="Add more dramatic clouds and make the colors warmer",
            conversation_id=conversation_id,
            size=ImageSize.SIZE_1024x1024,
            output_format=OutputFormat.MARKDOWN
        )

        result2 = await openai_conversational_image(params2)

        if '"error"' in result2:
            print_error("Refinement failed!")
            print_result(result2)
            return False

        print_success("Image refined successfully!")
        print_result(result2)

        # Step 3: List conversations
        print_info("Step 3: Listing conversations")
        result3 = await openai_list_conversations()
        print_success("Conversations listed")
        print_result(result3)

        return True

    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_parameter_validation():
    """Test 4: Parameter validation"""
    print_header("Test 4: Parameter Validation")

    try:
        # Test 1: Empty prompt
        print_info("Testing empty prompt (should fail)...")
        try:
            params = GenerateImageInput(prompt="")
            print_error("Validation should have failed but didn't!")
            return False
        except Exception as e:
            print_success(f"Correctly rejected empty prompt: {type(e).__name__}")

        # Test 2: Too long prompt
        print_info("Testing overly long prompt (should fail)...")
        try:
            params = GenerateImageInput(prompt="x" * 5000)
            print_error("Validation should have failed but didn't!")
            return False
        except Exception as e:
            print_success(f"Correctly rejected long prompt: {type(e).__name__}")

        # Test 3: Valid prompt
        print_info("Testing valid prompt...")
        params = GenerateImageInput(prompt="Test image")
        print_success("Valid prompt accepted")

        return True

    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_all():
    """Run all tests"""
    print_header("OpenAI Images MCP Server - Local Testing Suite")

    results = {}

    # Test 1: API Key
    results['api_key'] = await test_api_key_check()

    if not results['api_key']:
        print_error("\nCannot proceed without API key. Please set OPENAI_API_KEY environment variable.")
        return

    # Test 2: Simple generation (costs money, so make it optional)
    print_info("\n" + "=" * 70)
    response = input(f"{Colors.WARNING}Test 2 will make an actual API call (costs money). Continue? (y/N): {Colors.ENDC}")
    if response.lower() == 'y':
        results['simple_generation'] = await test_simple_generation()
    else:
        print_info("Skipping Test 2")
        results['simple_generation'] = None

    # Test 3: Conversational refinement (costs money)
    if results.get('simple_generation'):
        print_info("\n" + "=" * 70)
        response = input(f"{Colors.WARNING}Test 3 will make multiple API calls (costs more money). Continue? (y/N): {Colors.ENDC}")
        if response.lower() == 'y':
            results['conversational'] = await test_conversational_refinement()
        else:
            print_info("Skipping Test 3")
            results['conversational'] = None

    # Test 4: Parameter validation (free, always run)
    results['validation'] = await test_parameter_validation()

    # Summary
    print_header("Test Summary")

    for test_name, result in results.items():
        if result is True:
            print_success(f"{test_name}: PASSED")
        elif result is False:
            print_error(f"{test_name}: FAILED")
        else:
            print_info(f"{test_name}: SKIPPED")

    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)

    print(f"\n{Colors.BOLD}Total: {passed} passed, {failed} failed, {skipped} skipped{Colors.ENDC}\n")

if __name__ == "__main__":
    print(f"{Colors.BOLD}OpenAI Images MCP Server - Local Test Suite{Colors.ENDC}")
    print(f"{Colors.BOLD}Version: 3.0.0{Colors.ENDC}\n")

    try:
        asyncio.run(test_all())
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Tests interrupted by user{Colors.ENDC}")
    except Exception as e:
        print_error(f"Test suite failed: {e}")
        import traceback
        traceback.print_exc()
