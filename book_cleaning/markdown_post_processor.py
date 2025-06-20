#!/usr/bin/env python3
"""
Markdown Post-Processor for French Textbook OCR
Handles intelligent paragraph merging, header removal, and auto-formatting
"""

import re
from pathlib import Path
import json
from typing import List, Tuple
from datetime import datetime


class MarkdownPostProcessor:
    def __init__(self):
        self.stats = {
            "paragraphs_merged": 0,
            "headers_removed": 0,
            "formatting_fixes": 0,
            "lines_processed": 0
        }
    
    def process_file(self, input_path: Path, output_path: Path = None) -> Path:
        """Process a markdown file and apply all fixes"""
        
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_cleaned.md"
        
        print(f"📄 Processing: {input_path.name}")
        
        # Read the file
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply all processing steps
        content = self.remove_page_headers(content)
        content = self.merge_paragraphs(content)
        content = self.apply_markdown_formatting(content)
        
        # Write the cleaned file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Save processing stats
        self.save_stats(output_path.parent)
        
        print(f"✅ Saved to: {output_path.name}")
        print(f"📊 Stats: {self.stats['paragraphs_merged']} paragraphs merged, "
              f"{self.stats['headers_removed']} headers removed")
        
        return output_path
    
    def remove_page_headers(self, content: str) -> str:
        """Remove page headers like 'Unit 2: In town 23'"""
        
        lines = content.split('\n')
        cleaned_lines = []
        
        # Common header patterns
        patterns = [
            # Unit X: Title PageNum
            r'^Unit\s+\d+:\s+[A-Za-z\s]+\s+\d+\s*$',
            # Unit X: Title (French) PageNum  
            r'^Unit\s+\d+:\s+[A-Za-zÀ-ÿ\s]+\s+\d+\s*$',
            # Just page numbers at start/end of line
            r'^\d{1,3}\s*$',
            # Page X
            r'^Page\s+\d+\s*$',
            r'^\*\*Page\s+\d+\*\*\s*$',
        ]
        
        for line in lines:
            # Check if line matches any header pattern
            is_header = False
            for pattern in patterns:
                if re.match(pattern, line.strip()):
                    is_header = True
                    self.stats["headers_removed"] += 1
                    break
            
            if not is_header:
                cleaned_lines.append(line)
            
        return '\n'.join(cleaned_lines)
    
    def merge_paragraphs(self, content: str) -> str:
        """Intelligently merge lines that belong to the same paragraph"""
        
        lines = content.split('\n')
        merged_lines = []
        current_paragraph = []
        
        for i, line in enumerate(lines):
            line = line.rstrip()
            self.stats["lines_processed"] += 1
            
            # Skip empty lines
            if not line:
                if current_paragraph:
                    # End current paragraph
                    merged_lines.append(' '.join(current_paragraph))
                    current_paragraph = []
                merged_lines.append('')
                continue
            
            # Check if this is a special line that shouldn't be merged
            if self.is_special_line(line):
                if current_paragraph:
                    merged_lines.append(' '.join(current_paragraph))
                    current_paragraph = []
                merged_lines.append(line)
                continue
            
            # Check if line should continue previous paragraph
            if current_paragraph and self.should_merge_with_previous(current_paragraph[-1], line):
                # Handle split formatting (bold/italic)
                merged_line = self.fix_split_formatting(current_paragraph[-1], line)
                if merged_line:
                    current_paragraph[-1] = merged_line
                else:
                    current_paragraph.append(line)
                self.stats["paragraphs_merged"] += 1
            else:
                # Start new paragraph or continue current
                if current_paragraph and self.ends_sentence(current_paragraph[-1]):
                    merged_lines.append(' '.join(current_paragraph))
                    current_paragraph = [line]
                else:
                    current_paragraph.append(line)
        
        # Don't forget last paragraph
        if current_paragraph:
            merged_lines.append(' '.join(current_paragraph))
        
        return '\n'.join(merged_lines)
    
    def is_special_line(self, line: str) -> bool:
        """Check if line is special and shouldn't be merged"""
        
        special_patterns = [
            r'^#+\s',  # Headers
            r'^\*\*[A-Z]',  # Bold section headers
            r'^---+$',  # Horizontal rules
            r'^\|',  # Table rows
            r'^\d+\.\s',  # Numbered lists
            r'^-\s',  # Bullet points
            r'^\*\s',  # Bullet points
            r'^[A-Z][A-Z\s]+:',  # Speaker labels (ANNE:, RECEPTIONIST:)
            r'^Exercise\s+\d+',  # Exercise headers
            r'^\*\*Exercise\s+\d+',  # Bold exercise headers
            r'^Example:',  # Example labels
            r'^\*\*.*\*\*$',  # Full bold lines
        ]
        
        return any(re.match(pattern, line.strip()) for pattern in special_patterns)
    
    def should_merge_with_previous(self, prev_line: str, current_line: str) -> bool:
        """Determine if current line should merge with previous"""
        
        # Don't merge if previous ends with sentence terminator
        if self.ends_sentence(prev_line):
            return False
        
        # Don't merge if current starts with capital after period
        if re.match(r'^[A-Z]', current_line) and prev_line.rstrip().endswith('.'):
            return False
        
        # Merge if previous line ends mid-word (hyphenated)
        if prev_line.rstrip().endswith('-'):
            return True
        
        # Merge if current line starts with lowercase
        if re.match(r'^[a-zà-ÿ]', current_line):
            return True
        
        # Merge if previous line seems incomplete
        if not re.search(r'[.!?:;]$', prev_line.rstrip()):
            # But not if current is clearly a new element
            if not self.is_special_line(current_line):
                return True
        
        return False
    
    def ends_sentence(self, line: str) -> bool:
        """Check if line ends a complete sentence"""
        
        line = line.rstrip()
        # Check for sentence endings
        if re.search(r'[.!?]\s*$', line):
            return True
        # Check for colon (often ends introductory text)
        if line.endswith(':'):
            return True
        return False
    
    def fix_split_formatting(self, prev_line: str, current_line: str) -> str:
        """Fix formatting split across lines"""
        
        # Check for split bold formatting
        if prev_line.rstrip().endswith('**') and current_line.startswith('**'):
            # Remove trailing ** from prev and leading ** from current
            return prev_line.rstrip()[:-2] + ' ' + current_line[2:]
        
        # Check for incomplete bold
        if re.search(r'\*\*[^*]+$', prev_line) and not current_line.startswith('**'):
            # Bold started but not closed
            if '**' in current_line:
                return prev_line + ' ' + current_line
        
        return None
    
    def apply_markdown_formatting(self, content: str) -> str:
        """Apply consistent markdown formatting rules"""
        
        # Ensure consistent spacing around headers
        content = re.sub(r'(^|\n)(#+)(\S)', r'\1\2 \3', content, flags=re.MULTILINE)
        
        # Ensure blank lines around headers
        content = re.sub(r'(^|\n)(#+\s+[^\n]+)\n(?!\n)', r'\1\2\n\n', content, flags=re.MULTILINE)
        
        # Fix multiple blank lines (max 2)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Ensure consistent list formatting
        content = re.sub(r'^(\d+)\.\s*', r'\1. ', content, flags=re.MULTILINE)
        content = re.sub(r'^-\s*', r'- ', content, flags=re.MULTILINE)
        
        # Fix spacing around horizontal rules
        content = re.sub(r'(\n|^)(-{3,})(\n|$)', r'\1\n\2\n\3', content)
        
        # Clean up extra spaces
        content = re.sub(r' +', ' ', content)
        content = re.sub(r'\t+', ' ', content)
        
        # Ensure file ends with newline
        if not content.endswith('\n'):
            content += '\n'
        
        self.stats["formatting_fixes"] = len(re.findall(r'(^|\n)#+\s', content))
        
        return content
    
    def save_stats(self, output_dir: Path):
        """Save processing statistics"""
        
        stats_file = output_dir / "post_processing_stats.json"
        
        stats_data = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "processing_summary": {
                "total_lines": self.stats["lines_processed"],
                "efficiency": f"{(self.stats['paragraphs_merged'] / max(1, self.stats['lines_processed'])) * 100:.1f}%"
            }
        }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, indent=2)


def main():
    """Test the post-processor on Unit 2 output"""
    
    import argparse
    parser = argparse.ArgumentParser(description='Post-process OCR markdown output')
    parser.add_argument('input_file', help='Input markdown file to process')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    
    args = parser.parse_args()
    
    processor = MarkdownPostProcessor()
    input_path = Path(args.input_file)
    output_path = Path(args.output) if args.output else None
    
    processor.process_file(input_path, output_path)


if __name__ == "__main__":
    main()