#!/usr/bin/env python3
"""
Simple test of enhanced transcription with just the tiny model
Demonstrates alive-progress bars, file output, and timing analysis
"""

import os
import time
import json
import re
from pathlib import Path
from datetime import datetime
from alive_progress import alive_bar
from whisperkit.pipelines import WhisperKit

def transcribe_with_progress(audio_path):
    """Transcribe with progress bar and file output"""
    
    # Create output directory
    output_dir = Path("./transcription_results")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = output_dir / f"tiny_test_{timestamp}"
    session_dir.mkdir(exist_ok=True)
    
    model_name = "openai/whisper-tiny"
    
    with alive_bar(
        100,
        title="🎙️  WhisperKit Tiny",
        spinner="waves",
        dual_line=True,
        force_tty=True,
        refresh_secs=0.05
    ) as bar:
        
        start_time = time.time()
        
        try:
            bar.text = "🚀 Initializing WhisperKit..."
            bar(10)
            
            pipe = WhisperKit(
                whisper_version=model_name,
                out_dir="./whisper_output"
            )
            
            bar.text = "📂 Model loaded, processing audio..."
            bar(30)
            
            # Transcribe (this is the main work)
            result = pipe(audio_path)
            
            bar.text = "✅ Transcription complete, saving files..."
            bar(80)
            
            duration = time.time() - start_time
            
            # Clean up text
            clean_text = re.sub(r'<\|[^|]*\|>', '', result['text'])
            clean_text = ' '.join(clean_text.split()).strip()
            
            # Save files
            # 1. Full JSON result
            json_path = session_dir / "full_result.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # 2. Clean text
            text_path = session_dir / "transcription.txt"
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(clean_text)
            
            # 3. Timing info
            timing_path = session_dir / "timing.json"
            timing_info = {
                'total_duration_seconds': duration,
                'audio_length_seconds': result.get('timings', {}).get('inputAudioSeconds', 0),
                'language_detected': result.get('language', 'unknown'),
                'model_name': 'whisper-tiny',
                'characters_transcribed': len(clean_text),
                'processing_speed_ratio': result.get('timings', {}).get('inputAudioSeconds', 0) / duration if duration > 0 else 0
            }
            
            with open(timing_path, 'w', encoding='utf-8') as f:
                json.dump(timing_info, f, indent=2)
            
            # 4. SRT file if segments available
            if 'segments' in result:
                srt_path = session_dir / "subtitles.srt"
                srt_lines = []
                
                for i, seg in enumerate(result['segments'], 1):
                    text = re.sub(r'<\|[^|]*\|>', '', seg['text']).strip()
                    if not text:
                        continue
                        
                    start = format_timestamp(seg['start'])
                    end = format_timestamp(seg['end'])
                    
                    srt_lines.extend([str(i), f"{start} --> {end}", text, ""])
                
                with open(srt_path, 'w', encoding='utf-8') as f:
                    f.write('\\n'.join(srt_lines))
            
            bar.text = f"💾 Files saved! Total time: {duration:.1f}s"
            bar(100)
            
            return {
                'success': True,
                'duration': duration,
                'session_dir': session_dir,
                'clean_text': clean_text,
                'timing_info': timing_info
            }
            
        except Exception as e:
            bar.text = f"❌ Error: {str(e)[:30]}..."
            bar(100)
            return {
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time
            }

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')

def main():
    audio_path = "/Volumes/simons-enjoyment/GitHub/whisperkittools/french-i-lesson-01.mp3"
    
    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    print("🇫🇷 Enhanced WhisperKit Tiny Model Test")
    print("=" * 50)
    print(f"📁 Audio: {Path(audio_path).name}")
    print("")
    
    # Transcribe with progress
    result = transcribe_with_progress(audio_path)
    
    if result['success']:
        print("")
        print("✅ Transcription Successful!")
        print("=" * 50)
        print(f"⏱️  Duration: {result['duration']:.1f}s")
        print(f"🎯 Language: {result['timing_info']['language_detected']}")
        print(f"📝 Characters: {result['timing_info']['characters_transcribed']}")
        print(f"🚀 Speed: {result['timing_info']['processing_speed_ratio']:.1f}x realtime")
        print(f"📁 Files saved to: {result['session_dir']}")
        print("")
        print("📝 Transcription Preview:")
        print("-" * 40)
        print(result['clean_text'][:300] + "..." if len(result['clean_text']) > 300 else result['clean_text'])
        print("")
        print("📁 Generated Files:")
        print(f"  • full_result.json - Complete WhisperKit output")
        print(f"  • transcription.txt - Clean text only")
        print(f"  • timing.json - Performance metrics")
        print(f"  • subtitles.srt - Subtitle file")
        
    else:
        print("")
        print("❌ Transcription Failed!")
        print(f"Error: {result['error']}")
        print(f"Duration before failure: {result['duration']:.1f}s")

if __name__ == "__main__":
    main()