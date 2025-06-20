#!/usr/bin/env python3
"""
Test reasonable-sized WhisperKit models with progress indicators
"""

import time
import threading
from pathlib import Path
from whisperkit.pipelines import WhisperKit

class ProgressIndicator:
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
        print()  # New line after progress
        
    def _show_progress(self):
        while self.running:
            elapsed = time.time() - self.start_time
            print(f"\r🔄 Processing {self.model_name}... {elapsed:.1f}s", end='', flush=True)
            time.sleep(0.5)

def test_model_with_progress(model_name, audio_path):
    print(f"\n🤖 Testing: {model_name}")
    print("-" * 50)
    
    progress = ProgressIndicator(model_name)
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
        
        print(f"✅ Success! Duration: {duration:.1f}s")
        print(f"🎯 Language: {result['language']}")
        print(f"📝 Preview: {result['text'][:150]}...")
        
        return True, duration, result['language']
        
    except Exception as e:
        progress.stop()
        print(f"❌ Error: {str(e)}")
        return False, None, None

def main():
    audio_path = "/Volumes/simons-enjoyment/GitHub/whisperkittools/french-i-lesson-01.mp3"
    
    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    print("🇫🇷 Testing Reasonable WhisperKit Models")
    print("=" * 60)
    
    # Test progression: tiny -> base -> small -> distilled
    models_to_test = [
        "openai/whisper-base",
        "openai/whisper-small", 
        "openai/whisper-small_216MB",
        "distil-whisper/distil-large-v3"
    ]
    
    results = {}
    
    for model in models_to_test:
        success, duration, language = test_model_with_progress(model, audio_path)
        
        if success:
            results[model] = {
                'duration': duration,
                'language': language
            }
        else:
            print(f"⚠️  Skipping remaining models due to {model} failure")
            break
        
        # Brief pause between models
        time.sleep(2)
    
    # Summary
    if results:
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE SUMMARY")
        print("=" * 60)
        
        for model, data in results.items():
            print(f"🤖 {model.split('/')[-1]}: {data['duration']:.1f}s ({data['language']})")
        
        # Find fastest
        fastest = min(results.items(), key=lambda x: x[1]['duration'])
        print(f"\n🏆 Fastest: {fastest[0].split('/')[-1]} at {fastest[1]['duration']:.1f}s")

if __name__ == "__main__":
    main()