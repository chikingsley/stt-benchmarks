#!/usr/bin/env python3
"""
Comprehensive STT Benchmark: Kyutai vs WhisperKit
Measures Word Error Rate (WER) and Processing Time for all models
"""

import subprocess
import sys
import time
import json
import re
from pathlib import Path
from datetime import datetime
import jiwer
from alive_progress import alive_bar

class STTBenchmark:
    def __init__(self, audio_path, reference_text=None):
        self.audio_path = Path(audio_path)
        self.reference_text = reference_text
        
        # Create timestamped results directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_dir = Path("./benchmark_results") / f"benchmark_{timestamp}"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Model configurations
        self.kyutai_models = {
            "kyutai-standard": {
                "command": [sys.executable, "-m", "moshi.run_inference", "--hf-repo", "kyutai/stt-1b-en_fr", "--device", "cpu"],
                "description": "Kyutai 1B PyTorch (Standard)",
                "framework": "PyTorch"
            }
            # Note: Candle and MLX versions would need different command structures
            # For now, testing the standard version that we know works
        }
        
        self.whisperkit_models = {
            "whisperkit-tiny": {
                "script": "transcribe_fast.py",
                "description": "WhisperKit Tiny (~39M params)",
                "framework": "WhisperKit"
            },
            "whisperkit-large-v3-626mb": {
                "model": "openai/whisper-large-v3-v20240930_626MB",
                "description": "WhisperKit Large-v3 (626MB)",
                "framework": "WhisperKit"
            },
            "whisperkit-large-v3-turbo-632mb": {
                "model": "openai/whisper-large-v3-v20240930_turbo_632MB", 
                "description": "WhisperKit Large-v3 Turbo (632MB)",
                "framework": "WhisperKit"
            },
            "whisperkit-distill-large-v3": {
                "model": "distil-whisper/distil-large-v3",
                "description": "Distil Large-v3 (Faster)",
                "framework": "WhisperKit"
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
        print(f"\n🤖 Testing {model_name}")
        print(f"   {config['description']}")
        
        start_time = time.time()
        
        try:
            # Run Kyutai inference
            cmd = config["command"] + [str(self.audio_path)]
            
            with alive_bar(100, title=f"🎙️  {model_name}", force_tty=True) as bar:
                bar.text = "Starting inference..."
                bar(10)
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                bar.text = "Processing results..."
                bar(80)
                
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
                    
                    bar.text = f"✅ Complete! {duration:.1f}s"
                    bar(100)
                    
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
                    bar.text = f"❌ Failed!"
                    bar(100)
                    
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
    
    def test_whisperkit_model(self, model_name, config):
        """Test a WhisperKit model"""
        print(f"\n🔧 Testing {model_name}")
        print(f"   {config['description']}")
        
        start_time = time.time()
        
        try:
            with alive_bar(100, title=f"🎙️  {model_name}", force_tty=True) as bar:
                bar.text = "Starting WhisperKit..."
                bar(10)
                
                # Import WhisperKit pipeline
                from whisperkit.pipelines import WhisperKit
                
                bar.text = "Loading model..."
                bar(30)
                
                # Get model version
                if "script" in config:
                    # Use tiny model for fast script
                    model_version = "openai/whisper-tiny"
                else:
                    model_version = config["model"]
                
                # Initialize pipeline
                import io
                from contextlib import redirect_stdout, redirect_stderr
                
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    pipe = WhisperKit(
                        whisper_version=model_version,
                        out_dir="./whisper_output"
                    )
                
                bar.text = "Transcribing..."
                bar(50)
                
                # Transcribe
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    result = pipe(str(self.audio_path))
                
                bar.text = "Processing results..."
                bar(80)
                
                duration = time.time() - start_time
                
                transcription = result['text']
                clean_transcription = self.clean_text(transcription)
                
                # Calculate WER if reference exists
                wer = None
                if self.reference_text:
                    try:
                        wer = jiwer.wer(self.reference_text, clean_transcription)
                    except:
                        wer = float('inf')
                
                bar.text = f"✅ Complete! {duration:.1f}s"
                bar(100)
                
                return {
                    "success": True,
                    "duration": duration,
                    "transcription": transcription,
                    "clean_transcription": clean_transcription,
                    "wer": wer,
                    "framework": config["framework"],
                    "description": config["description"],
                    "model_version": model_version
                }
                
        except Exception as e:
            duration = time.time() - start_time
            return {
                "success": False,
                "duration": duration,
                "error": str(e),
                "framework": config["framework"],
                "description": config["description"]
            }
    
    def run_benchmark(self):
        """Run the complete benchmark"""
        print("🏁 Comprehensive STT Benchmark")
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
        
        # Test WhisperKit models
        print("\n🔧 Testing WhisperKit Models")
        print("-" * 30)
        
        for model_name, config in self.whisperkit_models.items():
            result = self.test_whisperkit_model(model_name, config)
            self.results[model_name] = result
            
            # Save individual result
            result_path = self.results_dir / f"{model_name}_result.json"
            with open(result_path, 'w') as f:
                json.dump(result, f, indent=2)
        
        # Generate comparison report
        self.generate_report()
    
    def generate_report(self):
        """Generate detailed comparison report"""
        print("\n📊 BENCHMARK RESULTS")
        print("=" * 80)
        
        # Sort by success, then by duration
        successful_results = {k: v for k, v in self.results.items() if v.get("success", False)}
        failed_results = {k: v for k, v in self.results.items() if not v.get("success", False)}
        
        if successful_results:
            print("\n✅ Successful Tests:")
            print("-" * 50)
            
            # Table header
            print(f"{'Model':<25} {'Time(s)':<8} {'WER':<8} {'RT Factor':<10} {'Framework':<12}")
            print("-" * 70)
            
            # Sort by WER if available, then by duration
            if self.reference_text:
                sorted_results = sorted(successful_results.items(), 
                                      key=lambda x: (x[1].get('wer', float('inf')), x[1]['duration']))
            else:
                sorted_results = sorted(successful_results.items(), 
                                      key=lambda x: x[1]['duration'])
            
            for model_name, result in sorted_results:
                duration = result['duration']
                wer = result.get('wer')
                wer_str = f"{wer:.3f}" if wer is not None and wer != float('inf') else "N/A"
                
                # Calculate real-time factor (assuming 30s audio)
                rt_factor = duration / 30.0  # Adjust based on actual audio length
                rt_str = f"{rt_factor:.1f}x"
                
                framework = result.get('framework', 'Unknown')
                
                print(f"{model_name:<25} {duration:<8.1f} {wer_str:<8} {rt_str:<10} {framework:<12}")
        
        if failed_results:
            print(f"\n❌ Failed Tests ({len(failed_results)}):")
            print("-" * 30)
            
            for model_name, result in failed_results.items():
                error = result.get('error', 'Unknown error')[:50]
                print(f"  {model_name}: {error}")
        
        # Best performers
        if successful_results and self.reference_text:
            best_accuracy = min(successful_results.items(), 
                              key=lambda x: x[1].get('wer', float('inf')))
            best_speed = min(successful_results.items(), 
                           key=lambda x: x[1]['duration'])
            
            print(f"\n🎯 Best Accuracy: {best_accuracy[0]} (WER: {best_accuracy[1].get('wer', 'N/A'):.3f})")
            print(f"⚡ Fastest: {best_speed[0]} ({best_speed[1]['duration']:.1f}s)")
        
        # Save detailed report
        report_path = self.results_dir / "benchmark_report.json"
        with open(report_path, 'w') as f:
            json.dump({
                "audio_file": str(self.audio_path),
                "reference_text": self.reference_text,
                "timestamp": datetime.now().isoformat(),
                "results": self.results
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_path}")
        print(f"📁 All results in: {self.results_dir}")

def main():
    # Check if audio file exists
    audio_path = "./samples/french-i-lesson-01-30s.mp3"
    
    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        print("Creating 30-second sample...")
        
        # Try to create the sample
        result = subprocess.run([
            "ffmpeg", "-i", "./samples/french-i-lesson-01.mp3", "-t", "30", "-c", "copy", 
            "./samples/french-i-lesson-01-30s.mp3"
        ], capture_output=True)
        
        if result.returncode != 0:
            print("❌ Could not create audio sample. Please ensure ./samples/french-i-lesson-01.mp3 exists.")
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
    benchmark.run_benchmark()

if __name__ == "__main__":
    main()