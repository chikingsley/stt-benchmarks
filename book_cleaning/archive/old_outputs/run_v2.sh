#!/bin/bash
# Run Book Formatter V2 with proper paths

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root to ensure Poetry can find pyproject.toml
cd "$PROJECT_ROOT"

# Run the formatter with all arguments passed through
poetry run python "$SCRIPT_DIR/book_formatter_v2.py" "$@"