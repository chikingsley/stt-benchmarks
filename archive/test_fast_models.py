#!/usr/bin/env python3
"""
Test only fast, small WhisperKit models for practical use
"""

import time
import threading
from pathlib import Path
from whisperkit.pipelines import WhisperKit

class QuickProgress:
    def __init__(self, model_name):
        self.model_name = model_name
        self.running = False
        self.start_time = None
        
    def start(self):
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._show_progress)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join()
        print()
        
    def _show_progress(self):
        dots = 0
        while self.running:
            elapsed = time.time() - self.start_time
            dot_str = "." * (dots % 4)
            print(f"\r🔄 {self.model_name}{dot_str:<3} {elapsed:.1f}s", end='', flush=True)
            dots += 1
            time.sleep(0.5)

def quick_test(model_name, audio_path, timeout=60):
    """Test with timeout to avoid hanging"""
    print(f"\n🤖 {model_name}")
    print("-" * 40)
    
    progress = QuickProgress(model_name.split('/')[-1])
    progress.start()
    
    start_time = time.time()
    
    try:
        pipe = WhisperKit(
            whisper_version=model_name, 
            out_dir="./whisper_output"
        )
        
        result = pipe(audio_path)
        
        end_time = time.time()
        duration = end_time - start_time
        
        progress.stop()
        
        if duration > timeout:
            print(f"⚠️  Too slow: {duration:.1f}s (>{timeout}s limit)")
            return False, duration, None
        
        print(f"✅ {duration:.1f}s | {result['language']} | {len(result['text'])} chars")
        print(f"📝 \"{result['text'][:100]}...\"")
        
        return True, duration, result['language']
        
    except Exception as e:
        progress.stop()
        print(f"❌ Failed: {str(e)[:50]}...")
        return False, None, None

def main():
    audio_path = "/Volumes/simons-enjoyment/GitHub/whisperkittools/french-i-lesson-01.mp3"
    
    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    print("🇫🇷 Quick WhisperKit Model Tests")
    print("=" * 50)
    
    # Start with tiny variants, then try some potentially faster models
    fast_models = [
        "openai/whisper-tiny",
        "openai/whisper-tiny.en", 
        # Only try these if tiny models work well
    ]
    
    # Maybe try these if the tiny ones are fast enough
    possibly_fast = [
        "openai/whisper-base.en",  # English-only might be faster
        "distil-whisper/distil-small.en",  # Distilled should be faster
    ]
    
    results = {}
    
    print("🚀 Testing ultra-fast models first...")
    
    for model in fast_models:
        success, duration, language = quick_test(model, audio_path, timeout=30)
        
        if success and duration < 30:
            results[model] = {'duration': duration, 'language': language}
        else:
            print(f"⚠️  {model} too slow or failed")
        
        time.sleep(1)
    
    # If we have some fast results, maybe try slightly bigger models
    if results:
        print(f"\n🎯 Found {len(results)} fast models! Trying medium-sized ones...")
        
        for model in possibly_fast:
            success, duration, language = quick_test(model, audio_path, timeout=45)
            
            if success and duration < 45:
                results[model] = {'duration': duration, 'language': language}
            else:
                print(f"⚠️  {model} too slow, skipping remaining tests")
                break
            
            time.sleep(1)
    
    # Summary
    if results:
        print("\n" + "=" * 50)
        print("🏆 FAST MODELS SUMMARY")
        print("=" * 50)
        
        sorted_results = sorted(results.items(), key=lambda x: x[1]['duration'])
        
        for model, data in sorted_results:
            model_name = model.split('/')[-1]
            print(f"⚡ {model_name:<20} {data['duration']:>6.1f}s ({data['language']})")
        
        fastest = sorted_results[0]
        print(f"\n🥇 Fastest: {fastest[0].split('/')[-1]} at {fastest[1]['duration']:.1f}s")
        print(f"💡 Recommendation: Use {fastest[0]} for your French transcription!")
    
    else:
        print("\n❌ No fast models found. Consider using whisper.cpp or MLX for faster inference.")

if __name__ == "__main__":
    main()