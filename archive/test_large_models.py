#!/usr/bin/env python3
"""
Test larger WhisperKit models on French audio
"""

import time
from pathlib import Path
from whisperkit.pipelines import WhisperKit

def test_model(model_name, audio_path):
    print(f"\n🤖 Testing {model_name}")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        pipe = WhisperKit(
            whisper_version=model_name, 
            out_dir="./whisper_output"
        )
        
        result = pipe(audio_path)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Transcription completed in {duration:.2f}s")
        print(f"🎯 Language detected: {result['language']}")
        print(f"📝 First 200 characters:")
        print("-" * 40)
        print(result['text'][:200] + "...")
        print("-" * 40)
        
        return True, duration
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, None

def main():
    audio_path = "/Volumes/simons-enjoyment/GitHub/whisperkittools/french-i-lesson-01.mp3"
    
    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    # Test the 626MB model first
    success_626, time_626 = test_model("openai/whisper-large-v3-v20240930_626MB", audio_path)
    
    if success_626:
        print(f"\n🎉 626MB model succeeded in {time_626:.2f}s")
        
        # Test the 632MB turbo model
        success_632, time_632 = test_model("openai/whisper-large-v3-v20240930_turbo_632MB", audio_path)
        
        if success_632:
            print(f"\n🎉 632MB turbo model succeeded in {time_632:.2f}s")
            
            print("\n" + "=" * 60)
            print("📊 PERFORMANCE COMPARISON")
            print("=" * 60)
            print(f"626MB model: {time_626:.2f}s")
            print(f"632MB turbo: {time_632:.2f}s")
            print(f"Difference: {abs(time_626 - time_632):.2f}s")

if __name__ == "__main__":
    main()