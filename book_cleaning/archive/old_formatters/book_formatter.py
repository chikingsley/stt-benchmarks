#!/usr/bin/env python3
"""
Colloquial French Book Formatter
Automates formatting of Units 2-16 using Mistral API with infinite retry pattern
"""

import os
import re
import time
from pathlib import Path
from datetime import datetime
from mistralai import Mistral
from alive_progress import alive_bar


class BookFormatter:
    def __init__(self, input_file, output_file):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        
        # Infinite retry pattern: medium -> large -> medium -> large...
        self.models = ["mistral-medium-latest", "mistral-large-latest"]
        self.current_model_idx = 0
        
        # Get API key from environment
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY environment variable required")
        
        self.client = Mistral(api_key=api_key)
        self.batch_size = 100
        
    def get_current_model(self):
        """Get current model and rotate for next call"""
        model = self.models[self.current_model_idx]
        self.current_model_idx = (self.current_model_idx + 1) % len(self.models)
        return model
        
    def call_mistral_with_retries(self, prompt, context):
        """Call Mistral with infinite retries, alternating between models"""
        attempt = 1
        
        while True:
            model = self.get_current_model()
            try:
                response = self.client.chat.complete(
                    model=model,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": context}
                    ],
                    temperature=0.1,
                    max_tokens=4000
                )
                return response.choices[0].message.content, model, attempt
                
            except Exception as e:
                print(f"  ❌ {model} failed (attempt {attempt}): {str(e)[:50]}...")
                attempt += 1
                time.sleep(min(2 ** min(attempt-1, 6), 60))  # Exponential backoff, max 60s
                continue
    
    def create_formatting_prompt(self):
        """Create the system prompt for formatting"""
        return """You are a textbook formatter specializing in language learning materials. 

Your task is to format raw text from a French textbook into clean Markdown following these patterns:

**Section Types & Formatting:**

1. **Unit Headers**: 
   ```
   ## Unit [X] Title (French Title)
   ```

2. **Dialogues**:
   ```
   ### Dialogue X - Title (CD X; X)
   [French text with CD references]
   ```

3. **Language Points**:
   ```
   ### Language points - Topic (CD X; X)
   [Content with bold **key terms**]
   ```

4. **Exercises**:
   ```
   #### Exercise X (CD X; X)
   [Numbered content]
   ```

5. **Grammar Sections**:
   ```
   ### The verb [verb] (translation)
   [Conjugation tables and examples]
   ```

**Key Rules:**
- Preserve all French accents and special characters
- Keep CD track references like "(CD 1; 2)"
- Use **bold** for key terms and headers
- Clean up OCR artifacts (weird spacing, broken words)
- Remove page numbers and headers
- Maintain proper markdown hierarchy
- Keep dialogue format consistent
- Preserve exercise numbering

**Input**: Raw text that needs formatting
**Output**: Clean markdown following the patterns above

Format the following text:"""

    def load_and_split_content(self):
        """Load content and split into batches"""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find where Unit 1 ends to start processing from Unit 2
        unit_2_start = None
        for i, line in enumerate(lines):
            if re.search(r'unit\s*\[?2\]?', line.lower()) and 'premiers contacts' not in line.lower():
                unit_2_start = i
                break
        
        if unit_2_start is None:
            print("⚠️ Could not find Unit 2 start, processing from line 500")
            unit_2_start = 500
        
        # Split into batches
        content_lines = lines[unit_2_start:]
        batches = []
        
        for i in range(0, len(content_lines), self.batch_size):
            batch = content_lines[i:i + self.batch_size]
            batches.append(''.join(batch))
        
        return batches, unit_2_start
    
    def process_batches(self):
        """Process all batches with progress tracking"""
        prompt = self.create_formatting_prompt()
        batches, start_line = self.load_and_split_content()
        
        print(f"📚 Processing {len(batches)} batches starting from line {start_line}")
        print(f"🤖 Using models: {' → '.join(self.models)} (infinite retry)")
        print()
        
        formatted_results = []
        success_count = 0
        total_attempts = 0
        
        with alive_bar(
            len(batches),
            title="📦 Formatting batches",
            spinner="waves",
            dual_line=True,
            force_tty=True,
            refresh_secs=0.05
        ) as bar:
            
            for i, batch in enumerate(batches):
                bar.text = f"📝 Processing batch {i+1}/{len(batches)}"
                
                # Format batch with retries
                formatted_text, model_used, attempts = self.call_mistral_with_retries(
                    prompt, batch
                )
                
                formatted_results.append(formatted_text)
                success_count += 1
                total_attempts += attempts
                
                # Update progress
                bar.text = f"✅ {success_count}/{len(batches)} | 🔄 {total_attempts} total attempts"
                bar()
                
                # Brief pause between batches
                time.sleep(0.5)
        
        return formatted_results, success_count, total_attempts
    
    def save_results(self, formatted_results, success_count, total_attempts):
        """Save formatted results to output file"""
        
        # Read Unit 1 content to preserve it
        with open(self.input_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Find Unit 1 end
        unit_1_match = re.search(r'(.*?)(?=unit\s*\[?2\]?)', original_content, re.DOTALL | re.IGNORECASE)
        unit_1_content = unit_1_match.group(1) if unit_1_match else ""
        
        # Combine Unit 1 + formatted content
        final_content = unit_1_content.rstrip() + "\n\n"
        final_content += "\n\n".join(formatted_results)
        
        # Save to output file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        # Generate summary
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary = f"""
# Book Formatting Summary

**Completed**: {timestamp}
**Batches processed**: {success_count}
**Total API attempts**: {total_attempts}
**Input file**: {self.input_file.name}
**Output file**: {self.output_file.name}
**Models used**: {' ↔ '.join(self.models)}

✅ Successfully formatted Units 2-16 with infinite retry pattern
"""
        
        summary_file = self.output_file.parent / "formatting_summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        return summary_file

    def run(self):
        """Main execution method"""
        print("📖 Colloquial French Book Formatter")
        print("=" * 50)
        print(f"📄 Input: {self.input_file.name}")
        print(f"💾 Output: {self.output_file.name}")
        print()
        
        start_time = time.time()
        
        # Process all batches
        formatted_results, success_count, total_attempts = self.process_batches()
        
        # Save results
        summary_file = self.save_results(formatted_results, success_count, total_attempts)
        
        duration = time.time() - start_time
        
        print()
        print("✅ Formatting Complete!")
        print(f"⏱️  Total time: {duration:.1f}s")
        print(f"📊 Summary: {summary_file}")
        print(f"📚 Formatted book: {self.output_file}")


def main():
    input_file = "/Volumes/simons-enjoyment/GitHub/whisperkittools/book_cleaning/colloqual_french.md"
    output_file = "/Volumes/simons-enjoyment/GitHub/whisperkittools/book_cleaning/colloqual_french_formatted.md"
    
    if not Path(input_file).exists():
        print(f"❌ Input file not found: {input_file}")
        return
    
    formatter = BookFormatter(input_file, output_file)
    formatter.run()


if __name__ == "__main__":
    main()