#!/usr/bin/env python3
"""
Hybrid OCR Quality Assurance System
Test combinations: Flash+Flash, Flash+Pro, Pro+Pro
"""

import os
import time
import json
import difflib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

import google.generativeai as genai
from pdf2image import convert_from_path
from PIL import Image
from alive_progress import alive_bar
from dotenv import load_dotenv

@dataclass
class HybridOCRResult:
    combination_name: str
    primary_text: str
    qa_text: str
    final_text: str
    primary_time: float
    qa_time: float
    total_time: float
    confidence_score: float
    improvement_metrics: Dict[str, Any]
    error: str = None

class HybridOCRQualityAssurance:
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
        self.gemini_2_5_pro = genai.GenerativeModel('gemini-2.5-pro')
        self.gemini_2_5_flash = genai.GenerativeModel('gemini-2.5-flash')
        
        # Session setup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"hybrid_qa_{timestamp}"
        self.session_dir.mkdir(exist_ok=True)
        
        self.results = []
    
    def convert_pdf_to_images(self, start_page, end_page):
        """Convert PDF pages to images"""
        images_dir = self.session_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        try:
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
            
            return image_paths
        except Exception as e:
            print(f"Error converting PDF to images: {e}")
            return []
    
    def primary_ocr(self, model, model_name, image_paths):
        """Primary OCR extraction"""
        print(f"🔍 Primary OCR: {model_name}")
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
            
            response = model.generate_content([instruction] + images)
            processing_time = time.time() - start_time
            
            return response.text, processing_time
            
        except Exception as e:
            processing_time = time.time() - start_time
            return f"ERROR: {str(e)}", processing_time
    
    def quality_assurance_review(self, primary_text, qa_model, qa_model_name, image_paths):
        """Quality assurance review and correction"""
        print(f"🔍 QA Review: {qa_model_name}")
        start_time = time.time()
        
        try:
            images = [Image.open(path) for path in image_paths]
            
            qa_instruction = f"""
QUALITY ASSURANCE TASK: Review and improve the OCR text extraction.

ORIGINAL OCR TEXT:
{primary_text}

YOUR TASK:
1. Compare the original images with the OCR text above
2. Identify and correct OCR errors:
   - Missing text sections
   - Incorrect character recognition
   - Wrong word boundaries
   - Layout/structure issues
3. Preserve all formatting and structure from original
4. Focus on ACCURACY improvements only

CRITICAL: 
- Only fix clear OCR errors, don't change content
- Maintain exact structure and organization
- Preserve all French accents and special characters
- Keep exercise numbering exactly as shown in images

OUTPUT: Corrected text with improved accuracy while preserving original structure.
"""
            
            response = qa_model.generate_content([qa_instruction] + images)
            processing_time = time.time() - start_time
            
            return response.text, processing_time
            
        except Exception as e:
            processing_time = time.time() - start_time
            return f"ERROR: {str(e)}", processing_time
    
    def calculate_improvement_metrics(self, primary_text, qa_text):
        """Calculate improvement metrics between primary and QA outputs"""
        
        # Basic similarity metrics
        similarity = difflib.SequenceMatcher(None, primary_text, qa_text).ratio()
        
        # Text length changes
        length_change = len(qa_text) - len(primary_text)
        length_change_percent = (length_change / len(primary_text)) * 100 if primary_text else 0
        
        # Word count changes
        words_primary = len(primary_text.split())
        words_qa = len(qa_text.split())
        word_change = words_qa - words_primary
        
        # Character-level analysis
        char_accuracy = sum(1 for a, b in zip(primary_text, qa_text) if a == b) / max(len(primary_text), len(qa_text))
        
        # Confidence scoring (heuristic based on changes)
        confidence_factors = []
        confidence_factors.append(0.7 if 0.85 <= similarity <= 0.98 else 0.3)  # Reasonable changes
        confidence_factors.append(0.8 if abs(length_change_percent) < 20 else 0.4)  # Not too drastic
        confidence_factors.append(0.9 if char_accuracy > 0.8 else 0.5)  # High character accuracy
        
        confidence_score = sum(confidence_factors) / len(confidence_factors)
        
        return {
            'similarity_to_primary': similarity,
            'length_change': length_change,
            'length_change_percent': length_change_percent,
            'word_change': word_change,
            'character_accuracy': char_accuracy,
            'confidence_score': confidence_score,
            'words_primary': words_primary,
            'words_qa': words_qa
        }
    
    def test_combination(self, combo_name, primary_model, primary_name, qa_model, qa_name, image_paths):
        """Test a specific model combination"""
        print(f"\n🔄 Testing {combo_name}")
        print("=" * 50)
        
        # Primary OCR
        primary_text, primary_time = self.primary_ocr(primary_model, primary_name, image_paths)
        
        if primary_text.startswith("ERROR"):
            return HybridOCRResult(
                combo_name, primary_text, "", primary_text, 
                primary_time, 0, primary_time, 0, {}, primary_text
            )
        
        # Quality Assurance
        qa_text, qa_time = self.quality_assurance_review(primary_text, qa_model, qa_name, image_paths)
        
        if qa_text.startswith("ERROR"):
            return HybridOCRResult(
                combo_name, primary_text, qa_text, primary_text,
                primary_time, qa_time, primary_time + qa_time, 0.5, {}, qa_text
            )
        
        # Calculate improvements
        improvement_metrics = self.calculate_improvement_metrics(primary_text, qa_text)
        
        # Determine final output (QA if confidence high, otherwise primary)
        final_text = qa_text if improvement_metrics['confidence_score'] > 0.6 else primary_text
        
        return HybridOCRResult(
            combo_name, primary_text, qa_text, final_text,
            primary_time, qa_time, primary_time + qa_time,
            improvement_metrics['confidence_score'], improvement_metrics
        )
    
    def run_hybrid_comparison(self, start_page=20, end_page=30):
        """Run comprehensive hybrid OCR comparison"""
        
        print("🚀 Hybrid OCR Quality Assurance Testing")
        print("=" * 60)
        print(f"📄 PDF: {self.pdf_path.name}")
        print(f"📖 Pages: {start_page}-{end_page}")
        print()
        
        # Convert PDF to images
        print("📷 Converting PDF to images...")
        image_paths = self.convert_pdf_to_images(start_page, end_page)
        if not image_paths:
            print("❌ Failed to convert PDF to images")
            return []
        
        # Define test combinations
        combinations = [
            ("Flash → Flash QA", self.gemini_2_5_flash, "2.5-Flash", self.gemini_2_5_flash, "2.5-Flash"),
            ("Flash → Pro QA", self.gemini_2_5_flash, "2.5-Flash", self.gemini_2_5_pro, "2.5-Pro"),
            ("Pro → Pro QA", self.gemini_2_5_pro, "2.5-Pro", self.gemini_2_5_pro, "2.5-Pro"),
        ]
        
        # Test each combination
        with alive_bar(
            len(combinations),
            title="🔍 Testing combinations",
            spinner="waves",
            dual_line=True,
            force_tty=True
        ) as bar:
            
            for combo_name, primary_model, primary_name, qa_model, qa_name in combinations:
                bar.text = f"🔄 {combo_name}"
                
                result = self.test_combination(
                    combo_name, primary_model, primary_name, 
                    qa_model, qa_name, image_paths
                )
                
                self.results.append(result)
                
                bar.text = f"✅ {combo_name} - Score: {result.confidence_score:.2f}"
                bar()
                time.sleep(2)  # Rate limiting
        
        # Generate comparison report
        self.generate_hybrid_report()
        
        return self.results
    
    def generate_hybrid_report(self):
        """Generate detailed hybrid comparison report"""
        
        print("\n📊 Generating hybrid comparison report...")
        
        # Sort by confidence score
        self.results.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Generate report
        report = {
            "timestamp": datetime.now().isoformat(),
            "pdf_file": str(self.pdf_path),
            "session_dir": str(self.session_dir),
            "combinations_tested": len(self.results),
            "results": []
        }
        
        for result in self.results:
            report["results"].append({
                "combination": result.combination_name,
                "confidence_score": result.confidence_score,
                "processing_time": {
                    "primary": result.primary_time,
                    "qa": result.qa_time,
                    "total": result.total_time
                },
                "text_lengths": {
                    "primary": len(result.primary_text),
                    "qa": len(result.qa_text),
                    "final": len(result.final_text)
                },
                "improvement_metrics": result.improvement_metrics,
                "error": result.error
            })
        
        # Save detailed report
        report_file = self.session_dir / "hybrid_comparison_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Save individual outputs
        for result in self.results:
            combo_safe = result.combination_name.replace(" ", "_").replace("→", "to")
            
            # Primary output
            primary_file = self.session_dir / f"{combo_safe}_primary.md"
            with open(primary_file, 'w', encoding='utf-8') as f:
                f.write(result.primary_text)
            
            # QA output
            qa_file = self.session_dir / f"{combo_safe}_qa.md"
            with open(qa_file, 'w', encoding='utf-8') as f:
                f.write(result.qa_text)
            
            # Final output
            final_file = self.session_dir / f"{combo_safe}_final.md"
            with open(final_file, 'w', encoding='utf-8') as f:
                f.write(result.final_text)
        
        # Print summary
        print(f"\n✅ Hybrid Comparison Complete!")
        print(f"📊 Report: {report_file}")
        print(f"📁 Session: {self.session_dir}")
        print()
        
        print("🏆 HYBRID RANKING (Best to Worst):")
        for i, result in enumerate(self.results, 1):
            if result.error:
                print(f"{i}. {result.combination_name} - ❌ {result.error}")
            else:
                print(f"{i}. {result.combination_name}")
                print(f"   🎯 Confidence: {result.confidence_score:.3f}")
                print(f"   ⏱️  Total Time: {result.total_time:.1f}s")
                print(f"   📊 Improvement: {result.improvement_metrics.get('similarity_to_primary', 0):.3f}")
                print(f"   📝 Length Change: {result.improvement_metrics.get('length_change_percent', 0):.1f}%")
                print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Hybrid OCR Quality Assurance Testing")
    parser.add_argument("pdf_file", help="Input PDF file")
    parser.add_argument("--start-page", type=int, default=20, help="Start page")
    parser.add_argument("--end-page", type=int, default=30, help="End page (for ~2 chapters)")
    
    args = parser.parse_args()
    
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Please set GOOGLE_API_KEY environment variable")
        return
    
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    # Run hybrid comparison
    hybrid_system = HybridOCRQualityAssurance(pdf_path)
    results = hybrid_system.run_hybrid_comparison(args.start_page, args.end_page)
    
    if results:
        print(f"🎯 Tested {len(results)} hybrid combinations successfully!")
        print("🏆 Winner:", results[0].combination_name if results else "None")
    else:
        print("❌ No combinations could be tested")


if __name__ == "__main__":
    main()