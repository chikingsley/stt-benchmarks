#!/usr/bin/env python3
"""
French Audio Transcription Script using WhisperKit
Progressively tests different Whisper model sizes on French audio
"""

import os
import time
from pathlib import Path
from whisperkit.pipelines import WhisperKit

def transcribe_audio(audio_path, model_version, out_dir="./whisper_output"):
    """Transcribe audio using specified Whisper model"""
    print(f"\n🎙️  Transcribing with {model_version}")
    print(f"📁 Audio file: {audio_path}")
    
    start_time = time.time()
    
    try:
        # Initialize WhisperKit pipeline
        pipe = WhisperKit(
            whisper_version=model_version, 
            out_dir=out_dir
        )
        
        # Transcribe the audio
        result = pipe(audio_path)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Transcription completed in {duration:.2f}s")
        print(f"📝 Result: {result}")
        
        return result, duration
        
    except Exception as e:
        print(f"❌ Error with {model_version}: {str(e)}")
        return None, None

def main():
    # Audio file path
    audio_path = "/Volumes/simons-enjoyment/GitHub/whisperkittools/french-i-lesson-01.mp3"
    
    # Check if audio file exists
    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    print("🇫🇷 French Audio Transcription with WhisperKit")
    print("=" * 50)
    
    # Models to test (smallest to largest)
    models = [
        "openai/whisper-tiny",
        "openai/whisper-large-v3-v20240930_626MB", 
        "openai/whisper-large-v3-v20240930_turbo_632MB"
    ]
    
    results = {}
    
    for model in models:
        result, duration = transcribe_audio(audio_path, model)
        if result:
            results[model] = {
                'transcription': result,
                'duration': duration
            }
        
        # Add a small delay between models
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TRANSCRIPTION SUMMARY")
    print("=" * 50)
    
    for model, data in results.items():
        print(f"\n🤖 {model}")
        print(f"⏱️  Time: {data['duration']:.2f}s")
        print(f"📝 Text: {data['transcription']}")

if __name__ == "__main__":
    main()