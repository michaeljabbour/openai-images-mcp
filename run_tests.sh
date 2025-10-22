#!/bin/bash
# Test runner for OpenAI Images MCP Server

echo "🧪 Running Phase 1 Tests for OpenAI Images MCP Server"
echo "=================================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing test requirements..."
    pip install -r requirements-test.txt
fi

# Run tests with different verbosity levels based on argument
if [ "$1" == "quick" ]; then
    echo "🏃 Running quick test suite (unit tests only)..."
    pytest tests/test_dialogue_system.py tests/test_prompt_enhancement.py tests/test_storage.py -v
elif [ "$1" == "coverage" ]; then
    echo "📊 Running tests with coverage report..."
    pytest tests/ --cov=. --cov-report=html --cov-report=term
elif [ "$1" == "integration" ]; then
    echo "🔗 Running integration tests only..."
    pytest tests/test_integration.py -v
else
    echo "🎯 Running all tests..."
    pytest tests/ -v
fi

echo ""
echo "✅ Test run complete!"
