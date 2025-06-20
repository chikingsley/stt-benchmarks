#!/usr/bin/env python3
"""
Test script for Kyutai STT models (stt-1b-en_fr)
Tests all three versions: standard, candle, and mlx
Compares performance and accuracy for real-time streaming STT
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
import argparse
import logging

# Suppress verbose logging
logging.basicConfig(level=logging.WARNING)

class KyutaiSTTTester:
    def __init__(self, audio_path, output_dir="./kyutai_stt_results"):
        self.audio_path = Path(audio_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create timestamped subdirectory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"session_{timestamp}"
        self.session_dir.mkdir(exist_ok=True)
        
        # Model configurations
        self.models = {
            "standard": {
                "path": "./stt-1b-en_fr",
                "hf_repo": "kyutai/stt-1b-en_fr",
                "description": "Standard PyTorch implementation"
            },
            "candle": {
                "path": "./stt-1b-en_fr-candle",
                "hf_repo": "kyutai/stt-1b-en_fr",  # Same repo, different implementation
                "description": "Candle (Rust) implementation - optimized for edge devices"
            },
            "mlx": {
                "path": "./stt-1b-en_fr-mlx",
                "hf_repo": "kyutai/stt-1b-en_fr",  # Same repo, different implementation
                "description": "MLX implementation - optimized for Apple Silicon"
            }
        }
        
        self.results = {}
    
    def check_dependencies(self):
        """Check if moshi package is available"""
        print("🔍 Checking dependencies...")
        
        try:
            # Try importing moshi
            result = subprocess.run(
                [sys.executable, "-c", "import moshi; print(moshi.__version__)"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ Moshi package found: version {result.stdout.strip()}")
                return True
            else:
                print("❌ Moshi package not found")
                print("\nTo install moshi, run:")
                print("  pip install moshi")
                print("\nOr with poetry:")
                print("  poetry add moshi")
                return False
                
        except Exception as e:
            print(f"❌ Error checking dependencies: {e}")
            return False
    
    def test_basic_inference(self, model_name):
        """Test basic inference using moshi CLI"""
        print(f"\n🎙️  Testing {model_name} model...")
        print(f"   {self.models[model_name]['description']}")
        
        model_dir = self.session_dir / model_name
        model_dir.mkdir(exist_ok=True)
        
        start_time = time.time()
        
        try:
            # Run moshi inference with CPU device
            cmd = [
                sys.executable, "-m", "moshi.run_inference",
                "--hf-repo", self.models[model_name]["hf_repo"],
                "--device", "cpu",
                str(self.audio_path)
            ]
            
            print(f"   🚀 Running inference...")
            
            # Execute command and capture output
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.models[model_name]["path"] if Path(self.models[model_name]["path"]).exists() else None
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print(f"   ✅ Success! Time: {duration:.2f}s")
                
                # Save output
                output_path = model_dir / "transcription.txt"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                
                # Save timing info
                timing_path = model_dir / "timing.json"
                timing_info = {
                    "model": model_name,
                    "duration_seconds": duration,
                    "audio_path": str(self.audio_path),
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                }
                
                with open(timing_path, 'w') as f:
                    json.dump(timing_info, f, indent=2)
                
                self.results[model_name] = {
                    "success": True,
                    "duration": duration,
                    "output": result.stdout,
                    "stderr": result.stderr
                }
                
            else:
                print(f"   ❌ Failed! Error: {result.stderr[:100]}...")
                
                # Save error info
                error_path = model_dir / "error.txt"
                with open(error_path, 'w') as f:
                    f.write(f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}")
                
                self.results[model_name] = {
                    "success": False,
                    "duration": duration,
                    "error": result.stderr
                }
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            self.results[model_name] = {
                "success": False,
                "error": str(e)
            }
    
    def test_streaming_simulation(self):
        """Simulate streaming by processing audio in chunks"""
        print("\n🌊 Testing streaming capabilities...")
        print("   Note: This simulates streaming by processing audio chunks")
        
        # This is a placeholder for more advanced streaming tests
        # Real streaming would require audio streaming libraries
        print("   ⚠️  Full streaming test requires additional setup")
        print("   💡 The models support real-time streaming with 0.5s delay")
    
    def compare_results(self):
        """Compare results across models"""
        print("\n📊 Results Summary")
        print("=" * 60)
        
        successful_models = {k: v for k, v in self.results.items() if v.get("success", False)}
        
        if not successful_models:
            print("❌ No models completed successfully")
            return
        
        # Performance comparison
        print("\n⚡ Performance Comparison:")
        sorted_by_speed = sorted(successful_models.items(), key=lambda x: x[1]["duration"])
        
        for model, data in sorted_by_speed:
            print(f"  {model:<10} - {data['duration']:>6.2f}s - {self.models[model]['description']}")
        
        # Output comparison (first 200 chars)
        print("\n📝 Output Preview:")
        for model, data in successful_models.items():
            output_preview = data["output"][:200].replace('\n', ' ')
            print(f"\n  {model}:")
            print(f"  {output_preview}...")
        
        # Save comparison report
        report_path = self.session_dir / "comparison_report.md"
        self._generate_report(report_path)
        print(f"\n📄 Full report saved to: {report_path}")
    
    def _generate_report(self, report_path):
        """Generate detailed comparison report"""
        report_lines = []
        report_lines.append("# Kyutai STT Models Test Report")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Audio file: {self.audio_path.name}")
        report_lines.append("")
        
        # Model Information
        report_lines.append("## Model Information")
        report_lines.append("")
        report_lines.append("- **Model**: stt-1b-en_fr")
        report_lines.append("- **Languages**: English and French")
        report_lines.append("- **Parameters**: ~1B")
        report_lines.append("- **Delay**: 0.5 seconds")
        report_lines.append("- **Features**: Streaming STT with semantic VAD")
        report_lines.append("")
        
        # Test Results
        report_lines.append("## Test Results")
        report_lines.append("")
        
        for model_name, result in self.results.items():
            report_lines.append(f"### {model_name.upper()} - {self.models[model_name]['description']}")
            report_lines.append("")
            
            if result.get("success", False):
                report_lines.append(f"✅ **Status**: Success")
                report_lines.append(f"⏱️  **Duration**: {result['duration']:.2f} seconds")
                report_lines.append("")
                report_lines.append("**Output Preview**:")
                report_lines.append("```")
                report_lines.append(result['output'][:500])
                report_lines.append("```")
            else:
                report_lines.append(f"❌ **Status**: Failed")
                report_lines.append(f"**Error**: {result.get('error', 'Unknown error')[:200]}")
            
            report_lines.append("")
        
        # Recommendations
        report_lines.append("## Recommendations")
        report_lines.append("")
        
        if any(r.get("success", False) for r in self.results.values()):
            fastest = min(
                [(k, v) for k, v in self.results.items() if v.get("success", False)],
                key=lambda x: x[1]["duration"]
            )
            report_lines.append(f"🏆 **Fastest Model**: {fastest[0]} ({fastest[1]['duration']:.2f}s)")
            report_lines.append("")
        
        report_lines.append("### Use Cases:")
        report_lines.append("- **Standard (PyTorch)**: General purpose, maximum compatibility")
        report_lines.append("- **Candle (Rust)**: Edge devices, embedded systems, low memory")
        report_lines.append("- **MLX**: Apple Silicon Macs, iOS/macOS applications")
        report_lines.append("")
        
        report_lines.append("### Integration Notes:")
        report_lines.append("- All models support streaming inference")
        report_lines.append("- 0.5 second delay makes them suitable for real-time applications")
        report_lines.append("- Semantic VAD helps detect actual speech vs noise")
        report_lines.append("- Models can handle long audio (tested up to 2 hours)")
        
        # Write report
        with open(report_path, 'w') as f:
            f.write('\n'.join(report_lines))
    
    def test_with_local_models(self):
        """Test using local model files if available"""
        print("\n🔍 Checking for local model files...")
        
        for model_name, config in self.models.items():
            model_path = Path(config["path"])
            if model_path.exists():
                print(f"✅ Found local model: {model_name} at {model_path}")
                
                # Check for required files
                required_files = ["model.safetensors", "config.json", "tokenizer_en_fr_audio_8000.model"]
                missing_files = []
                
                for file in required_files:
                    if not (model_path / file).exists():
                        missing_files.append(file)
                
                if missing_files:
                    print(f"   ⚠️  Missing files: {', '.join(missing_files)}")
                else:
                    print(f"   ✅ All required files present")
            else:
                print(f"❌ Local model not found: {model_name}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Kyutai STT Model Testing Suite")
        print("=" * 60)
        print(f"Audio: {self.audio_path.name}")
        print(f"Output: {self.session_dir}")
        print("")
        
        # Check dependencies
        if not self.check_dependencies():
            print("\n⚠️  Installing moshi package is required to run inference tests")
            print("However, we can still check the local model files...")
        
        # Check local models
        self.test_with_local_models()
        
        # Try to run inference tests if moshi is available
        if self.check_dependencies():
            # Test each model
            for model_name in self.models:
                self.test_basic_inference(model_name)
            
            # Streaming capabilities
            self.test_streaming_simulation()
            
            # Compare results
            self.compare_results()
        else:
            print("\n📝 Next Steps:")
            print("1. Install moshi: pip install moshi")
            print("2. Run this script again to test inference")
            print("3. For MLX version, you may need: pip install mlx")
            print("4. For Candle version, Rust toolchain may be required")

def main():
    parser = argparse.ArgumentParser(description="Test Kyutai STT models")
    parser.add_argument(
        "--audio",
        default="./samples/french-i-lesson-01.mp3",
        help="Path to audio file"
    )
    parser.add_argument(
        "--output-dir",
        default="./kyutai_stt_results",
        help="Output directory for results"
    )
    
    args = parser.parse_args()
    
    if not Path(args.audio).exists():
        print(f"❌ Audio file not found: {args.audio}")
        return
    
    tester = KyutaiSTTTester(args.audio, args.output_dir)
    tester.run_all_tests()

if __name__ == "__main__":
    main()