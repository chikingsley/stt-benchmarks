#!/usr/bin/env python3
"""
Mistral OCR with page-by-page processing for better layout handling
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime
from mistralai import Mistral
from alive_progress import alive_bar
import base64
from dotenv import load_dotenv

class MistralPageProcessor:
    def __init__(self, pdf_path, output_dir="./formatted_output"):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # API setup
        load_dotenv()
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY environment variable required")
        
        self.client = Mistral(api_key=api_key)
        
        # Session setup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"mistral_pages_{timestamp}"
        self.session_dir.mkdir(exist_ok=True)
        
    def encode_pdf(self):
        """Encode PDF for OCR"""
        try:
            with open(self.pdf_path, "rb") as pdf_file:
                return base64.b64encode(pdf_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding PDF: {e}")
            return None
    
    def ocr_specific_pages(self, page_numbers):
        """OCR specific pages with structured output"""
        
        # Check file size
        file_size_mb = self.pdf_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 50:
            print(f"⚠️ PDF size ({file_size_mb:.1f}MB) exceeds 50MB limit")
            return None
        
        base64_pdf = self.encode_pdf()
        if not base64_pdf:
            return None
        
        print(f"🔍 OCR processing pages {page_numbers} ({file_size_mb:.1f}MB)")
        
        try:
            # Use structured output to better handle layout
            ocr_response = self.client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{base64_pdf}"
                },
                pages=[p - 1 for p in page_numbers],  # Convert to 0-based indexing
                include_image_base64=False,
                # Try structured output for better layout handling
                document_annotation_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "textbook_structure",
                        "description": "Extract structured content from language textbook",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "sections": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "type": {"type": "string", "enum": ["language_points", "dialogue", "exercise", "grammar", "vocabulary"]},
                                            "title": {"type": "string"},
                                            "content": {"type": "string"},
                                            "page": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            )
            
            print(f"✅ OCR complete! Processed {len(ocr_response.pages)} pages")
            return ocr_response
            
        except Exception as e:
            print(f"❌ Structured OCR failed: {e}")
            # Fallback to regular OCR
            try:
                ocr_response = self.client.ocr.process(
                    model="mistral-ocr-latest",
                    document={
                        "type": "document_url",
                        "document_url": f"data:application/pdf;base64,{base64_pdf}"
                    },
                    pages=[p - 1 for p in page_numbers],
                    include_image_base64=False
                )
                print(f"✅ Fallback OCR complete! Processed {len(ocr_response.pages)} pages")
                return ocr_response
            except Exception as e2:
                print(f"❌ OCR failed completely: {e2}")
                return None
    
    def format_with_mistral(self, ocr_text):
        """Format OCR output using Mistral formatting model"""
        
        format_prompt = """Format this French textbook content with these EXACT rules:

FORMATTING RULES:
1. **French examples**: **Elle _habite_ en Angleterre** (verb italicized within bold)
2. **Section headers**: ## Language points - Topic, ### Exercise N
3. **Grammatical terms**: **je**, **tu**, **-er** etc.
4. **Preserve exact content order** - no reorganizing
5. **Keep original exercise numbering** - don't fix what looks wrong
6. **Simple dialogue format**: SPEAKER: Text

CRITICAL: You are a FORMATTER only. Do not add translations, reorganize, or "fix" content.

Text to format:"""
        
        try:
            response = self.client.chat.complete(
                model="mistral-medium-latest",
                messages=[
                    {"role": "system", "content": format_prompt},
                    {"role": "user", "content": ocr_text}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Formatting failed: {e}")
            return ocr_text
    
    def process_pages(self, start_page, end_page=None):
        """Process specific page range"""
        
        if end_page is None:
            end_page = start_page + 2  # Default 3 pages
        
        page_numbers = list(range(start_page, end_page + 1))
        
        print(f"🚀 Mistral Page-by-Page Processor")
        print(f"📄 PDF: {self.pdf_path.name}")
        print(f"📖 Pages: {start_page}-{end_page}")
        
        # OCR specific pages
        ocr_response = self.ocr_specific_pages(page_numbers)
        if not ocr_response:
            return None
        
        # Combine page content
        combined_text = "\n\n".join([
            f"=== PAGE {page.index + 1} ===\n{page.markdown}"
            for page in ocr_response.pages
        ])
        
        # Save raw OCR
        raw_file = self.session_dir / "raw_ocr_pages.md"
        with open(raw_file, 'w', encoding='utf-8') as f:
            f.write(combined_text)
        
        # Format with Mistral
        print("🎨 Formatting with Mistral...")
        formatted_text = self.format_with_mistral(combined_text)
        
        # Save formatted result
        formatted_file = self.session_dir / f"{self.pdf_path.stem}_page_formatted.md"
        with open(formatted_file, 'w', encoding='utf-8') as f:
            f.write(formatted_text)
        
        # Save detailed OCR data
        ocr_file = self.session_dir / "detailed_ocr.json"
        with open(ocr_file, 'w', encoding='utf-8') as f:
            json.dump({
                "pages": [
                    {
                        "index": page.index,
                        "markdown": page.markdown,
                        "dimensions": page.dimensions.__dict__ if hasattr(page, 'dimensions') else {}
                    }
                    for page in ocr_response.pages
                ]
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Processing complete!")
        print(f"📄 Raw OCR: {raw_file}")
        print(f"🎨 Formatted: {formatted_file}")
        print(f"📊 Details: {ocr_file}")
        
        return formatted_file


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Mistral OCR Page-by-Page Processor")
    parser.add_argument("pdf_file", help="Input PDF file")
    parser.add_argument("--start-page", type=int, default=20, help="Start page")
    parser.add_argument("--end-page", type=int, default=22, help="End page")
    
    args = parser.parse_args()
    
    load_dotenv()
    if not os.getenv("MISTRAL_API_KEY"):
        print("❌ Please set MISTRAL_API_KEY environment variable")
        return
    
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    processor = MistralPageProcessor(pdf_path)
    result = processor.process_pages(args.start_page, args.end_page)
    
    if result:
        print(f"🎯 Success: {result}")


if __name__ == "__main__":
    main()