#!/usr/bin/env python3
"""
Fast French Audio Transcription - Tiny Model Only
Clean, fast transcription with file output and minimal terminal noise
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

# Suppress WhisperKit noise
logging.getLogger("whisperkit.pipelines").setLevel(logging.ERROR)
logging.getLogger("argmaxtools.utils").setLevel(logging.ERROR)

def clean_text(text):
    """Remove timestamp markers and clean up text"""
    cleaned = re.sub(r'<\|[^|]*\|>', '', text)
    return ' '.join(cleaned.split()).strip()

def transcribe_tiny_model(audio_path, output_dir):
    """Transcribe with tiny model - fast and reliable"""
    
    model_version = "openai/whisper-tiny"
    model_dir = output_dir / "whisper-tiny"
    model_dir.mkdir(exist_ok=True)
    
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
            bar.text = "🚀 Loading model..."
            bar(10)
            
            # Suppress output during loading
            import sys
            from contextlib import redirect_stdout, redirect_stderr
            import io
            
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                pipe = WhisperKit(
                    whisper_version=model_version,
                    out_dir="./whisper_output"
                )
            
            bar.text = "🎙️ Processing audio..."
            bar(30)
            
            # Transcribe with output suppression
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                result = pipe(audio_path)
            
            bar.text = "💾 Saving files..."
            bar(80)
            
            duration = time.time() - start_time
            clean_transcription = clean_text(result['text'])
            
            # Save files
            files = {}
            
            # 1. Clean text
            text_path = model_dir / "transcription.txt"
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(clean_transcription)
            files['text'] = text_path
            
            # 2. Full JSON
            json_path = model_dir / "full_result.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            files['json'] = json_path
            
            # 3. Performance metrics
            audio_seconds = result.get('timings', {}).get('inputAudioSeconds', 0)
            metrics = {
                'model': 'whisper-tiny',
                'duration_seconds': duration,
                'audio_length_seconds': audio_seconds,
                'language_detected': result.get('language', 'unknown'),
                'characters_transcribed': len(clean_transcription),
                'words_estimated': len(clean_transcription.split()),
                'processing_speed_ratio': audio_seconds / duration if duration > 0 else 0,
                'timestamp': datetime.now().isoformat()
            }
            
            metrics_path = model_dir / "metrics.json"
            with open(metrics_path, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2)
            files['metrics'] = metrics_path
            
            bar.text = f"✅ Done! {duration:.1f}s | {metrics['processing_speed_ratio']:.1f}x speed"
            bar(100)
            
            return {
                'success': True,
                'result': result,
                'clean_text': clean_transcription,
                'metrics': metrics,
                'files': files,
                'duration': duration
            }
            
        except Exception as e:
            bar.text = f"❌ Error: {str(e)[:40]}..."
            bar(100)
            return {
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time
            }

def main():
    audio_path = "./samples/french-i-lesson-01.mp3"
    
    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("./transcription_results") / f"tiny_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🇫🇷 Fast French Transcription (WhisperKit Tiny)")
    print("=" * 50)
    print(f"📁 Audio: {Path(audio_path).name}")
    print("")
    
    # Transcribe
    result = transcribe_tiny_model(audio_path, output_dir)
    
    if result['success']:
        metrics = result['metrics']
        
        print("")
        print("✅ SUCCESS!")
        print("=" * 50)
        print(f"⏱️  Duration: {metrics['duration_seconds']:.1f}s")
        print(f"🎯 Language: {metrics['language_detected']}")
        print(f"📝 Characters: {metrics['characters_transcribed']:,}")
        print(f"📖 Words: {metrics['words_estimated']:,}")
        print(f"🚀 Speed: {metrics['processing_speed_ratio']:.1f}x realtime")
        print(f"📁 Output: {output_dir}")
        print("")
        print("📄 Generated Files:")
        for file_type, path in result['files'].items():
            print(f"  • {path.name} - {file_type}")
        print("")
        print("📝 Transcription Preview:")
        print("-" * 40)
        preview = result['clean_text'][:400]
        print(preview + "..." if len(result['clean_text']) > 400 else preview)
        
    else:
        print("")
        print("❌ FAILED!")
        print(f"Error: {result['error']}")
        print(f"Duration before failure: {result['duration']:.1f}s")

if __name__ == "__main__":
    main()