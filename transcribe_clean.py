#!/usr/bin/env python3
"""
Clean French Audio Transcription with File Output
Based on working transcribe_french.py but with organized file output and progress
"""

import os
import time
import json
import re
import logging
from pathlib import Path
from datetime import datetime
from alive_progress import alive_bar
from whisperkit.pipelines import WhisperKit
import jiwer

# Suppress verbose WhisperKit logging
logging.getLogger("whisperkit.pipelines").setLevel(logging.ERROR)
logging.getLogger("argmaxtools.utils").setLevel(logging.ERROR)

def clean_text(text):
    """Remove timestamp markers and clean up text"""
    cleaned = re.sub(r'<\|[^|]*\|>', '', text)
    return ' '.join(cleaned.split()).strip()

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')

def transcribe_with_progress(audio_path, model_version, output_dir, timeout=120):
    """Transcribe with progress bar and save to files"""
    
    model_name = model_version.split('/')[-1]
    model_dir = output_dir / model_name
    model_dir.mkdir(exist_ok=True)
    
    with alive_bar(
        100,
        title=f"🎙️  {model_name}",
        spinner="waves",
        dual_line=True,
        force_tty=True,
        refresh_secs=0.05
    ) as bar:
        
        start_time = time.time()
        
        try:
            bar.text = "🚀 Loading model..."
            bar(20)
            
            # Suppress stdout during model loading
            import sys
            from contextlib import redirect_stdout, redirect_stderr
            import io
            
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                pipe = WhisperKit(
                    whisper_version=model_version,
                    out_dir="./whisper_output"
                )
            
            bar.text = "🎙️ Transcribing audio..."
            bar(40)
            
            # Transcribe with output suppression
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                result = pipe(audio_path)
            
            bar.text = "💾 Saving results..."
            bar(80)
            
            duration = time.time() - start_time
            
            # Check timeout
            if duration > timeout:
                bar.text = f"⚠️ Timeout after {duration:.1f}s"
                return None, duration
            
            # Clean and save text
            clean_transcription = clean_text(result['text'])
            
            # Save files
            files_saved = []
            
            # 1. Clean text
            text_path = model_dir / "transcription.txt"
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(clean_transcription)
            files_saved.append(text_path.name)
            
            # 2. Full JSON
            json_path = model_dir / "full_result.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            files_saved.append(json_path.name)
            
            # 3. Timing info
            timing_path = model_dir / "timing.json"
            timing_info = {
                'model': model_name,
                'duration_seconds': duration,
                'audio_length_seconds': result.get('timings', {}).get('inputAudioSeconds', 0),
                'language': result.get('language', 'unknown'),
                'characters': len(clean_transcription),
                'speed_ratio': result.get('timings', {}).get('inputAudioSeconds', 0) / duration if duration > 0 else 0
            }
            
            with open(timing_path, 'w', encoding='utf-8') as f:
                json.dump(timing_info, f, indent=2)
            files_saved.append(timing_path.name)
            
            # 4. SRT file
            if 'segments' in result:
                srt_path = model_dir / "subtitles.srt"
                srt_lines = []
                
                for i, seg in enumerate(result['segments'], 1):
                    text = clean_text(seg['text'])
                    if not text:
                        continue
                        
                    start = format_timestamp(seg['start'])
                    end = format_timestamp(seg['end'])
                    
                    srt_lines.extend([str(i), f"{start} --> {end}", text, ""])
                
                with open(srt_path, 'w', encoding='utf-8') as f:
                    f.write('\\n'.join(srt_lines))
                files_saved.append(srt_path.name)
            
            bar.text = f"✅ Complete! {duration:.1f}s | {len(files_saved)} files"
            bar(100)
            
            return {
                'result': result,
                'clean_text': clean_transcription,
                'duration': duration,
                'timing_info': timing_info,
                'files_saved': files_saved,
                'model_dir': model_dir
            }, duration
            
        except Exception as e:
            bar.text = f"❌ Error: {str(e)[:30]}..."
            bar(100)
            return None, time.time() - start_time

def calculate_wer(text1, text2):
    """Calculate Word Error Rate between two texts"""
    try:
        return jiwer.wer(text1, text2)
    except:
        return float('inf')

def main():
    audio_path = "/Volumes/simons-enjoyment/GitHub/whisperkittools/french-i-lesson-01.mp3"
    
    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("./transcription_results") / f"session_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🇫🇷 Clean WhisperKit French Transcription")
    print("=" * 50)
    print(f"📁 Audio: {Path(audio_path).name}")
    print(f"📂 Output: {output_dir}")
    print("")
    
    # Models from working transcribe_french.py
    models = [
        "openai/whisper-tiny",
        "openai/whisper-large-v3-v20240930_626MB", 
        "openai/whisper-large-v3-v20240930_turbo_632MB"
    ]
    
    timeouts = {
        "openai/whisper-tiny": 60,
        "openai/whisper-large-v3-v20240930_626MB": 300,
        "openai/whisper-large-v3-v20240930_turbo_632MB": 300
    }
    
    results = {}
    
    for model in models:
        timeout = timeouts.get(model, 180)
        data, duration = transcribe_with_progress(audio_path, model, output_dir, timeout)
        
        if data:
            results[model] = data
        else:
            model_name = model.split('/')[-1]
            if "large" in model:
                print(f"⚠️  {model_name} too slow, continuing...")
                continue
            else:
                print(f"⚠️  {model_name} failed, stopping")
                break
        
        time.sleep(1)
    
    # Analysis
    print("")
    print("📊 ANALYSIS")
    print("=" * 50)
    
    if len(results) >= 2:
        print("🔍 Calculating Word Error Rates...")
        model_names = list(results.keys())
        
        for i, model1 in enumerate(model_names):
            for model2 in model_names[i+1:]:
                text1 = results[model1]['clean_text']
                text2 = results[model2]['clean_text']
                wer = calculate_wer(text1, text2)
                
                name1 = model1.split('/')[-1]
                name2 = model2.split('/')[-1]
                print(f"📈 {name1} vs {name2}: WER = {wer:.3f}")
    
    # Summary
    print("")
    print("⚡ PERFORMANCE SUMMARY")
    print("=" * 50)
    
    sorted_results = sorted(results.items(), key=lambda x: x[1]['duration'])
    
    for model, data in sorted_results:
        name = model.split('/')[-1]
        timing = data['timing_info']
        print(f"🤖 {name:<20} {timing['duration_seconds']:>6.1f}s | {timing['language']} | {timing['speed_ratio']:.1f}x")
    
    if sorted_results:
        fastest = sorted_results[0]
        print(f"\\n🏆 Fastest: {fastest[0].split('/')[-1]} at {fastest[1]['duration']:.1f}s")
    
    print(f"\\n📁 All results saved to: {output_dir}")

if __name__ == "__main__":
    main()