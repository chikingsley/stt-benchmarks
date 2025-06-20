#!/usr/bin/env python3
"""
Simple test for Kyutai STT - debug version
"""

import subprocess
import sys
import time
from pathlib import Path

def test_kyutai_simple():
    audio_file = "./samples/french-i-lesson-01-30s.mp3"
    
    print("🧪 Simple Kyutai STT Test")
    print(f"📁 Audio: {audio_file}")
    
    if not Path(audio_file).exists():
        print(f"❌ Audio file not found: {audio_file}")
        return
    
    print("🚀 Starting Kyutai inference...")
    print("⏳ This may take a while on first run (downloading model)...")
    
    start_time = time.time()
    
    try:
        # Run the command with real-time output
        process = subprocess.Popen(
            [
                sys.executable, "-m", "moshi.run_inference",
                "--hf-repo", "kyutai/stt-1b-en_fr",
                "--device", "cpu",
                audio_file
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Read output in real-time
        output_lines = []
        for line in iter(process.stdout.readline, ''):
            print(line.rstrip())
            output_lines.append(line.rstrip())
            
            # Stop after 5 minutes
            if time.time() - start_time > 300:
                print("\n⏰ Stopping after 5 minutes...")
                process.terminate()
                break
        
        process.wait()
        duration = time.time() - start_time
        
        print(f"\n✅ Process completed in {duration:.1f}s")
        
        # Save output
        with open("kyutai_simple_output.txt", "w") as f:
            f.write("\n".join(output_lines))
        print("💾 Output saved to kyutai_simple_output.txt")
        
        # Show transcription if any
        transcription_lines = [line for line in output_lines if not line.startswith('[') and line.strip()]
        if transcription_lines:
            print("\n📝 Transcription found:")
            print("-" * 40)
            for line in transcription_lines[-5:]:  # Show last 5 lines
                print(line)
            print("-" * 40)
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_kyutai_simple()