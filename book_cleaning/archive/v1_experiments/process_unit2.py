#!/usr/bin/env python3
"""
Process Unit 2 of Colloquial French using Gemini 2.5-Flash
Optimized for speed and quality based on our testing
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime

import google.generativeai as genai
from pdf2image import convert_from_path
from PIL import Image
from alive_progress import alive_bar
from dotenv import load_dotenv

class Unit2Processor:
    def __init__(self, pdf_path, output_dir="./formatted_output"):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup API
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable required")
        
        genai.configure(api_key=api_key)
        # Use 2.5-Flash for optimal speed/quality balance
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Session setup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"unit2_flash_{timestamp}"
        self.session_dir.mkdir(exist_ok=True)
        
        print(f"✅ Unit 2 Processor initialized")
        print(f"🚀 Using Gemini 2.5-Flash (optimal speed/quality)")
        print(f"📁 Session: {self.session_dir}")
    
    def convert_pdf_to_images(self, start_page, end_page, batch_size=10):
        """Convert PDF pages to images in batches"""
        images_dir = self.session_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        total_pages = end_page - start_page + 1
        print(f"\n📷 Converting {total_pages} pages to images...")
        
        all_image_paths = []
        
        # Process in batches to manage memory
        with alive_bar(
            total_pages,
            title="📷 Converting pages",
            spinner="waves",
            force_tty=True
        ) as bar:
            
            for batch_start in range(start_page, end_page + 1, batch_size):
                batch_end = min(batch_start + batch_size - 1, end_page)
                
                try:
                    # Convert batch
                    images = convert_from_path(
                        self.pdf_path,
                        dpi=300,
                        first_page=batch_start,
                        last_page=batch_end
                    )
                    
                    # Save batch
                    for i, image in enumerate(images):
                        page_num = batch_start + i
                        image_path = images_dir / f"page_{page_num:03d}.jpg"
                        image.save(image_path, 'JPEG', quality=95)
                        all_image_paths.append(image_path)
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
        
        # Optimal instruction for French textbook
        instruction = """
EDUCATIONAL OCR TASK: Extract visible text from these French language textbook pages.

CRITICAL REQUIREMENTS:
1. **Multi-column layout**: Read LEFT to RIGHT, TOP to BOTTOM
2. **French formatting**: Preserve all accents (é, è, ê, ë, à, â, etc.)
3. **Exercise numbering**: Keep exact sequence as shown
4. **Dialogue format**: Maintain speaker labels and order
5. **Tables**: Preserve structure, especially verb conjugations

TEXTBOOK ELEMENTS TO CAPTURE:
- Unit/section headers
- Language points and grammar explanations
- Dialogue conversations with speakers
- Exercise questions and numbering
- "Did you notice?" boxes
- CD track references (CD 1; 5)
- Verb conjugation tables
- Vocabulary lists

OUTPUT: Clean text with preserved structure. Focus on accuracy over formatting.
"""
        
        # Process in batches
        batches = [image_paths[i:i + batch_size] for i in range(0, len(image_paths), batch_size)]
        results = []
        
        print(f"\n🔍 Processing {len(image_paths)} pages in {len(batches)} batches...")
        
        with alive_bar(
            len(batches),
            title="🚀 OCR Processing",
            spinner="waves",
            dual_line=True,
            force_tty=True
        ) as bar:
            
            for batch_num, batch_paths in enumerate(batches):
                bar.text = f"📖 Batch {batch_num + 1}/{len(batches)} ({len(batch_paths)} pages)"
                
                try:
                    # Load images for batch
                    images = [Image.open(path) for path in batch_paths]
                    
                    # Process with Gemini 2.5-Flash
                    start_time = time.time()
                    response = self.model.generate_content([instruction] + images)
                    processing_time = time.time() - start_time
                    
                    # Store result
                    start_page = int(batch_paths[0].stem.split('_')[1])
                    end_page = int(batch_paths[-1].stem.split('_')[1])
                    
                    results.append({
                        "batch": batch_num + 1,
                        "start_page": start_page,
                        "end_page": end_page,
                        "text": response.text,
                        "processing_time": processing_time,
                        "pages_count": len(batch_paths)
                    })
                    
                    bar.text = f"✅ Batch {batch_num + 1} complete ({processing_time:.1f}s)"
                    
                    # Clear memory
                    del images
                    
                except Exception as e:
                    print(f"\n❌ Error processing batch {batch_num + 1}: {e}")
                    results.append({
                        "batch": batch_num + 1,
                        "start_page": start_page,
                        "end_page": end_page,
                        "text": f"[ERROR: {str(e)}]",
                        "processing_time": 0,
                        "pages_count": len(batch_paths),
                        "error": True
                    })
                
                bar()
                time.sleep(1)  # Rate limiting
        
        return results
    
    def apply_french_formatting(self, text):
        """Apply French textbook-specific formatting"""
        
        # Basic formatting improvements
        # This is a simple version - could be enhanced with more rules
        formatted = text
        
        # Ensure section headers have proper formatting
        formatted = formatted.replace("Language points", "## Language points")
        formatted = formatted.replace("Exercise ", "### Exercise ")
        formatted = formatted.replace("Dialogue ", "### Dialogue ")
        formatted = formatted.replace("Did you notice?", "### Did you notice?")
        
        # Ensure proper line breaks around exercises
        import re
        formatted = re.sub(r'(\d+)\s+([A-Z])', r'\1 \2', formatted)
        
        return formatted
    
    def save_results(self, ocr_results):
        """Save all results and create final formatted output"""
        
        # Combine all text
        combined_text = ""
        total_time = 0
        successful_batches = 0
        
        for result in ocr_results:
            if not result.get('error'):
                combined_text += f"\n\n{'='*60}\n"
                combined_text += f"Pages {result['start_page']}-{result['end_page']}\n"
                combined_text += f"{'='*60}\n\n"
                combined_text += result['text']
                total_time += result['processing_time']
                successful_batches += 1
        
        # Apply formatting
        formatted_text = self.apply_french_formatting(combined_text)
        
        # Save raw OCR output
        raw_file = self.session_dir / "unit2_raw_ocr.md"
        with open(raw_file, 'w', encoding='utf-8') as f:
            f.write(combined_text)
        
        # Save formatted output
        formatted_file = self.session_dir / "Unit2_Colloquial_French_formatted.md"
        with open(formatted_file, 'w', encoding='utf-8') as f:
            f.write(formatted_text)
        
        # Save detailed results
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "pdf_file": str(self.pdf_path),
            "session_dir": str(self.session_dir),
            "model": "gemini-2.5-flash",
            "total_processing_time": total_time,
            "successful_batches": successful_batches,
            "total_batches": len(ocr_results),
            "pages_processed": sum(r['pages_count'] for r in ocr_results if not r.get('error')),
            "average_time_per_page": total_time / sum(r['pages_count'] for r in ocr_results if not r.get('error')) if successful_batches > 0 else 0,
            "batches": ocr_results
        }
        
        results_file = self.session_dir / "processing_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        return formatted_file, results_data
    
    def process_unit2(self, start_page=20, end_page=40):
        """Main processing function for Unit 2"""
        
        print("\n🚀 Processing Unit 2 of Colloquial French")
        print("=" * 60)
        print(f"📄 PDF: {self.pdf_path.name}")
        print(f"📖 Estimated pages: {start_page}-{end_page}")
        print(f"🤖 Model: Gemini 2.5-Flash (optimal speed/quality)")
        
        start_total = time.time()
        
        # Step 1: Convert to images
        image_paths = self.convert_pdf_to_images(start_page, end_page)
        if not image_paths:
            print("❌ Failed to convert PDF to images")
            return None
        
        # Step 2: OCR in batches
        ocr_results = self.process_pages_in_batches(image_paths)
        
        # Step 3: Save results
        formatted_file, results_data = self.save_results(ocr_results)
        
        total_time = time.time() - start_total
        
        # Print summary
        print("\n" + "=" * 60)
        print("✅ UNIT 2 PROCESSING COMPLETE!")
        print("=" * 60)
        print(f"📊 Pages processed: {results_data['pages_processed']}")
        print(f"⏱️  Total time: {total_time:.1f}s")
        print(f"⚡ OCR time: {results_data['total_processing_time']:.1f}s")
        print(f"📄 Average per page: {results_data['average_time_per_page']:.1f}s")
        print(f"✅ Success rate: {results_data['successful_batches']}/{results_data['total_batches']} batches")
        print()
        print(f"📁 Output files:")
        print(f"   - Formatted: {formatted_file}")
        print(f"   - Raw OCR: {self.session_dir / 'unit2_raw_ocr.md'}")
        print(f"   - Results: {results_data}")
        
        return formatted_file


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Process Unit 2 with Gemini 2.5-Flash")
    parser.add_argument("pdf_file", help="Input PDF file")
    parser.add_argument("--start-page", type=int, default=20, help="Start page for Unit 2")
    parser.add_argument("--end-page", type=int, default=40, help="End page for Unit 2")
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    # Process Unit 2
    processor = Unit2Processor(pdf_path)
    result = processor.process_unit2(args.start_page, args.end_page)
    
    if result:
        print(f"\n🎯 Unit 2 successfully processed!")
        print(f"📄 Open the formatted file to review: {result}")
    else:
        print("❌ Unit 2 processing failed")


if __name__ == "__main__":
    main()