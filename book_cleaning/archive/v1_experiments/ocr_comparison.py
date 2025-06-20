#!/usr/bin/env python3
"""
OCR Comparison Script - Test Mistral vs Gemini models and compare to ground truth
"""

import os
import time
import json
import re
import difflib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any
from dotenv import load_dotenv

# Mistral imports
from mistralai import Mistral
import base64

# Gemini imports
import google.generativeai as genai
from pdf2image import convert_from_path
from PIL import Image

# Progress tracking
from alive_progress import alive_bar

@dataclass
class OCRResult:
    model_name: str
    text: str
    processing_time: float
    error: str = None
    metadata: Dict[str, Any] = None

class OCRComparison:
    def __init__(self, pdf_path, ground_truth_path):
        self.pdf_path = Path(pdf_path)
        self.ground_truth_path = Path(ground_truth_path)
        
        # Load ground truth
        with open(self.ground_truth_path, 'r', encoding='utf-8') as f:
            self.ground_truth = f.read()
        
        # Setup APIs
        self.setup_apis()
        
        # Session setup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = Path("./formatted_output") / f"comparison_{timestamp}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = []
    
    def setup_apis(self):
        """Initialize API clients"""
        
        # Load environment variables
        load_dotenv()
        
        # Mistral setup
        mistral_key = os.getenv("MISTRAL_API_KEY")
        if mistral_key:
            self.mistral_client = Mistral(api_key=mistral_key)
            print("✅ Mistral API configured")
        else:
            self.mistral_client = None
            print("⚠️ MISTRAL_API_KEY not found")
        
        # Gemini setup
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key:
            genai.configure(api_key=google_key)
            try:
                self.gemini_2_5_pro = genai.GenerativeModel('gemini-2.5-pro')
                self.gemini_2_5_flash = genai.GenerativeModel('gemini-2.5-flash')
                self.gemini_2_0_flash = genai.GenerativeModel('gemini-2.0-flash')
                print("✅ Gemini models configured (2.5-pro, 2.5-flash, 2.0-flash)")
            except Exception as e:
                print(f"⚠️ Error configuring Gemini models: {e}")
                self.gemini_2_5_pro = None
                self.gemini_2_5_flash = None
                self.gemini_2_0_flash = None
        else:
            self.gemini_2_5_pro = None
            self.gemini_2_5_flash = None
            self.gemini_2_0_flash = None
            print("⚠️ GOOGLE_API_KEY not found")
    
    def encode_pdf_for_mistral(self):
        """Encode PDF for Mistral OCR"""
        try:
            with open(self.pdf_path, "rb") as pdf_file:
                return base64.b64encode(pdf_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding PDF: {e}")
            return None
    
    def convert_pdf_to_images(self, start_page, end_page):
        """Convert PDF pages to images for Gemini"""
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
    
    def test_mistral_ocr(self, start_page, end_page):
        """Test Mistral OCR"""
        if not self.mistral_client:
            return OCRResult("mistral-ocr-latest", "", 0, "API not configured")
        
        print("🤖 Testing Mistral OCR...")
        start_time = time.time()
        
        try:
            base64_pdf = self.encode_pdf_for_mistral()
            if not base64_pdf:
                raise Exception("Failed to encode PDF")
            
            page_numbers = [p - 1 for p in range(start_page, end_page + 1)]  # 0-based
            
            ocr_response = self.mistral_client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{base64_pdf}"
                },
                pages=page_numbers,
                include_image_base64=False
            )
            
            # Combine pages
            combined_text = "\n\n".join([page.markdown for page in ocr_response.pages])
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                "mistral-ocr-latest",
                combined_text,
                processing_time,
                metadata={
                    "pages_processed": len(ocr_response.pages),
                    "model_used": "mistral-ocr-latest"
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return OCRResult("mistral-ocr-latest", "", processing_time, str(e))
    
    def test_gemini_model(self, model, model_name, image_paths):
        """Test a Gemini model"""
        print(f"🤖 Testing {model_name}...")
        start_time = time.time()
        
        try:
            images = [Image.open(path) for path in image_paths]
            
            instruction = """
Extract ALL text content from these French language textbook pages.

CRITICAL LAYOUT HANDLING:
1. **Multi-column text**: Process columns LEFT to RIGHT, TOP to BOTTOM
2. **Exercises**: Keep original numbering sequence exactly as shown
3. **Dialogues**: Maintain exact speaker order and conversation flow
4. **Tables**: Preserve structure and content
5. **Preserve exact exercise numbering** - do not "fix" what looks wrong

TEXTBOOK ELEMENTS TO PRESERVE:
- Unit headers and section titles
- Language points and grammar explanations  
- Dialogue conversations (exact speaker order!)
- Exercise questions (exact original numbering!)
- "Did you notice?" sections
- CD track references like (CD 1; 2)
- Verb conjugation information

OUTPUT: Clean text with preserved structure, no formatting markup needed.
Focus on ACCURACY - get the content and order exactly right.
"""
            
            response = model.generate_content([instruction] + images)
            ocr_text = response.text
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                model_name,
                ocr_text,
                processing_time,
                metadata={
                    "pages_processed": len(images),
                    "model_used": model_name
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return OCRResult(model_name, "", processing_time, str(e))
    
    def calculate_similarity_metrics(self, text1, text2):
        """Calculate detailed similarity metrics between two texts"""
        
        # Basic similarity
        similarity_ratio = difflib.SequenceMatcher(None, text1, text2).ratio()
        
        # Word-level comparison
        words1 = text1.lower().split()
        words2 = text2.lower().split()
        word_similarity = difflib.SequenceMatcher(None, words1, words2).ratio()
        
        # Line-level comparison
        lines1 = text1.split('\n')
        lines2 = text2.split('\n')
        line_similarity = difflib.SequenceMatcher(None, lines1, lines2).ratio()
        
        # Content preservation metrics
        def extract_key_content(text):
            # Extract exercises
            exercises = re.findall(r'Exercise \d+.*?(?=Exercise|\Z)', text, re.DOTALL | re.IGNORECASE)
            
            # Extract dialogues  
            dialogues = re.findall(r'Dialogue.*?(?=Language points|\Z)', text, re.DOTALL | re.IGNORECASE)
            
            # Extract CD references
            cd_refs = re.findall(r'\(CD \d+[;,]\s*\d+\)', text)
            
            # Extract French sentences (simple heuristic)
            french_sentences = re.findall(r'[A-Z][^.!?]*[éèêëàâäôöùûüçñ][^.!?]*[.!?]', text)
            
            return {
                'exercises': len(exercises),
                'dialogues': len(dialogues), 
                'cd_references': len(cd_refs),
                'french_sentences': len(french_sentences)
            }
        
        content1 = extract_key_content(text1)
        content2 = extract_key_content(text2)
        
        # Content preservation score
        content_scores = []
        for key in content1:
            if content1[key] == 0 and content2[key] == 0:
                content_scores.append(1.0)
            elif content1[key] == 0:
                content_scores.append(0.0)
            else:
                content_scores.append(min(content2[key] / content1[key], 1.0))
        
        content_preservation = sum(content_scores) / len(content_scores) if content_scores else 0
        
        # Exercise numbering accuracy (specific to our problem)
        exercise_accuracy = self.check_exercise_numbering(text1, text2)
        
        return {
            'overall_similarity': similarity_ratio,
            'word_similarity': word_similarity,
            'line_similarity': line_similarity,
            'content_preservation': content_preservation,
            'exercise_accuracy': exercise_accuracy,
            'content_analysis': {
                'ground_truth': content1,
                'extracted': content2
            }
        }
    
    def check_exercise_numbering(self, ground_truth, extracted):
        """Specific check for exercise numbering accuracy"""
        
        # Extract exercise numbers from both texts
        def extract_exercise_numbers(text):
            # Find exercise sections and extract the numbers that follow
            exercise_sections = re.findall(r'Exercise \d+.*?(?=Exercise|\Z)', text, re.DOTALL | re.IGNORECASE)
            all_numbers = []
            
            for section in exercise_sections:
                # Find numbered items (1, 2, 3, etc.)
                numbers = re.findall(r'^\s*(\d+)[.\s]', section, re.MULTILINE)
                all_numbers.extend([int(n) for n in numbers])
            
            return all_numbers
        
        truth_numbers = extract_exercise_numbers(ground_truth)
        extracted_numbers = extract_exercise_numbers(extracted)
        
        if not truth_numbers and not extracted_numbers:
            return 1.0
        elif not truth_numbers:
            return 0.0
        else:
            # Compare sequences
            sequence_match = truth_numbers == extracted_numbers
            return 1.0 if sequence_match else 0.0
    
    def run_comparison(self, start_page=20, end_page=22):
        """Run OCR comparison across all models"""
        
        print("🚀 OCR Model Comparison")
        print("=" * 50)
        print(f"📄 PDF: {self.pdf_path.name}")
        print(f"📄 Ground truth: {self.ground_truth_path.name}")
        print(f"📖 Pages: {start_page}-{end_page}")
        print()
        
        models_to_test = []
        
        # Add Mistral if available (commented out due to API issues)
        # if self.mistral_client:
        #     models_to_test.append(("mistral", None))
        
        # Add Gemini models if available
        available_gemini_models = []
        if self.gemini_2_5_pro:
            available_gemini_models.append(("gemini-2.5-pro", self.gemini_2_5_pro))
        if self.gemini_2_5_flash:
            available_gemini_models.append(("gemini-2.5-flash", self.gemini_2_5_flash))
        if self.gemini_2_0_flash:
            available_gemini_models.append(("gemini-2.0-flash", self.gemini_2_0_flash))
            
        if available_gemini_models:
            # Convert PDF to images for Gemini
            print("📷 Converting PDF to images for Gemini...")
            image_paths = self.convert_pdf_to_images(start_page, end_page)
            if image_paths:
                for model_name, model_obj in available_gemini_models:
                    models_to_test.append((model_name, {"images": image_paths, "model": model_obj}))
        
        if not models_to_test:
            print("❌ No API keys configured")
            return
        
        # Test each model
        with alive_bar(
            len(models_to_test),
            title="🔍 Testing models",
            spinner="waves",
            dual_line=True,
            force_tty=True
        ) as bar:
            
            for model_info, data in models_to_test:
                bar.text = f"🤖 Testing {model_info}"
                
                if model_info == "mistral":
                    result = self.test_mistral_ocr(start_page, end_page)
                elif model_info in ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"]:
                    result = self.test_gemini_model(data["model"], model_info, data["images"])
                
                self.results.append(result)
                
                bar.text = f"✅ {model_info} complete ({result.processing_time:.1f}s)"
                bar()
                time.sleep(1)  # Rate limiting
        
        # Generate comparison report
        self.generate_comparison_report()
        
        return self.results
    
    def generate_comparison_report(self):
        """Generate detailed comparison report"""
        
        print("\n📊 Generating comparison report...")
        
        # Calculate metrics for each result
        detailed_results = []
        
        for result in self.results:
            if result.error:
                metrics = {
                    'overall_similarity': 0,
                    'word_similarity': 0,
                    'line_similarity': 0,
                    'content_preservation': 0,
                    'exercise_accuracy': 0,
                    'error': result.error
                }
            else:
                metrics = self.calculate_similarity_metrics(self.ground_truth, result.text)
            
            detailed_results.append({
                'model': result.model_name,
                'processing_time': result.processing_time,
                'text_length': len(result.text),
                'metrics': metrics,
                'metadata': result.metadata
            })
        
        # Sort by overall quality (composite score)
        def quality_score(result):
            m = result['metrics']
            if 'error' in m:
                return 0
            # Weighted composite score
            return (
                m['overall_similarity'] * 0.25 +
                m['content_preservation'] * 0.35 +
                m['exercise_accuracy'] * 0.25 +
                m['word_similarity'] * 0.15
            )
        
        detailed_results.sort(key=quality_score, reverse=True)
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'comparison_summary': {
                'pdf_file': str(self.pdf_path),
                'ground_truth': str(self.ground_truth_path),
                'models_tested': len(self.results),
                'successful_models': len([r for r in detailed_results if 'error' not in r['metrics']])
            },
            'results': detailed_results,
            'ranking': [r['model'] for r in detailed_results]
        }
        
        # Save detailed report
        report_file = self.session_dir / "comparison_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Save individual OCR outputs
        for i, result in enumerate(self.results):
            output_file = self.session_dir / f"{result.model_name}_output.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                if result.error:
                    f.write(f"# Error\n\n{result.error}")
                else:
                    f.write(result.text)
        
        # Print summary
        print(f"\n✅ Comparison Complete!")
        print(f"📊 Report: {report_file}")
        print(f"📁 Session: {self.session_dir}")
        print()
        
        print("🏆 RANKING (Best to Worst):")
        for i, result in enumerate(detailed_results, 1):
            metrics = result['metrics']
            if 'error' in metrics:
                print(f"{i}. {result['model']} - ❌ {metrics['error']}")
            else:
                score = quality_score(result)
                print(f"{i}. {result['model']} - Score: {score:.3f}")
                print(f"   📊 Similarity: {metrics['overall_similarity']:.3f}")
                print(f"   📝 Content: {metrics['content_preservation']:.3f}")
                print(f"   🔢 Exercises: {metrics['exercise_accuracy']:.3f}")
                print(f"   ⏱️  Time: {result['processing_time']:.1f}s")
                print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OCR Model Comparison")
    parser.add_argument("pdf_file", help="Input PDF file")
    parser.add_argument("ground_truth", help="Ground truth markdown file")
    parser.add_argument("--start-page", type=int, default=20, help="Start page")
    parser.add_argument("--end-page", type=int, default=22, help="End page")
    
    args = parser.parse_args()
    
    # Validate files
    if not Path(args.pdf_file).exists():
        print(f"❌ PDF not found: {args.pdf_file}")
        return
    
    if not Path(args.ground_truth).exists():
        print(f"❌ Ground truth not found: {args.ground_truth}")
        return
    
    # Run comparison
    comparison = OCRComparison(args.pdf_file, args.ground_truth)
    results = comparison.run_comparison(args.start_page, args.end_page)
    
    if results:
        print(f"🎯 Tested {len(results)} models successfully!")
    else:
        print("❌ No models could be tested")


if __name__ == "__main__":
    main()