#!/usr/bin/env python3
"""
Simple test script for V2 formatter
"""

import os
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from book_cleaning.book_formatter_v2 import BookFormatterV2

def main():
    # Check API key
    if not os.getenv("MISTRAL_API_KEY"):
        print("❌ Please set MISTRAL_API_KEY environment variable")
        return
    
    # Paths
    pdf_path = Path("Colloquial French 1.pdf").resolve()
    config_path = Path("formatted_output/session_20250619_053709/generated_config.yaml").resolve()
    
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
        
    if not config_path.exists():
        print(f"❌ Config not found: {config_path}")
        return
    
    print(f"📄 PDF: {pdf_path}")
    print(f"📋 Config: {config_path}")
    
    # Create formatter
    formatter = BookFormatterV2(pdf_path, "./formatted_output")
    
    # Test sample pages
    result = formatter.process_with_pipeline(
        mode="sample",
        start_page=20,
        end_page=22,
        config_path=str(config_path),
        preview=False
    )
    
    print(f"✅ Result: {result}")

if __name__ == "__main__":
    main()