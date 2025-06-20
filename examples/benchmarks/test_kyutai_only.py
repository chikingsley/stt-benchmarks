#!/usr/bin/env python3
"""
Kyutai-only STT Test Script
Simple script to test just Kyutai models for optimization work
"""

import subprocess
import sys
import time
from pathlib import Path

def test_kyutai_model(audio_path, model_path="kyutai/stt-1b-en_fr"):
    """Test Kyutai model with given audio"""
    print(f"🤖 Testing Kyutai: {model_path}")
    print(f"🎵 Audio: {audio_path}")
    
    start_time = time.time()
    
    # Run Kyutai inference
    cmd = [sys.executable, "-m", "moshi.run_inference", 
           "--hf-repo", model_path, "--device", "cpu", str(audio_path)]
    
    try:
        print("🔄 Starting Kyutai inference...")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            # Extract transcription (skip log lines)
            lines = result.stdout.split('\n')
            transcription_lines = []
            
            for line in lines:
                # Skip log lines
                if not (line.startswith('[') or line.startswith('Info:') or 
                       'loading' in line.lower() or 'processed' in line.lower()):
                    if line.strip():
                        transcription_lines.append(line.strip())
            
            transcription = ' '.join(transcription_lines)
            
            print(f"✅ Success! Duration: {duration:.1f}s")
            print(f"📝 Transcription:")
            print(f"   {transcription}")
            
            return {
                "success": True,
                "duration": duration,
                "transcription": transcription
            }
        else:
            print(f"❌ Failed! Error:")
            print(f"   {result.stderr}")
            
            return {
                "success": False,
                "duration": duration,
                "error": result.stderr
            }
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout after 5 minutes")
        return {
            "success": False,
            "duration": 300,
            "error": "Timeout"
        }
    except Exception as e:
        duration = time.time() - start_time
        print(f"💥 Exception: {str(e)}")
        return {
            "success": False,
            "duration": duration,
            "error": str(e)
        }

def main():
    # Default audio file
    audio_path = "./samples/french-i-lesson-01-30s.mp3"
    
    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        print("Please ensure the audio file exists in samples/")
        return
    
    print("🎯 Kyutai Model Test")
    print("=" * 40)
    
    # Test standard PyTorch model
    result = test_kyutai_model(audio_path)
    
    if result["success"]:
        print(f"\n🏆 Results:")
        print(f"   Time: {result['duration']:.1f}s")
        print(f"   RT Factor: {result['duration']/30:.1f}x")  # assuming 30s audio
    else:
        print(f"\n💔 Failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()