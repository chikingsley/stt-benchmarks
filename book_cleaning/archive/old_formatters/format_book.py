#!/usr/bin/env python3
"""
Simple wrapper for book_formatter_v2.py with better path handling
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import and run the main function
from book_cleaning.book_formatter_v2 import main

if __name__ == "__main__":
    main()