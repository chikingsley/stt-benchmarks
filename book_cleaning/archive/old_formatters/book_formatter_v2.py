#!/usr/bin/env python3
"""
Book Formatter V2 - OCR Integration + Structure Analysis
Implements: OCR → Structure Analysis → YAML Generation → Formatting Pipeline
"""

import os
import re
import time
import yaml
import json
import argparse
import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime
from mistralai import Mistral
from alive_progress import alive_bar
from PIL import Image
import base64
import io


class BookFormatterV2:
    def __init__(self, input_file, output_dir="./formatted_output"):
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Models: OCR and formatting
        self.ocr_model = "mistral-ocr-latest"
        self.format_models = ["mistral-medium-latest", "mistral-large-latest"]
        self.current_model_idx = 0
        
        # API setup
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY environment variable required")
        
        self.client = Mistral(api_key=api_key)
        
        # Session setup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"session_{timestamp}"
        self.session_dir.mkdir(exist_ok=True)
        
        self.token_usage = {"ocr": 0, "analysis": 0, "formatting": 0}
        
    def get_format_model(self):
        """Get current formatting model and rotate"""
        model = self.format_models[self.current_model_idx]
        self.current_model_idx = (self.current_model_idx + 1) % len(self.format_models)
        return model
    
    def encode_pdf_for_ocr(self, pdf_path):
        """Encode entire PDF to base64 for OCR processing"""
        try:
            with open(pdf_path, "rb") as pdf_file:
                return base64.b64encode(pdf_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding PDF: {e}")
            return None
    
    def ocr_pdf_document(self, start_page=None, end_page=None):
        """OCR the PDF document using mistral-ocr-latest"""
        
        print(f"📄 OCR processing: {self.input_file.name}")
        
        # Check file size limit (50MB)
        file_size_mb = self.input_file.stat().st_size / (1024 * 1024)
        if file_size_mb > 50:
            print(f"⚠️ PDF size ({file_size_mb:.1f}MB) exceeds 50MB limit")
            print("  Consider splitting the PDF or processing page by page")
            return None
        
        # Encode PDF
        print("📦 Encoding PDF...")
        base64_pdf = self.encode_pdf_for_ocr(self.input_file)
        if not base64_pdf:
            return None
        
        print(f"🔍 Sending to OCR ({file_size_mb:.1f}MB)...")
        
        try:
            # Use the OCR-specific API
            ocr_response = self.client.ocr.process(
                model=self.ocr_model,
                document={
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{base64_pdf}"
                },
                include_image_base64=False  # We don't need image data for text processing
            )
            
            print(f"✅ OCR complete! Processed {len(ocr_response.pages)} pages")
            
            # Track token usage (estimate)
            total_chars = sum(len(page.markdown) for page in ocr_response.pages)
            self.token_usage["ocr"] += total_chars * 0.25  # Rough token estimate
            
            return ocr_response
            
        except Exception as e:
            print(f"❌ OCR failed: {str(e)}")
            return None
    
    def filter_pages(self, ocr_response, start_page=None, end_page=None):
        """Filter OCR results to specific page range"""
        if not start_page and not end_page:
            return ocr_response.pages
        
        filtered_pages = []
        for page in ocr_response.pages:
            if start_page and page.index < start_page:
                continue
            if end_page and page.index > end_page:
                continue
            filtered_pages.append(page)
        
        return filtered_pages
    
    def call_mistral_with_retries(self, messages, model_type="format"):
        """Call Mistral with infinite retries for formatting"""
        attempt = 1
        
        while True:
            model = self.get_format_model()
                
            try:
                response = self.client.chat.complete(
                    model=model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=4000
                )
                
                # Track token usage
                content = response.choices[0].message.content
                estimated_tokens = len(content.split()) * 1.3
                self.token_usage[model_type if model_type in self.token_usage else "formatting"] += estimated_tokens
                
                return content, model, attempt
                
            except Exception as e:
                print(f"  ❌ {model} failed (attempt {attempt}): {str(e)[:50]}...")
                attempt += 1
                time.sleep(min(2 ** min(attempt-1, 6), 60))
                continue
    
    def analyze_book_structure(self, sample_pages=10):
        """Analyze book structure from OCR output to generate YAML configuration"""
        
        print("🔍 Analyzing book structure from PDF...")
        
        # OCR the entire document first
        ocr_response = self.ocr_pdf_document()
        if not ocr_response:
            print("❌ Failed to OCR PDF for structure analysis")
            return None, None
        
        # Use first N pages for analysis
        sample_pages_data = self.filter_pages(ocr_response, 1, sample_pages)
        
        # Combine sample text for analysis
        sample_text = "\n\n".join([
            f"=== PAGE {page.index} ===\n{page.markdown}" 
            for page in sample_pages_data
        ])
        
        # Save full OCR for reference
        ocr_file = self.session_dir / "full_ocr_output.json"
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
            }, f, indent=2)
        print(f"💾 Full OCR saved: {ocr_file}")
        
        analysis_prompt = """You are a textbook structure analyzer. Analyze this sample text and create a YAML configuration for automated formatting.

Your task:
1. Identify section patterns (units, dialogues, exercises, language points)
2. Determine heading hierarchy 
3. Find formatting patterns (bold terms, italics, special formatting)
4. Detect numbering schemes
5. Identify reference patterns (CD tracks, page numbers, etc.)

Output a YAML configuration like this:

```yaml
book_info:
  title: "Book Title"
  type: "language_textbook"
  language: "french"

section_patterns:
  unit: "Unit \\[?(\\d+)\\]?"
  dialogue: "Dialogue \\d+"
  exercise: "Exercise \\d+"
  language_points: "Language points"

formatting_rules:
  preserve_bold: true
  bold_terms: ["UN", "UNE", "LE", "LA"]  # Common terms to bold
  heading_levels:
    unit: 2
    dialogue: 3  
    exercise: 4
  
reference_patterns:
  cd_tracks: "\\(CD \\d+;\\s*\\d+\\)"
  
special_sections:
  - "Did you notice"
  - "Grammar rules"
  - "Vocabulary"
```

Analyze this sample:"""

        messages = [
            {"role": "system", "content": analysis_prompt},
            {"role": "user", "content": sample_text}
        ]
        
        yaml_config, model, attempts = self.call_mistral_with_retries(messages, "analysis")
        
        # Extract YAML from response
        yaml_match = re.search(r'```yaml\n(.*?)\n```', yaml_config, re.DOTALL)
        if yaml_match:
            yaml_content = yaml_match.group(1)
        else:
            yaml_content = yaml_config
        
        # Fix common YAML regex escaping issues
        yaml_content = yaml_content.replace(r'(\d+)', r'\\(\\d+\\)')
        yaml_content = yaml_content.replace(r'\(CD \d+;\s*\d+\)', r'\\(CD \\d+;\\s*\\d+\\)')
        yaml_content = yaml_content.replace(r'\(\d+\)', r'\\(\\d+\\)')
            
        # Save generated config
        config_path = self.session_dir / "generated_config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
            
        print(f"📋 Generated config: {config_path}")
        print(f"🤖 Analysis by: {model} ({attempts} attempts)")
        
        # Store OCR response for later use
        self.cached_ocr_response = ocr_response
        
        return yaml_content, config_path
    
    def load_or_generate_config(self, config_path=None):
        """Load existing config or generate new one"""
        
        if config_path:
            config_file = Path(config_path)
            if config_file.exists():
                print(f"📋 Loading existing config: {config_path}")
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        return yaml.safe_load(f), config_file
                except yaml.YAMLError as e:
                    print(f"⚠️ Config file has YAML errors: {e}")
                    print("📝 Please fix the config file manually")
                    return None, config_file
            else:
                print(f"⚠️ Config file not found: {config_path}")
        
        print("🔍 No valid config provided, analyzing book structure...")
        yaml_content, config_path = self.analyze_book_structure()
        try:
            return yaml.safe_load(yaml_content), config_path
        except yaml.YAMLError as e:
            print(f"⚠️ YAML parsing error: {e}")
            print("📝 Raw config saved, please review and fix manually")
            return None, config_path
    
    def create_enhanced_formatting_prompt(self, config):
        """Create formatting prompt based on YAML config"""
        
        book_info = config.get('book_info', {})
        section_patterns = config.get('section_patterns', {})
        formatting_rules = config.get('formatting_rules', {})
        
        prompt = f"""You are formatting a {book_info.get('type', 'textbook')} in {book_info.get('language', 'unknown language')}.

CRITICAL REQUIREMENTS:
1. **Preserve ALL content** - do not omit any text, translations, or explanations
2. **Maintain exact formatting** - bold terms, italics, special characters
3. **Keep all translations** - English translations must be preserved
4. **Preserve section headers** - dialogue names, exercise titles, etc.

SECTION PATTERNS:
"""
        
        for section, pattern in section_patterns.items():
            level = formatting_rules.get('heading_levels', {}).get(section, 3)
            prompt += f"- {section}: {'#' * level} [formatted title]\n"
        
        if formatting_rules.get('bold_terms'):
            prompt += f"\nBOLD THESE TERMS: {', '.join(formatting_rules['bold_terms'])}\n"
        
        prompt += """
SPECIFIC FORMATTING REQUIREMENTS:
- French examples: **bold** format (e.g. **Vous êtes français.**)
- English translations: _italics_ format (e.g. _You are French._)
- Grammatical terms: **bold** (e.g. **habiter**, **-er**, **je**, **tu**)
- Section headers: Clean format "Language points - Topic" not "**Language points**"
- Dialogues: Simple speaker format, not tables
- Verb conjugations: Simple list format, not complex tables
- Exercise numbering: Keep original order
- Preserve ALL "Did you notice?" sections
- Keep CD track references like (CD 1; 2)
- Preserve ALL English translations

CRITICAL: Match the educational textbook style with clear, consistent formatting.

Format this text maintaining ALL content:"""
        
        return prompt
    
    def format_with_config(self, text_batch, config):
        """Format text batch using YAML configuration"""
        
        prompt = self.create_enhanced_formatting_prompt(config)
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text_batch}
        ]
        
        formatted_text, model, attempts = self.call_mistral_with_retries(messages, "formatting")
        return formatted_text, model, attempts
    
    def process_with_pipeline(self, mode="full", start_page=None, end_page=None, config_path=None, preview=False):
        """Main processing pipeline with OCR → Analysis → Format"""
        
        print("🚀 Book Formatter V2 - PDF OCR + Structure Pipeline")
        print("=" * 60)
        print(f"📄 Input PDF: {self.input_file.name}")
        
        # Step 1: Load or generate configuration
        config, config_file = self.load_or_generate_config(config_path)
        if not config:
            print("❌ Failed to load/generate config")
            return
            
        print(f"📋 Using config: {config_file}")
        print("\n📖 Review the generated config above and press Enter to continue (or Ctrl+C to abort)")
        input("Press Enter to proceed...")
        
        # Step 2: Determine pages to process
        if mode == "analyze":
            print("✅ Analysis complete - config generated")
            return config_file
        
        # Step 3: Get OCR data (use cached if available from analysis)
        if hasattr(self, 'cached_ocr_response'):
            print("📄 Using cached OCR data from analysis")
            ocr_response = self.cached_ocr_response
        else:
            print("📄 Running OCR on full document")
            ocr_response = self.ocr_pdf_document()
            if not ocr_response:
                print("❌ OCR failed")
                return
        
        # Filter pages if needed
        if start_page or end_page:
            pages_to_process = self.filter_pages(ocr_response, start_page, end_page)
            print(f"📄 Processing pages {start_page or 1}-{end_page or 'end'} ({len(pages_to_process)} pages)")
        else:
            pages_to_process = ocr_response.pages
            print(f"📄 Processing all {len(pages_to_process)} pages")
        
        if preview:
            print(f"\n📄 Preview - would process {len(pages_to_process)} pages")
            if pages_to_process:
                print(f"🎯 First page sample: {pages_to_process[0].markdown[:500]}...")
            return
        
        # Step 4: Format OCR results using config
        formatted_results = []
        
        print(f"\n🎨 Formatting {len(pages_to_process)} pages with enhanced rules")
        
        with alive_bar(
            len(pages_to_process),
            title="🎨 Enhanced Formatting",
            spinner="waves",
            dual_line=True,
            force_tty=True
        ) as bar:
            
            for page in pages_to_process:
                page_num = page.index
                page_text = page.markdown
                
                bar.text = f"🎨 Page {page_num} | Tokens: {sum(self.token_usage.values()):.0f}"
                
                formatted_text, model, attempts = self.format_with_config(page_text, config)
                
                formatted_results.append({
                    "page": page_num,
                    "formatted_text": formatted_text,
                    "model": model,
                    "attempts": attempts
                })
                
                bar()
                time.sleep(0.5)  # Rate limiting
        
        # Step 5: Save results
        self.save_formatted_results(formatted_results, pages_to_process, config_file)
        
        return self.session_dir / f"{self.input_file.stem}_formatted_v2.md"
    
    def save_formatted_results(self, formatted_results, ocr_pages, config_file):
        """Save all results in organized structure"""
        
        # Combined output
        combined_content = "\n\n".join([r["formatted_text"] for r in formatted_results])
        output_file = self.session_dir / f"{self.input_file.stem}_formatted_v2.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(combined_content)
        
        # Individual page results
        pages_dir = self.session_dir / "pages"
        pages_dir.mkdir(exist_ok=True)
        
        for result in formatted_results:
            page_file = pages_dir / f"page_{result['page']:03d}.md"
            with open(page_file, 'w', encoding='utf-8') as f:
                f.write(result["formatted_text"])
        
        # OCR results for reference
        ocr_dir = self.session_dir / "ocr_raw"
        ocr_dir.mkdir(exist_ok=True)
        
        for page in ocr_pages:
            ocr_file = ocr_dir / f"page_{page.index:03d}_ocr.md"
            with open(ocr_file, 'w', encoding='utf-8') as f:
                f.write(page.markdown)
        
        # Generate processing stats
        stats = {
            "pages_processed": len(formatted_results),
            "total_attempts": sum(r["attempts"] for r in formatted_results),
            "models_used": {}
        }
        
        for result in formatted_results:
            model = result["model"]
            stats["models_used"][model] = stats["models_used"].get(model, 0) + 1
        
        # Generate comprehensive report
        self.generate_processing_report(stats, config_file, output_file)
        
        print(f"\n✅ Processing Complete!")
        print(f"📄 Main output: {output_file}")
        print(f"📁 Individual pages: {pages_dir}")
        print(f"📄 Raw OCR: {ocr_dir}")
        print(f"📊 Total tokens used: {sum(self.token_usage.values()):.0f}")
    
    def generate_processing_report(self, stats, config_file, output_file):
        """Generate detailed processing report"""
        
        report = {
            "session_info": {
                "timestamp": datetime.now().isoformat(),
                "input_file": str(self.input_file),
                "output_file": str(output_file),
                "config_used": str(config_file)
            },
            "processing_stats": stats,
            "token_usage": self.token_usage,
            "estimated_cost": {
                "ocr": self.token_usage.get("ocr", 0) * 0.002 / 1000,
                "formatting": (self.token_usage.get("analysis", 0) + self.token_usage.get("formatting", 0)) * 0.002 / 1000,
                "total": sum(self.token_usage.values()) * 0.002 / 1000
            },
            "rate_limit_info": {
                "tokens_used": sum(self.token_usage.values()),
                "percent_of_minute_limit": (sum(self.token_usage.values()) / 500000) * 100,
                "percent_of_month_limit": (sum(self.token_usage.values()) / 1000000000) * 100
            }
        }
        
        report_file = self.session_dir / "processing_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Report saved: {report_file}")


def main():
    parser = argparse.ArgumentParser(description="Book Formatter V2 - PDF OCR + Structure Analysis")
    parser.add_argument("input_file", help="Input PDF file")
    parser.add_argument("--mode", choices=["analyze", "sample", "full"], default="sample", 
                       help="Processing mode: analyze=structure only, sample=test pages, full=entire book")
    parser.add_argument("--start-page", type=int, help="Start page number")
    parser.add_argument("--end-page", type=int, help="End page number") 
    parser.add_argument("--config", help="YAML config file path")
    parser.add_argument("--preview", action="store_true", help="Preview only, don't process")
    parser.add_argument("--output-dir", default="./formatted_output", help="Output directory")
    
    args = parser.parse_args()
    
    # Convert to absolute path for consistent handling
    input_path = Path(args.input_file).resolve()
    
    if not input_path.exists():
        print(f"❌ Input file not found: {args.input_file}")
        print(f"   Looked for: {input_path}")
        return
    
    if not input_path.suffix.lower() == '.pdf':
        print(f"❌ V2 requires PDF input. Found: {input_path.suffix}")
        return
    
    # Also resolve output directory
    output_dir = Path(args.output_dir).resolve()
    
    formatter = BookFormatterV2(input_path, output_dir)
    
    formatter.process_with_pipeline(
        mode=args.mode,
        start_page=args.start_page,
        end_page=args.end_page,
        config_path=args.config,
        preview=args.preview
    )


if __name__ == "__main__":
    main()