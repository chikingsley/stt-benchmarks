#!/usr/bin/env python3
"""
WhisperKit Tiny Model Test Script
Optimized for speed testing and development
"""

import time
import io
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr

def test_whisperkit_tiny(audio_path):
    """Test WhisperKit Tiny model"""
    print(f"🔧 Testing WhisperKit Tiny")
    print(f"🎵 Audio: {audio_path}")
    
    start_time = time.time()
    
    try:
        # Import WhisperKit pipeline
        from whisperkit.pipelines import WhisperKit
        
        print("📦 Loading WhisperKit Tiny model...")
        
        # Initialize pipeline with tiny model
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            pipe = WhisperKit(
                whisper_version="openai/whisper-tiny",
                out_dir="./whisper_output"
            )
        
        print("🚀 Starting transcription...")
        
        # Transcribe
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = pipe(str(audio_path))
        
        duration = time.time() - start_time
        transcription = result['text']
        
        print(f"✅ Success! Duration: {duration:.1f}s")
        print(f"📝 Transcription:")
        print(f"   {transcription}")
        
        return {
            "success": True,
            "duration": duration,
            "transcription": transcription,
            "model": "whisper-tiny"
        }
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Failed! Error: {str(e)}")
        
        return {
            "success": False,
            "duration": duration,
            "error": str(e),
            "model": "whisper-tiny"
        }

def main():
    # Default audio file
    audio_path = "./samples/french-i-lesson-01-30s.mp3"
    
    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        print("Please ensure the audio file exists in samples/")
        return
    
    print("⚡ WhisperKit Tiny Speed Test")
    print("=" * 40)
    
    # Test tiny model
    result = test_whisperkit_tiny(audio_path)
    
    if result["success"]:
        print(f"\n🏆 Results:")
        print(f"   Time: {result['duration']:.1f}s")
        print(f"   RT Factor: {result['duration']/30:.1f}x")  # assuming 30s audio
        print(f"   Model: {result['model']}")
    else:
        print(f"\n💔 Failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()