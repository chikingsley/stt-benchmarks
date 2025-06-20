#!/usr/bin/env python3
"""
Test MLX Whisper for fast French audio transcription
MLX is optimized for Apple Silicon and should be much faster
"""

import time
from pathlib import Path
from whisperkit.pipelines import WhisperMLX, WhisperKit

def test_mlx_model(model_name, audio_path):
    """Test MLX Whisper model"""
    print(f"\n🚀 Testing MLX Whisper: {model_name}")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        # Initialize MLX Whisper
        print("⏳ Loading MLX model...")
        pipe = WhisperMLX(
            whisper_version=model_name,
            out_dir="./mlx_whisper_output"
        )
        
        # Transcribe
        print("🎙️  Transcribing audio...")
        result = pipe(audio_path)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Success! Total time: {duration:.1f}s")
        print(f"🎯 Language detected: {result.get('language', 'unknown')}")
        print(f"📝 Transcription preview:")
        print("-" * 40)
        
        # Handle different result formats
        if isinstance(result, dict) and 'text' in result:
            text = result['text']
        elif isinstance(result, str):
            text = result
        else:
            text = str(result)
            
        print(text[:300] + "..." if len(text) > 300 else text)
        
        return True, duration, text
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, None, None

def compare_with_whisperkit(audio_path):
    """Quick comparison with WhisperKit tiny"""
    print("\n📊 Quick WhisperKit comparison (tiny model)")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        pipe = WhisperKit(
            whisper_version="openai/whisper-tiny",
            out_dir="./whisper_output"
        )
        result = pipe(audio_path)
        
        duration = time.time() - start_time
        print(f"⏱️  WhisperKit tiny: {duration:.1f}s")
        
        return duration
        
    except Exception as e:
        print(f"❌ WhisperKit error: {str(e)}")
        return None

def main():
    audio_path = "/Volumes/simons-enjoyment/GitHub/whisperkittools/french-i-lesson-01.mp3"
    
    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    print("🇫🇷 MLX Whisper Test for French Audio")
    print("=" * 60)
    print("ℹ️  MLX is optimized for Apple Silicon (M1/M2/M3)")
    
    # Test different MLX models
    mlx_models = [
        "mlx-community/whisper-tiny",
        "mlx-community/whisper-base", 
        "mlx-community/whisper-small",
        "mlx-community/whisper-large-v3-turbo"  # Optimized large model
    ]
    
    results = {}
    
    for model in mlx_models:
        success, duration, text = test_mlx_model(model, audio_path)
        
        if success:
            results[model] = duration
            
            # Stop if a model takes too long
            if duration > 60:
                print(f"⚠️  {model} took {duration:.1f}s, skipping larger models")
                break
        else:
            print(f"⚠️  {model} failed, trying next model...")
        
        time.sleep(1)
    
    # Compare with WhisperKit
    print("\n" + "=" * 60)
    wk_duration = compare_with_whisperkit(audio_path)
    
    # Summary
    if results:
        print("\n" + "=" * 60)
        print("🏁 PERFORMANCE SUMMARY")
        print("=" * 60)
        
        sorted_results = sorted(results.items(), key=lambda x: x[1])
        
        print("\n📊 MLX Models:")
        for model, duration in sorted_results:
            model_name = model.split('/')[-1]
            print(f"   {model_name:<20} {duration:>6.1f}s")
        
        if wk_duration:
            print(f"\n📊 WhisperKit:")
            print(f"   whisper-tiny         {wk_duration:>6.1f}s")
            
            fastest_mlx = sorted_results[0]
            speedup = wk_duration / fastest_mlx[1]
            print(f"\n🚀 MLX {fastest_mlx[0].split('/')[-1]} is {speedup:.1f}x faster than WhisperKit!")

if __name__ == "__main__":
    main()