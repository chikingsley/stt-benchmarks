#!/usr/bin/env python3
"""
Production-ready WhisperKit transcription script for French audio
Uses the tiny model which provides the best speed/accuracy balance
"""

import time
import json
from pathlib import Path
from whisperkit.pipelines import WhisperKit

def transcribe_french_audio(audio_path, output_format="text"):
    """
    Transcribe French audio using WhisperKit tiny model
    
    Args:
        audio_path: Path to audio file
        output_format: "text", "json", or "srt"
    
    Returns:
        Transcription result
    """
    print("🇫🇷 WhisperKit French Transcription")
    print("-" * 40)
    
    start_time = time.time()
    
    try:
        # Use tiny model for best performance
        pipe = WhisperKit(
            whisper_version="openai/whisper-tiny",
            out_dir="./whisper_output"
        )
        
        # Transcribe
        print(f"🎙️  Processing: {Path(audio_path).name}")
        result = pipe(audio_path)
        
        duration = time.time() - start_time
        
        print(f"✅ Completed in {duration:.1f}s")
        print(f"🎯 Language: {result['language']}")
        
        if output_format == "json":
            # Save full JSON result
            output_path = Path(audio_path).with_suffix('.json')
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"💾 Saved JSON to: {output_path}")
            return result
            
        elif output_format == "srt":
            # Generate SRT format
            srt_content = generate_srt(result['segments'])
            output_path = Path(audio_path).with_suffix('.srt')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            print(f"💾 Saved SRT to: {output_path}")
            return srt_content
            
        else:
            # Return plain text
            return result['text']
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def generate_srt(segments):
    """Convert segments to SRT format"""
    srt_lines = []
    
    for i, seg in enumerate(segments, 1):
        # Extract text without timestamps
        text = seg['text']
        # Remove timestamp markers like <|0.00|>
        import re
        text = re.sub(r'<\|\d+\.\d+\|>', '', text).strip()
        
        # Format timestamps
        start = format_timestamp(seg['start'])
        end = format_timestamp(seg['end'])
        
        # Add SRT entry
        srt_lines.append(f"{i}")
        srt_lines.append(f"{start} --> {end}")
        srt_lines.append(text)
        srt_lines.append("")  # Empty line between entries
    
    return '\n'.join(srt_lines)

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')

def main():
    # Your French audio file
    audio_path = "/Volumes/simons-enjoyment/GitHub/whisperkittools/french-i-lesson-01.mp3"
    
    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    # Transcribe and get text
    text = transcribe_french_audio(audio_path, output_format="text")
    
    if text:
        print("\n📝 Transcription:")
        print("-" * 40)
        print(text)
        
        # Also save as SRT for subtitles
        print("\n💡 Generating SRT file...")
        transcribe_french_audio(audio_path, output_format="srt")

if __name__ == "__main__":
    main()