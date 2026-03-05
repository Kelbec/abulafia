#!/bin/bash
# Quick test runner for Abulafia Test Suite (Linux/Mac)

echo "=========================================="
echo "  Abulafia Test Suite Runner"
echo "=========================================="
echo

# Activate virtual environment if it exists
if [ -f venv/bin/activate ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -f .venv/bin/activate ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "No virtual environment found, using system Python"
fi

echo
echo "Running test suite..."
echo

python test_suite.py

echo
echo "=========================================="
echo "  Test run complete"
echo "=========================================="
