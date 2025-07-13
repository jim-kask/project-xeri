#!/usr/bin/env bash

# Script to run all tests for the Xeri Chat application

echo "Running tests for Xeri Chat application..."
echo "----------------------------------------"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python tests/setup_tests.py
else
    source venv/bin/activate
fi

# Run the tests with coverage
echo "Running tests with coverage..."
python -m pytest --cov=xeri --cov-report=term-missing -v

# Check if tests passed
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ All tests passed!${NC}"
    echo -e "\nGenerating HTML coverage report..."
    python -m pytest --cov=xeri --cov-report=html
    echo -e "Coverage report generated in htmlcov/ directory"
else
    echo -e "\n${RED}❌ Tests failed!${NC}"
    exit 1
fi

echo -e "\nTests completed successfully!"
