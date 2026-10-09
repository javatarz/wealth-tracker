# 29. Linting and Testing Improvements for Faster Feedback

Date: 2026-10-03

## Status

Accepted

## Context

The project needed faster linting and testing feedback for developers and AI agents while maintaining high code quality standards. The existing setup was comprehensive but could be optimized for speed without sacrificing quality.

## Decision

We will optimize the linting and testing pipeline with the following improvements:

### 1. Parallel Test Execution
- Added `pytest-xdist` for parallel test execution
- Added test markers to distinguish fast unit tests from slower integration tests
- Added specific commands for running only fast tests (`mise run test:unit`, `mise run test:quick`)

### 2. Optimized Type Checking
- Kept strict mypy for comprehensive type checking
- Configured mypy caching for better performance
- (Future) Will evaluate ruff's type checking when it becomes available

### 3. Test Coverage Requirements
- Added `pytest-cov` with 80% coverage requirement
- Configured coverage reporting to show missing lines

### 4. Performance Optimizations
- Added caching directories for ruff and mypy
- Optimized pre-commit hooks for faster local feedback
- Added require_serial flag to mypy hook to prevent conflicts

## Consequences

### Positive
- Test execution is now parallelized, significantly reducing test run time
- Developers and AI agents get faster feedback with unit test filtering
- Test coverage is now enforced, improving code quality
- Clear distinction between fast unit tests and slower integration tests
- MyPy caching improves type checking performance

### Negative
- Slightly more complex configuration
- Additional dependencies added to the project

## Commands

Fast feedback commands for development:
- `mise run test:unit` - Run only fast unit tests
- `mise run test:quick` - Run all tests with minimal output
- `mise run lint:backend` - Run ruff linting and formatting

Comprehensive checks:
- `mise run test:backend` - Run all tests with coverage
- `mise run typecheck:backend` - Strict mypy type checking
- `mise run check` - Full quality gate including all checks
