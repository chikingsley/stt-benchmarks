#!/usr/bin/env python3
"""
Precise formatter with exact preservation instructions
"""

import os
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from book_cleaning.book_formatter_v2 import BookFormatterV2

class PreciseFormatter(BookFormatterV2):
    def create_enhanced_formatting_prompt(self, config):
        """Create very precise formatting prompt"""
        
        book_info = config.get('book_info', {})
        
        prompt = f"""You are formatting a {book_info.get('type', 'textbook')} in {book_info.get('language', 'unknown language')}.

CRITICAL PRESERVATION RULES:
1. **DO NOT ADD TRANSLATIONS** - Only include translations that are already in the source
2. **PRESERVE EXACT STRUCTURE** - Do not reorder, reorganize, or "improve" the content
3. **MAINTAIN ORIGINAL ORDER** - Keep exercises, dialogues, and sections in exact original sequence

EXACT FORMATTING RULES:

1. **French sentences with verbs**:
   - Format: **Elle _habite_ en Angleterre**
   - The verb should be italicized WITHIN the bold: _verb_

2. **Simple examples**:
   - Statement: **Vous êtes français.** (statement)
   - Question: **Vous êtes français?** (question)
   - NO translations unless already present

3. **Section headers**:
   - Use ### for subsections like "Giving more information about yourself"
   - Do NOT add "Language points -" prefix to subsections

4. **Exercises**:
   - Keep EXACT original numbering
   - Do NOT add translations to exercise questions
   - Preserve the two groups as separate

5. **Dialogues**:
   - Keep speaker order EXACTLY as in source
   - French dialogue first, then English translation block
   - Simple format: SPEAKER: Text

6. **Verb lists**:
   - Format: **téléphoner** to phone (on same line)
   - NOT bullet points

7. **Grammar explanations**:
   - Bold key terms: **-er**, **je**, **tu**, etc.
   - Simple conjugation lists, not tables

CRITICAL: You are a FORMATTER, not a translator or editor. PRESERVE the exact content and structure.

Format this text:"""
        
        return prompt


def main():
    # Check API key
    if not os.getenv("MISTRAL_API_KEY"):
        print("❌ Please set MISTRAL_API_KEY environment variable")
        return
    
    # Paths
    pdf_path = Path("Colloquial French 1.pdf").resolve()
    config_path = Path("improved_config.yaml").resolve()
    
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
        
    if not config_path.exists():
        print(f"❌ Config not found: {config_path}")
        return
    
    print(f"📄 PDF: {pdf_path}")
    print(f"📋 Config: {config_path}")
    
    # Create precise formatter
    formatter = PreciseFormatter(pdf_path, "./formatted_output")
    
    # Test same pages with precise instructions
    result = formatter.process_with_pipeline(
        mode="sample",
        start_page=20,
        end_page=22,
        config_path=str(config_path),
        preview=False
    )
    
    print(f"✅ Precise result: {result}")

if __name__ == "__main__":
    main()