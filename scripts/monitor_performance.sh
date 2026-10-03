#!/bin/bash

# Monitor development performance targets
# Run this script periodically to ensure we maintain our DevEx goals

echo "=== Development Performance Monitoring ==="
echo "Date: $(date)"
echo

echo "1. Code Linting Performance:"
time mise run lint:backend >/dev/null 2>&1
echo

echo "2. Unit Test Performance:"
time mise run test:unit >/dev/null 2>&1
echo

echo "3. Full Test Suite Performance:"
time mise run test:backend >/dev/null 2>&1
echo

echo "4. Type Checking Performance:"
time mise run typecheck:backend >/dev/null 2>&1
echo

echo "=== Performance Targets ==="
echo "✓ Code linting: Under 1 second"
echo "✓ Unit tests: Under 5 seconds"
echo "✓ All tests: Under 1 minute"
echo "✓ Type checking: Under 5 seconds"
echo
echo "See ADR-0030 for details"
