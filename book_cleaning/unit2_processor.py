#!/usr/bin/env python3
"""
Process Unit 2 with improved OCR prompting and post-processing
Optimized for Gemini 2.5-Flash with better paragraph handling
"""

from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import io
import base64
import google.generativeai as genai
from datetime import datetime
import json
from alive_progress import alive_bar
import os
from dotenv import load_dotenv
from markdown_post_processor import MarkdownPostProcessor

# Load environment variables
load_dotenv()

class Unit2ProcessorV2:
    def __init__(self):
        """Initialize with Gemini 2.5-Flash"""
        
        # Configure Gemini
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Please set GOOGLE_API_KEY in .env file")
        
        genai.configure(api_key=api_key)
        
        # Use Gemini 2.5-Flash for optimal speed/quality
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Create session directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = Path("formatted_output") / f"unit2_flash_v2_{timestamp}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Unit 2 Processor V2 initialized")
        print(f"🚀 Using Gemini 2.5-Flash with improved prompting")
        print(f"📁 Session: {self.session_dir}")
    
    def convert_pdf_to_images_batch(self, pdf_path: Path, start_page: int, end_page: int):
        """Convert PDF pages to images in batches"""
        
        all_image_paths = []
        
        # Process in batches of 10 for memory efficiency
        batch_size = 10
        total_pages = end_page - start_page + 1
        
        print(f"\n📷 Converting {total_pages} pages to images...")
        
        with alive_bar(total_pages, title="📷 Converting pages", spinner="waves") as bar:
            for batch_start in range(start_page, end_page + 1, batch_size):
                batch_end = min(batch_start + batch_size - 1, end_page)
                
                try:
                    # Open PDF for this batch
                    pdf = fitz.open(pdf_path)
                    
                    # Convert batch
                    images = []
                    for page_num in range(batch_start - 1, batch_end):
                        if page_num < len(pdf):
                            page = pdf[page_num]
                            # Higher resolution for better OCR
                            mat = fitz.Matrix(2.0, 2.0)
                            pix = page.get_pixmap(matrix=mat)
                            img_data = pix.tobytes("png")
                            img = Image.open(io.BytesIO(img_data))
                            images.append(img)
                    
                    pdf.close()
                    
                    # Save images
                    for i, img in enumerate(images):
                        page_num = batch_start + i
                        img_path = self.session_dir / f"page_{page_num:03d}.png"
                        img.save(img_path, "PNG", optimize=True)
                        all_image_paths.append(img_path)
                        bar()
                    
                    # Clear memory
                    del images
                    
                except Exception as e:
                    print(f"\n❌ Error converting pages {batch_start}-{batch_end}: {e}")
                    return None
        
        print(f"✅ Converted {len(all_image_paths)} pages")
        return all_image_paths
    
    def process_pages_in_batches(self, image_paths, batch_size=5):
        """Process pages in optimal batches for Gemini 2.5-Flash"""
        
        # IMPROVED instruction for better paragraph handling
        instruction = """
EDUCATIONAL OCR TASK: Extract text from these French language textbook pages.

CRITICAL INSTRUCTIONS FOR TEXT EXTRACTION:

1. **PARAGRAPH HANDLING**:
   - Merge lines that belong to the same paragraph into single continuous lines
   - Do NOT preserve line breaks within paragraphs
   - Only create new lines for: new paragraphs, dialogue speakers, exercises, headers
   - If a sentence continues across lines, merge it into one line

2. **PAGE HEADERS TO IGNORE**:
   - Skip any headers like "Unit 2: In town 23" or page numbers
   - Skip standalone page numbers
   - Focus only on the main content

3. **PRESERVE THESE ELEMENTS**:
   - French accents (é, è, ê, ë, à, â, etc.)
   - Exercise numbering and structure
   - Dialogue format with speaker labels
   - Tables (especially verb conjugations)
   - Bold text markers (**)
   - Section headers

4. **FORMATTING RULES**:
   - Each paragraph should be on its own line
   - Leave blank lines between different sections
   - Keep special formatting (bold, lists) intact

EXAMPLE OUTPUT:
Instead of:
"Elle habite en Angleterre,
à Coventry."

Output:
"Elle habite en Angleterre, à Coventry."

Extract all visible text following these rules."""
        
        # Process in batches
        results = []
        total_batches = (len(image_paths) + batch_size - 1) // batch_size
        
        print(f"\n🔍 Processing {len(image_paths)} pages in {total_batches} batches...")
        
        with alive_bar(total_batches, title="🚀 OCR Processing", spinner="waves") as bar:
            for i in range(0, len(image_paths), batch_size):
                batch_images = image_paths[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                print(f"\n📖 Batch {batch_num}/{total_batches} ({len(batch_images)} pages)")
                
                try:
                    # Convert images to base64
                    image_parts = []
                    for img_path in batch_images:
                        with open(img_path, 'rb') as f:
                            image_data = base64.b64encode(f.read()).decode('utf-8')
                            image_parts.append({
                                "mime_type": "image/png",
                                "data": image_data
                            })
                    
                    # Create prompt with all images
                    prompt_parts = [instruction]
                    prompt_parts.extend([{"inline_data": img} for img in image_parts])
                    
                    # Process with Gemini
                    response = self.model.generate_content(prompt_parts)
                    
                    if response.text:
                        results.append({
                            "batch": batch_num,
                            "start_page": int(batch_images[0].stem.split('_')[1]),
                            "end_page": int(batch_images[-1].stem.split('_')[1]),
                            "text": response.text,
                            "processing_time": 0,  # Would need timing
                            "pages_count": len(batch_images)
                        })
                        print(f"✅ Batch {batch_num} complete")
                    else:
                        print(f"⚠️ Batch {batch_num} returned empty")
                    
                except Exception as e:
                    print(f"❌ Error processing batch {batch_num}: {e}")
                    results.append({
                        "batch": batch_num,
                        "error": str(e)
                    })
                
                bar()
        
        return results
    
    def save_results(self, results, pdf_path):
        """Save OCR results and apply post-processing"""
        
        # Combine all text
        all_text = []
        for batch in results:
            if "text" in batch and batch["text"]:
                all_text.append(batch["text"])
        
        combined_text = "\n\n".join(all_text)
        
        # Save raw OCR output
        raw_file = self.session_dir / f"unit2_raw_ocr_v2.md"
        with open(raw_file, 'w', encoding='utf-8') as f:
            f.write(combined_text)
        
        print(f"\n📝 Saved raw OCR to: {raw_file.name}")
        
        # Apply post-processing
        print("\n🔧 Applying post-processing...")
        processor = MarkdownPostProcessor()
        cleaned_file = processor.process_file(raw_file)
        
        # Save final formatted version
        final_file = self.session_dir / f"Unit2_{pdf_path.stem}_formatted_v2.md"
        with open(cleaned_file, 'r', encoding='utf-8') as f:
            final_content = f.read()
        with open(final_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        # Save processing results
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "pdf_file": str(pdf_path),
            "session_dir": str(self.session_dir),
            "model": "gemini-2.5-flash",
            "improved_prompting": True,
            "post_processing_applied": True,
            "successful_batches": len([r for r in results if "text" in r]),
            "total_batches": len(results),
            "pages_processed": sum(r.get("pages_count", 0) for r in results if "text" in r),
            "post_processing_stats": processor.stats,
            "batches": results
        }
        
        results_file = self.session_dir / "processing_results_v2.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        return final_file, results_file
    
    def process_unit2(self, pdf_path: Path, start_page=20, end_page=40):
        """Main processing pipeline for Unit 2"""
        
        print(f"\n🚀 Processing Unit 2 of {pdf_path.name}")
        print("=" * 60)
        print(f"📄 PDF: {pdf_path}")
        print(f"📖 Pages: {start_page}-{end_page}")
        print(f"🤖 Model: Gemini 2.5-Flash (with improved prompting)")
        print(f"🔧 Post-processing: Enabled")
        
        # Convert pages to images
        image_paths = self.convert_pdf_to_images_batch(pdf_path, start_page, end_page)
        if not image_paths:
            print("❌ Failed to convert PDF to images")
            return None, None
        
        # Process with OCR
        results = self.process_pages_in_batches(image_paths, batch_size=5)
        
        # Save results with post-processing
        formatted_file, results_file = self.save_results(results, pdf_path)
        
        print(f"\n✅ Processing complete!")
        print(f"📄 Final output: {formatted_file}")
        print(f"📊 Results: {results_file}")
        
        return formatted_file, results_file


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Process Unit 2 with improved OCR and post-processing')
    parser.add_argument('pdf_file', help='Path to the PDF file')
    parser.add_argument('--start-page', type=int, default=20, help='Start page (default: 20)')
    parser.add_argument('--end-page', type=int, default=40, help='End page (default: 40)')
    
    args = parser.parse_args()
    
    processor = Unit2ProcessorV2()
    pdf_path = Path(args.pdf_file)
    
    if not pdf_path.exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    processor.process_unit2(pdf_path, args.start_page, args.end_page)


if __name__ == "__main__":
    main()