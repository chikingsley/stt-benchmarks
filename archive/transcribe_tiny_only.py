#!/usr/bin/env python3
"""
French Audio Transcription Script using WhisperKit Tiny Model Only
"""

import time
from pathlib import Path
from whisperkit.pipelines import WhisperKit

def main():
    # Audio file path
    audio_path = "/Volumes/simons-enjoyment/GitHub/whisperkittools/french-i-lesson-01.mp3"
    
    # Check if audio file exists
    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    print("🇫🇷 French Audio Transcription with WhisperKit Tiny")
    print("=" * 50)
    
    start_time = time.time()
    
    try:
        # Initialize WhisperKit pipeline with tiny model
        pipe = WhisperKit(
            whisper_version="openai/whisper-tiny", 
            out_dir="./whisper_output"
        )
        
        # Transcribe the audio
        result = pipe(audio_path)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Transcription completed in {duration:.2f}s")
        print(f"📝 Full transcription:")
        print("-" * 50)
        print(result['text'])
        print("-" * 50)
        print(f"🏁 Total processing time: {duration:.2f}s")
        print(f"🎯 Language detected: {result['language']}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()