#!/usr/bin/env python3
"""
Gemini 2.0 Flash OCR Formatter - Alternative to Mistral OCR
Based on the insights from gemini_ocr_blog.md
"""

import os
import time
import yaml
import json
from pathlib import Path
from datetime import datetime
import google.generativeai as genai
from pdf2image import convert_from_path
from PIL import Image
from alive_progress import alive_bar
from dotenv import load_dotenv

class GeminiOCRFormatter:
    def __init__(self, pdf_path, output_dir="./formatted_output"):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup Gemini API
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable required")
        
        genai.configure(api_key=api_key)
        # Default to 2.0-flash, but allow override
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Session setup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"gemini_session_{timestamp}"
        self.session_dir.mkdir(exist_ok=True)
        
        self.usage_stats = {"pages_processed": 0, "api_calls": 0}
    
    def convert_pdf_to_images(self, start_page=1, end_page=None, dpi=300):
        """Convert PDF pages to high-quality images"""
        
        print(f"📄 Converting PDF to images (DPI: {dpi})")
        
        # Convert specific page range
        if end_page:
            page_range = range(start_page - 1, end_page)  # 0-based for pdf2image
        else:
            page_range = None
        
        # Create images directory
        images_dir = self.session_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        # Convert PDF to images
        images = convert_from_path(
            self.pdf_path, 
            dpi=dpi,
            first_page=start_page,
            last_page=end_page
        )
        
        image_paths = []
        with alive_bar(
            len(images),
            title="📷 Converting pages",
            spinner="waves",
            force_tty=True
        ) as bar:
            for i, image in enumerate(images):
                page_num = start_page + i
                image_path = images_dir / f"page_{page_num:03d}.jpg"
                image.save(image_path, 'JPEG', quality=95)
                image_paths.append(image_path)
                bar()
        
        print(f"✅ Converted {len(image_paths)} pages")
        return image_paths
    
    def ocr_textbook_pages(self, image_paths):
        """OCR specifically for language textbook with layout awareness"""
        
        instruction = """
EDUCATIONAL OCR TASK: Extract visible text from these educational document images for research purposes.

TECHNICAL REQUIREMENTS:
1. **Reading order**: Process text LEFT to RIGHT, TOP to BOTTOM
2. **Numbered lists**: Maintain exact sequence as shown
3. **Speaker labels**: Keep exact order and format
4. **Tables**: Preserve structure 
5. **Headers**: Include all section titles

EXTRACTION APPROACH:
- Read all visible text characters accurately
- Preserve spacing and line breaks
- Include all numbers, punctuation, and symbols
- Maintain original text organization
- Do not interpret or translate content
- Focus purely on character recognition

OUTPUT: Clean plain text with preserved structure and layout.
"""
        
        # Process in batches for better accuracy
        batch_size = 10  # Conservative batch size
        results = []
        
        batches = [image_paths[i:i + batch_size] for i in range(0, len(image_paths), batch_size)]
        
        with alive_bar(
            len(batches),
            title="🔍 Gemini OCR",
            spinner="waves",
            dual_line=True,
            force_tty=True
        ) as bar:
            
            for batch_num, batch_paths in enumerate(batches):
                bar.text = f"📖 Processing batch {batch_num + 1}/{len(batches)}"
                
                # Load images for this batch
                images = [Image.open(path) for path in batch_paths]
                
                try:
                    # Call Gemini with images
                    response = self.model.generate_content([instruction] + images)
                    ocr_text = response.text
                    
                    # Store result with page info
                    start_page = int(batch_paths[0].stem.split('_')[1])
                    end_page = int(batch_paths[-1].stem.split('_')[1])
                    
                    results.append({
                        "batch": batch_num + 1,
                        "start_page": start_page,
                        "end_page": end_page,
                        "text": ocr_text,
                        "page_count": len(batch_paths)
                    })
                    
                    self.usage_stats["api_calls"] += 1
                    self.usage_stats["pages_processed"] += len(batch_paths)
                    
                    bar.text = f"✅ Batch {batch_num + 1} complete | Pages: {self.usage_stats['pages_processed']}"
                    
                except Exception as e:
                    print(f"❌ Error processing batch {batch_num + 1}: {e}")
                    results.append({
                        "batch": batch_num + 1,
                        "start_page": start_page,
                        "end_page": end_page,
                        "text": f"[ERROR: {str(e)}]",
                        "page_count": len(batch_paths),
                        "error": True
                    })
                
                bar()
                time.sleep(1)  # Rate limiting
        
        return results
    
    def enhance_formatting(self, ocr_results):
        """Apply specific formatting rules to OCR output"""
        
        # Combine all OCR text
        combined_text = "\n\n=== PAGE BREAK ===\n\n".join([
            f"# Pages {result['start_page']}-{result['end_page']}\n\n{result['text']}"
            for result in ocr_results if not result.get('error')
        ])
        
        formatting_instruction = """
The following text was extracted via OCR from a French language textbook.
Apply proper markdown formatting following these EXACT rules:

FORMATTING RULES:
1. **French sentences with verbs**: **Elle _habite_ en Angleterre** (verb italicized within bold)
2. **Standalone French examples**: **Vous êtes français.**
3. **English translations**: Keep as plain text (not italics unless originally italicized)
4. **Section headers**: 
   - Main: ## Language points - Topic
   - Sub: ### Did you notice?
   - Exercises: ### Exercise N (CD X; Y)
5. **Grammatical terms**: **je**, **tu**, **-er**, **conjugation**, etc.
6. **Dialogues**: Simple format - SPEAKER: Text
7. **Preserve ALL content** - no additions, no reorganizing

CRITICAL: 
- Do NOT add translations that weren't in the source
- Do NOT reorder content - keep exact sequence
- Do NOT change exercise numbering
- Do NOT reverse dialogue speakers

Clean OCR text:
"""
        
        try:
            response = self.model.generate_content(formatting_instruction + combined_text)
            formatted_text = response.text
            self.usage_stats["api_calls"] += 1
            
            return formatted_text
            
        except Exception as e:
            print(f"⚠️ Formatting failed: {e}")
            return combined_text  # Return unformatted if formatting fails
    
    def save_results(self, ocr_results, formatted_text):
        """Save all results and generate report"""
        
        # Save raw OCR results
        ocr_file = self.session_dir / "gemini_ocr_raw.json"
        with open(ocr_file, 'w', encoding='utf-8') as f:
            json.dump(ocr_results, f, indent=2, ensure_ascii=False)
        
        # Save formatted output
        formatted_file = self.session_dir / f"{self.pdf_path.stem}_gemini_formatted.md"
        with open(formatted_file, 'w', encoding='utf-8') as f:
            f.write(formatted_text)
        
        # Generate processing report
        report = {
            "timestamp": datetime.now().isoformat(),
            "pdf_file": str(self.pdf_path),
            "session_dir": str(self.session_dir),
            "usage_stats": self.usage_stats,
            "ocr_batches": len(ocr_results),
            "successful_batches": len([r for r in ocr_results if not r.get('error')]),
            "total_api_calls": self.usage_stats["api_calls"]
        }
        
        report_file = self.session_dir / "gemini_processing_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        return formatted_file, report_file
    
    def process_pdf(self, start_page=1, end_page=None, mode="sample"):
        """Main processing pipeline"""
        
        print("🚀 Gemini 2.0 Flash OCR Formatter")
        print("=" * 50)
        print(f"📄 PDF: {self.pdf_path.name}")
        
        if mode == "sample" and not end_page:
            end_page = start_page + 2  # Default to 3 pages for sample
        
        # Step 1: Convert PDF to images
        image_paths = self.convert_pdf_to_images(start_page, end_page)
        
        # Step 2: OCR with Gemini
        print(f"\n🔍 OCR processing pages {start_page}-{end_page or 'end'}")
        ocr_results = self.ocr_textbook_pages(image_paths)
        
        # Step 3: Format output
        print("\n🎨 Applying formatting...")
        formatted_text = self.enhance_formatting(ocr_results)
        
        # Step 4: Save results
        formatted_file, report_file = self.save_results(ocr_results, formatted_text)
        
        print(f"\n✅ Processing Complete!")
        print(f"📄 Formatted output: {formatted_file}")
        print(f"📊 Processing report: {report_file}")
        print(f"🔥 API calls: {self.usage_stats['api_calls']}")
        print(f"📖 Pages processed: {self.usage_stats['pages_processed']}")
        
        return formatted_file


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Gemini 2.0 Flash OCR for French Textbook")
    parser.add_argument("pdf_file", help="Input PDF file")
    parser.add_argument("--start-page", type=int, default=20, help="Start page")
    parser.add_argument("--end-page", type=int, help="End page")
    parser.add_argument("--mode", choices=["sample", "full"], default="sample")
    
    args = parser.parse_args()
    
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Please set GOOGLE_API_KEY environment variable")
        return
    
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    formatter = GeminiOCRFormatter(pdf_path)
    result = formatter.process_pdf(
        start_page=args.start_page,
        end_page=args.end_page,
        mode=args.mode
    )
    
    print(f"🎯 Result: {result}")


if __name__ == "__main__":
    main()