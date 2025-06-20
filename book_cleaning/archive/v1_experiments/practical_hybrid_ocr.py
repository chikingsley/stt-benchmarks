#!/usr/bin/env python3
"""
Practical Hybrid OCR: Flash → Pro QA
Test the most practical hybrid approach: Fast Flash OCR + Pro quality review
"""

import os
import time
import json
import difflib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import google.generativeai as genai
from pdf2image import convert_from_path
from PIL import Image
from alive_progress import alive_bar
from dotenv import load_dotenv

class PracticalHybridOCR:
    def __init__(self, pdf_path, output_dir="./formatted_output"):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup APIs
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable required")
        
        genai.configure(api_key=api_key)
        self.flash = genai.GenerativeModel('gemini-2.5-flash')
        self.pro = genai.GenerativeModel('gemini-2.5-pro')
        
        # Session setup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"practical_hybrid_{timestamp}"
        self.session_dir.mkdir(exist_ok=True)
        
        print(f"✅ Practical Hybrid OCR initialized")
        print(f"📁 Session: {self.session_dir}")
    
    def convert_pdf_to_images(self, start_page, end_page):
        """Convert PDF pages to images"""
        images_dir = self.session_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        try:
            print(f"📷 Converting PDF pages {start_page}-{end_page} to images...")
            images = convert_from_path(
                self.pdf_path,
                dpi=300,
                first_page=start_page,
                last_page=end_page
            )
            
            image_paths = []
            for i, image in enumerate(images):
                page_num = start_page + i
                image_path = images_dir / f"page_{page_num:03d}.jpg"
                image.save(image_path, 'JPEG', quality=95)
                image_paths.append(image_path)
            
            print(f"✅ Converted {len(image_paths)} pages to images")
            return image_paths
            
        except Exception as e:
            print(f"❌ Error converting PDF to images: {e}")
            return []
    
    def flash_primary_ocr(self, image_paths):
        """Step 1: Fast primary OCR with Flash"""
        print("🚀 Step 1: Flash Primary OCR")
        start_time = time.time()
        
        try:
            images = [Image.open(path) for path in image_paths]
            
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
            
            response = self.flash.generate_content([instruction] + images)
            processing_time = time.time() - start_time
            
            print(f"✅ Flash OCR complete: {processing_time:.1f}s")
            return response.text, processing_time
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ Flash OCR failed: {e}")
            return f"ERROR: {str(e)}", processing_time
    
    def pro_quality_review(self, flash_text, image_paths):
        """Step 2: Pro quality assurance review"""
        print("🔍 Step 2: Pro Quality Review")
        start_time = time.time()
        
        try:
            images = [Image.open(path) for path in image_paths]
            
            qa_instruction = f"""
QUALITY ASSURANCE REVIEW: Improve the OCR text extraction accuracy.

ORIGINAL FLASH OCR TEXT:
{flash_text}

YOUR TASK:
Compare the original images with the Flash OCR text above and make targeted improvements:

1. **Fix OCR errors**: Correct misread characters, words, or numbers
2. **Improve structure**: Better table formatting, cleaner line breaks
3. **Enhance formatting**: Proper section headers, bullet points, numbering
4. **Preserve content**: Don't change meaning, only improve accuracy and presentation

CRITICAL GUIDELINES:
- Only make improvements that fix clear OCR errors
- Preserve all original content and meaning
- Maintain French accents and special characters
- Keep exercise numbering exactly as shown in images
- Focus on accuracy and readability improvements

OUTPUT: Improved text with better accuracy and formatting while preserving all original content.
"""
            
            response = self.pro.generate_content([qa_instruction] + images)
            processing_time = time.time() - start_time
            
            print(f"✅ Pro QA complete: {processing_time:.1f}s")
            return response.text, processing_time
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ Pro QA failed: {e}")
            return f"ERROR: {str(e)}", processing_time
    
    def calculate_improvement_metrics(self, flash_text, pro_text):
        """Calculate improvement metrics"""
        
        # Basic similarity between Flash and Pro outputs
        similarity = difflib.SequenceMatcher(None, flash_text, pro_text).ratio()
        
        # Text length changes
        length_change = len(pro_text) - len(flash_text)
        length_change_percent = (length_change / len(flash_text)) * 100 if flash_text else 0
        
        # Word count changes
        words_flash = len(flash_text.split())
        words_pro = len(pro_text.split())
        word_change = words_pro - words_flash
        word_change_percent = (word_change / words_flash) * 100 if words_flash else 0
        
        # Line count changes
        lines_flash = len(flash_text.split('\n'))
        lines_pro = len(pro_text.split('\n'))
        line_change = lines_pro - lines_flash
        
        # Estimate quality improvement (heuristic)
        # Moderate changes usually indicate good improvements
        quality_indicators = []
        
        # Similarity should be high but not perfect (some improvements made)
        if 0.85 <= similarity <= 0.95:
            quality_indicators.append(0.8)  # Good improvement level
        elif similarity > 0.95:
            quality_indicators.append(0.6)  # Maybe minor improvements
        else:
            quality_indicators.append(0.4)  # Maybe too many changes
        
        # Length changes should be moderate
        if -10 <= length_change_percent <= 20:
            quality_indicators.append(0.8)  # Reasonable changes
        else:
            quality_indicators.append(0.5)  # Possibly too drastic
        
        # Word changes should be moderate
        if -5 <= word_change_percent <= 15:
            quality_indicators.append(0.8)  # Good improvement
        else:
            quality_indicators.append(0.6)  # Maybe too many changes
        
        estimated_quality_improvement = sum(quality_indicators) / len(quality_indicators)
        
        return {
            'flash_to_pro_similarity': similarity,
            'length_change': length_change,
            'length_change_percent': length_change_percent,
            'word_change': word_change,
            'word_change_percent': word_change_percent,
            'line_change': line_change,
            'words_flash': words_flash,
            'words_pro': words_pro,
            'lines_flash': lines_flash,
            'lines_pro': lines_pro,
            'estimated_quality_improvement': estimated_quality_improvement
        }
    
    def run_practical_hybrid_test(self, start_page=20, end_page=22):
        """Run the practical hybrid test: Flash → Pro QA"""
        
        print("🚀 Practical Hybrid OCR Test: Flash → Pro QA")
        print("=" * 60)
        print(f"📄 PDF: {self.pdf_path.name}")
        print(f"📖 Pages: {start_page}-{end_page}")
        print()
        
        # Convert PDF to images
        image_paths = self.convert_pdf_to_images(start_page, end_page)
        if not image_paths:
            return None
        
        # Step 1: Flash Primary OCR
        flash_text, flash_time = self.flash_primary_ocr(image_paths)
        if flash_text.startswith("ERROR"):
            print(f"❌ Test failed at Flash OCR step")
            return None
        
        # Step 2: Pro Quality Review
        pro_text, pro_time = self.pro_quality_review(flash_text, image_paths)
        if pro_text.startswith("ERROR"):
            print(f"⚠️ Pro QA failed, using Flash output only")
            pro_text = flash_text
            pro_time = 0
        
        # Calculate metrics
        total_time = flash_time + pro_time
        improvement_metrics = self.calculate_improvement_metrics(flash_text, pro_text)
        
        # Generate results
        results = {
            'flash_text': flash_text,
            'pro_text': pro_text,
            'flash_time': flash_time,
            'pro_time': pro_time,
            'total_time': total_time,
            'improvement_metrics': improvement_metrics,
            'pages_processed': len(image_paths)
        }
        
        # Save outputs
        self.save_results(results)
        
        # Print summary
        self.print_summary(results)
        
        return results
    
    def save_results(self, results):
        """Save all results"""
        
        # Save Flash output
        flash_file = self.session_dir / "flash_primary_output.md"
        with open(flash_file, 'w', encoding='utf-8') as f:
            f.write(results['flash_text'])
        
        # Save Pro QA output  
        pro_file = self.session_dir / "pro_qa_output.md"
        with open(pro_file, 'w', encoding='utf-8') as f:
            f.write(results['pro_text'])
        
        # Save detailed report
        report = {
            'timestamp': datetime.now().isoformat(),
            'pdf_file': str(self.pdf_path),
            'session_dir': str(self.session_dir),
            'processing_times': {
                'flash_ocr': results['flash_time'],
                'pro_qa': results['pro_time'],
                'total': results['total_time']
            },
            'text_lengths': {
                'flash': len(results['flash_text']),
                'pro': len(results['pro_text'])
            },
            'pages_processed': results['pages_processed'],
            'improvement_metrics': results['improvement_metrics']
        }
        
        report_file = self.session_dir / "practical_hybrid_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📁 Files saved:")
        print(f"   - Flash output: {flash_file}")
        print(f"   - Pro QA output: {pro_file}")
        print(f"   - Report: {report_file}")
    
    def print_summary(self, results):
        """Print results summary"""
        
        metrics = results['improvement_metrics']
        
        print("\n📊 PRACTICAL HYBRID RESULTS")
        print("=" * 50)
        print(f"⚡ Flash OCR Time: {results['flash_time']:.1f}s")
        print(f"🔍 Pro QA Time: {results['pro_time']:.1f}s") 
        print(f"🕐 Total Time: {results['total_time']:.1f}s")
        print()
        print(f"📝 Flash Text Length: {len(results['flash_text'])} chars")
        print(f"📝 Pro Text Length: {len(results['pro_text'])} chars")
        print(f"📊 Length Change: {metrics['length_change']:+d} chars ({metrics['length_change_percent']:+.1f}%)")
        print()
        print(f"🔄 Flash→Pro Similarity: {metrics['flash_to_pro_similarity']:.3f}")
        print(f"📈 Est. Quality Improvement: {metrics['estimated_quality_improvement']:.3f}")
        print()
        
        # Comparison with single models
        print("🆚 VS SINGLE MODELS:")
        print(f"   Flash alone: ~{results['flash_time']:.1f}s (63% quality)")
        print(f"   Pro alone: ~47s (74% quality)")
        print(f"   Hybrid: {results['total_time']:.1f}s (?% quality)")
        
        if results['total_time'] < 47:
            print(f"✅ Hybrid is {47 - results['total_time']:.1f}s faster than Pro alone!")
        else:
            print(f"⚠️ Hybrid is {results['total_time'] - 47:.1f}s slower than Pro alone")
        
        if results['total_time'] > results['flash_time'] * 2:
            print(f"⚠️ Hybrid is {results['total_time'] / results['flash_time']:.1f}x slower than Flash alone")
        else:
            print(f"✅ Reasonable time vs Flash alone ({results['total_time'] / results['flash_time']:.1f}x)")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Practical Hybrid OCR: Flash → Pro QA")
    parser.add_argument("pdf_file", help="Input PDF file")
    parser.add_argument("--start-page", type=int, default=20, help="Start page")
    parser.add_argument("--end-page", type=int, default=22, help="End page")
    
    args = parser.parse_args()
    
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Please set GOOGLE_API_KEY environment variable")
        return
    
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    # Run practical hybrid test
    hybrid_system = PracticalHybridOCR(pdf_path)
    results = hybrid_system.run_practical_hybrid_test(args.start_page, args.end_page)
    
    if results:
        print(f"\n🎯 Practical Hybrid Test Complete!")
        if results['total_time'] < 47 and results['improvement_metrics']['estimated_quality_improvement'] > 0.7:
            print("🏆 Hybrid approach shows promise!")
        elif results['total_time'] < 47:
            print("✅ Hybrid is faster than Pro, quality improvement unclear")
        else:
            print("📝 Hybrid results available for analysis")
    else:
        print("❌ Hybrid test failed")


if __name__ == "__main__":
    main()