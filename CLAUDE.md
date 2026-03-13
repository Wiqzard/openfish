# Development Guidelines

This document contains critical information about working with this codebase. Follow these guidelines precisely.

## Core Development Rules

1. Package Management
   - ONLY use `uv`, NEVER `pip`
   - Install and update dependencies with `uv add` / `uv add --dev`
   - Sync the environment with `uv sync --dev`
   - Run tools with `uv run --frozen <tool>`
   - Update locked packages with `uv lock --upgrade-package <package>`
   - Commit `uv.lock` when dependencies change
   - FORBIDDEN: `pip install`, `uv pip install`, `@latest` syntax

2. Code Quality
   - Type hints are required for all new or modified Python code
   - Public APIs must have docstrings
   - Functions must stay focused and small
   - Follow existing patterns before introducing new abstractions
   - Maximum line length: 120 characters
   - FORBIDDEN: imports inside functions

3. Testing Requirements
   - Main test command: `uv run --frozen pytest`
   - Async tests must use `anyio`, not `asyncio.run()`
   - Prefer function-based tests, not `Test*` classes
   - Cover edge cases and error paths
   - New features require tests
   - Bug fixes require regression tests
   - Prefer minimal end-to-end tests over overly mocked internals
   - When testing MCP behavior, prefer exercising the actual MCP tool surface when practical
   - Wrap indefinite async waits in `anyio.fail_after(5)` to avoid hangs
   - Avoid fixed sleeps unless the behavior under test is explicitly time-based

4. Commit Discipline
   - After each major change, run the relevant checks first
   - If tests pass, create a commit and push it to the remote before moving to the next major change
   - For user-reported bug fixes or features, add `git commit --trailer "Reported-by:<name>"`
   - For GitHub issue work, add `git commit --trailer "Github-Issue:#<number>"`
   - NEVER add `co-authored-by` or mention tooling in commit messages or pull requests

## Repo Commands

- Open the command deck: `uv run --frozen openfish`
- Start the web app: `uv run --frozen openfish ui`
- Start the MCP server: `uv run --frozen openfish mcp`
- Start the dummy VLM server: `uv run --frozen openfish dummy-vlm`
- Run the config doctor: `uv run --frozen openfish doctor`
- Run tests: `uv run --frozen pytest`
- Format: `uv run --frozen ruff format .`
- Lint: `uv run --frozen ruff check .`
- Type check: `uv run --frozen pyright`
- Run hooks: `uv run --frozen pre-commit run --all-files`

## Tooling

1. Ruff
   - Format with `uv run --frozen ruff format .`
   - Lint with `uv run --frozen ruff check .`
   - Auto-fix with `uv run --frozen ruff check . --fix`
   - The repo uses import sorting through Ruff

2. Pyright
   - Run `uv run --frozen pyright`
   - Keep the checked scope focused on OpenFish code, not bundled third-party resources

3. Pre-commit
   - Config lives in `.pre-commit-config.yaml`
   - Install hooks with `uv run --frozen pre-commit install`
   - Run all hooks with `uv run --frozen pre-commit run --all-files`

## Error Handling

- Use specific exceptions where possible
- Prefer `logger.exception()` over `logger.error()` when logging caught exceptions
- Avoid `except Exception:` unless it is a true top-level boundary

## Licensing

- This repository currently uses a restrictive source-available license in `LICENSE`
- Do not describe the repo as open source while this license is in place
