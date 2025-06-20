#!/usr/bin/env python3
"""
Simple MLX Whisper test with correct model names
"""

import time
from pathlib import Path
from whisperkit.pipelines import WhisperMLX

def test_mlx():
    audio_path = "/Volumes/simons-enjoyment/GitHub/whisperkittools/french-i-lesson-01.mp3"
    
    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    print("🇫🇷 Testing MLX Whisper")
    print("=" * 50)
    
    # Try with standard OpenAI model names that MLX might support
    models_to_try = [
        "tiny",
        "base", 
        "small",
        "medium",
        "large"
    ]
    
    for model in models_to_try:
        print(f"\n🤖 Trying model: {model}")
        start_time = time.time()
        
        try:
            # MLX might use simpler model names
            pipe = WhisperMLX(
                whisper_version=model,
                out_dir="./mlx_output"
            )
            
            result = pipe(audio_path)
            duration = time.time() - start_time
            
            print(f"✅ Success in {duration:.1f}s!")
            
            # Handle different result formats
            if isinstance(result, dict) and 'text' in result:
                print(f"📝 Text: {result['text'][:150]}...")
            elif isinstance(result, str):
                print(f"📝 Text: {result[:150]}...")
            else:
                print(f"📝 Result type: {type(result)}")
            
            return True
            
        except Exception as e:
            print(f"❌ {model} failed: {str(e)[:100]}...")
            continue
    
    print("\n⚠️  No MLX models worked. MLX might need different setup or model names.")
    return False

if __name__ == "__main__":
    test_mlx()