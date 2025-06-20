#!/usr/bin/env python3
"""
Quick test version of comprehensive benchmark - Kyutai only
"""

import subprocess
import sys
import time
import json
import re
import logging
import warnings
import os
from pathlib import Path
from datetime import datetime
import jiwer

# Suppress warnings and verbose logging
warnings.filterwarnings('ignore')
logging.getLogger('whisperkit').setLevel(logging.ERROR)
logging.getLogger('transformers').setLevel(logging.ERROR)

class STTBenchmark:
    def __init__(self, audio_path, reference_text=None):
        self.audio_path = Path(audio_path)
        self.reference_text = reference_text
        
        # Create timestamped results directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_dir = Path("./outputs/benchmark_results") / f"benchmark_{timestamp}"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Model configurations - Kyutai only
        self.kyutai_models = {
            "kyutai-standard": {
                "command": [sys.executable, "-m", "moshi.run_inference", "--hf-repo", "kyutai/stt-1b-en_fr", "--device", "cpu"],
                "description": "Kyutai 1B PyTorch (Standard)",
                "framework": "PyTorch"
            }
        }
        
        self.results = {}
        
    def set_reference_text(self, text):
        """Set the reference text for WER calculation"""
        self.reference_text = self.clean_text(text)
        
        # Save reference
        ref_path = self.results_dir / "reference_transcription.txt"
        with open(ref_path, 'w', encoding='utf-8') as f:
            f.write(self.reference_text)
        
    def clean_text(self, text):
        """Clean text for WER calculation"""
        # Remove timestamps and special markers
        cleaned = re.sub(r'<\|[^|]*\|>', '', text)
        # Normalize whitespace
        cleaned = ' '.join(cleaned.split())
        # Convert to lowercase for comparison
        cleaned = cleaned.lower()
        # Remove extra punctuation for WER calculation
        cleaned = re.sub(r'[^\w\s\'-]', '', cleaned)
        return cleaned.strip()
    
    def test_kyutai_model(self, model_name, config):
        """Test a Kyutai model"""
        print(f"🤖 Testing {model_name}")
        
        start_time = time.time()
        
        try:
            # Run Kyutai inference
            cmd = config["command"] + [str(self.audio_path)]
            
            print(f"🔄 Starting {model_name} inference...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                # Extract transcription (skip the log lines)
                lines = result.stdout.split('\n')
                transcription_lines = []
                
                for line in lines:
                    # Skip log lines that start with [Info] or other patterns
                    if not (line.startswith('[') or line.startswith('Info:') or 
                           'loading' in line.lower() or 'processed' in line.lower()):
                        if line.strip():
                            transcription_lines.append(line.strip())
                
                transcription = ' '.join(transcription_lines)
                clean_transcription = self.clean_text(transcription)
                
                # Calculate WER if reference exists
                wer = None
                if self.reference_text:
                    try:
                        wer = jiwer.wer(self.reference_text, clean_transcription)
                    except:
                        wer = float('inf')
                
                print(f"✅ {model_name} completed! Duration: {duration:.1f}s, WER: {wer:.3f if wer else 'N/A'}")
                
                return {
                    "success": True,
                    "duration": duration,
                    "transcription": transcription,
                    "clean_transcription": clean_transcription,
                    "wer": wer,
                    "framework": config["framework"],
                    "description": config["description"]
                }
            else:
                print(f"❌ {model_name} failed!")
                
                return {
                    "success": False,
                    "duration": duration,
                    "error": result.stderr,
                    "framework": config["framework"],
                    "description": config["description"]
                }
                    
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "duration": 300,
                "error": "Timeout after 5 minutes",
                "framework": config["framework"],
                "description": config["description"]
            }
        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": str(e),
                "framework": config["framework"],
                "description": config["description"]
            }
    
    def run_benchmark(self):
        """Run the complete benchmark"""
        print("🏁 Kyutai-Only Benchmark Test")
        print("=" * 60)
        print(f"📁 Audio: {self.audio_path.name}")
        print(f"📂 Results: {self.results_dir}")
        
        if self.reference_text:
            print(f"📝 Reference: {len(self.reference_text.split())} words")
        else:
            print("⚠️  No reference text - WER will not be calculated")
        
        print("")
        
        # Test Kyutai models
        print("🤖 Testing Kyutai Models")
        print("-" * 30)
        
        for model_name, config in self.kyutai_models.items():
            result = self.test_kyutai_model(model_name, config)
            self.results[model_name] = result
            
            # Save individual result
            result_path = self.results_dir / f"{model_name}_result.json"
            with open(result_path, 'w') as f:
                json.dump(result, f, indent=2)
        
        # Generate comparison report
        return self.generate_report()
    
    def generate_report(self):
        """Generate detailed comparison report and save as markdown"""
        
        # Create markdown report
        markdown_content = self._generate_markdown_report()
        
        # Save markdown report
        markdown_path = self.results_dir / "benchmark_results.md"
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Save detailed JSON report
        report_path = self.results_dir / "benchmark_report.json"
        with open(report_path, 'w') as f:
            json.dump({
                "audio_file": str(self.audio_path),
                "reference_text": self.reference_text,
                "timestamp": datetime.now().isoformat(),
                "results": self.results
            }, f, indent=2)
        
        # Print summary to terminal
        print(f"\n🏁 Benchmark Complete!")
        print(f"📊 Results saved to: {markdown_path}")
        print(f"📄 JSON report: {report_path}")
        print(f"📁 All files in: {self.results_dir}")
        
        return markdown_path
    
    def _generate_markdown_report(self):
        """Generate markdown format report"""
        
        content = []
        content.append("# 📊 Kyutai Speech-to-Text Test Results\n\n")
        content.append(f"**Audio:** `{self.audio_path.name}`  \n")
        content.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        
        if self.reference_text:
            word_count = len(self.reference_text.split())
            content.append(f"**Reference:** {word_count} words  \n")
        
        content.append("\n## Performance Summary\n\n")
        
        # Sort by success, then by duration
        successful_results = {k: v for k, v in self.results.items() if v.get("success", False)}
        failed_results = {k: v for k, v in self.results.items() if not v.get("success", False)}
        
        if successful_results:
            content.append("| Model | Time (s) | WER | RT Factor | Framework | Status |\n")
            content.append("|-------|----------|-----|-----------|-----------|--------|\n")
            
            for model_name, result in successful_results.items():
                duration = result['duration']
                wer = result.get('wer')
                wer_str = f"{wer:.3f}" if wer is not None and wer != float('inf') else "N/A"
                
                # Calculate real-time factor (assuming 30s audio)
                rt_factor = duration / 30.0
                rt_str = f"{rt_factor:.1f}x"
                
                framework = result.get('framework', 'Unknown')
                status = "✅ Success"
                
                content.append(f"| **{model_name}** | {duration:.1f} | **{wer_str}** | {rt_str} | {framework} | {status} |\n")
        
        if failed_results:
            content.append(f"\n## ❌ Failed Tests ({len(failed_results)})\n\n")
            
            for model_name, result in failed_results.items():
                error = result.get('error', 'Unknown error')[:100]
                content.append(f"- **{model_name}**: {error}\n")
        
        # Transcription samples
        if self.reference_text and successful_results:
            content.append("\n## Transcription Quality\n\n")
            content.append(f"**Reference:**\n> {self.reference_text[:200]}...\n\n")
            
            for model_name, result in successful_results.items():
                if result.get('transcription'):
                    transcription = result['transcription'][:200]
                    wer = result.get('wer', 'N/A')
                    content.append(f"**{model_name} (WER: {wer:.3f if wer != 'N/A' else 'N/A'}):**\n> {transcription}...\n\n")
        
        content.append("\n---\n")
        content.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*")
        
        return ''.join(content)

def main():
    # Check if audio file exists
    audio_path = "./samples/french-i-lesson-01-30s.mp3"
    
    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    # Initialize benchmark
    benchmark = STTBenchmark(audio_path)
    
    # Set reference text (from our previous Kyutai test)
    reference = """This is Unit 1 of Pimsleur's French 1. Listen to this French conversation. 
    Est-ce que vous comprenez l'anglais ? Non, monsieur. Je ne comprends pas l'anglais. 
    Je comprends un peu le français. Est-ce que vous êtes américain ? Oui, mademoiselle. 
    In the next few minutes, you'll learn not only to understand this conversation, 
    but to take part in it yourself. Imagine an American man sitting next to a French woman. 
    He wants to begin a conversation, so he's..."""
    
    benchmark.set_reference_text(reference)
    
    # Run the benchmark
    markdown_path = benchmark.run_benchmark()
    
    print(f"\n🎉 View results: {markdown_path}")

if __name__ == "__main__":
    main()