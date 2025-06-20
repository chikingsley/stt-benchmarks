#!/usr/bin/env python3
"""
Kyutai STT Streaming Demo
Shows how to use the stt-1b-en_fr model for real-time streaming transcription
"""

import sys
import subprocess
import time
from pathlib import Path

def install_moshi():
    """Install moshi package if not already installed"""
    try:
        import moshi
        print(f"✅ Moshi {moshi.__version__} already installed")
        return True
    except ImportError:
        print("📦 Installing moshi package...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "moshi"])
            print("✅ Moshi installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install moshi")
            return False

def simple_transcribe(audio_path, model="kyutai/stt-1b-en_fr"):
    """Simple transcription using Kyutai STT"""
    print(f"\n🎙️  Transcribing: {Path(audio_path).name}")
    print(f"🤖 Model: {model}")
    print("⏳ Processing...")
    
    start_time = time.time()
    
    try:
        # Run moshi inference with CPU device (for macOS compatibility)
        result = subprocess.run(
            [sys.executable, "-m", "moshi.run_inference", "--hf-repo", model, "--device", "cpu", str(audio_path)],
            capture_output=True,
            text=True
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"\n✅ Success! Processed in {duration:.2f}s")
            print("\n📝 Transcription:")
            print("-" * 60)
            print(result.stdout)
            print("-" * 60)
            
            # Calculate real-time factor
            # Note: We'd need to get actual audio duration for accurate RTF
            print(f"\n⚡ Processing time: {duration:.2f}s")
            print("💡 Model features:")
            print("   - 0.5 second streaming delay")
            print("   - Semantic VAD (Voice Activity Detection)")
            print("   - Supports English and French")
            
            return result.stdout
        else:
            print(f"\n❌ Error: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        return None

def streaming_example():
    """Example of how streaming would work in production"""
    print("\n🌊 Streaming Architecture Example")
    print("=" * 60)
    print("""
In a real-time streaming application, you would:

1. **Audio Input Stream**:
   ```python
   # Capture audio from microphone in chunks
   audio_stream = microphone.get_stream(chunk_size=0.1)  # 100ms chunks
   ```

2. **Model Processing**:
   ```python
   # Initialize Kyutai STT model
   model = KyutaiSTT("stt-1b-en_fr")
   
   # Process audio chunks as they arrive
   for audio_chunk in audio_stream:
       text = model.process_chunk(audio_chunk)
       if text:  # Model outputs text with 0.5s delay
           print(text, end='', flush=True)
   ```

3. **Key Features**:
   - **0.5s delay**: Text appears 0.5 seconds after speech
   - **Semantic VAD**: Detects actual speech (not just noise)
   - **Streaming**: No need to wait for sentence completion
   - **Real-time**: Suitable for live captioning, voice assistants

4. **Performance**:
   - Can handle up to 400 concurrent streams on H100 GPU
   - Works well with 2+ hour audio files
   - Low latency for interactive applications
""")

def compare_with_whisper():
    """Compare Kyutai STT with WhisperKit"""
    print("\n📊 Kyutai STT vs WhisperKit Comparison")
    print("=" * 60)
    print("""
| Feature           | Kyutai STT          | WhisperKit         |
|-------------------|--------------------|--------------------|
| Streaming         | ✅ Native (0.5s)   | ❌ Batch only      |
| Real-time Factor  | ~1x (real-time)    | 0.1-10x (varies)   |
| Languages         | EN, FR             | 99+ languages      |
| Model Size        | 1B params          | 39M-1.5B params    |
| Delay             | 0.5 seconds        | Full audio needed  |
| Use Case          | Live streaming     | Offline accuracy   |
| VAD               | ✅ Semantic        | ❌ Basic           |
| Timestamps        | ✅ Word-level      | ✅ Word-level      |

**When to use Kyutai STT**:
- Live transcription (meetings, streams)
- Voice assistants requiring low latency
- Real-time captioning
- Interactive applications

**When to use WhisperKit**:
- Offline transcription for accuracy
- Multi-language support needed
- Post-processing workflows
- When full context improves accuracy
""")

def main():
    print("🚀 Kyutai STT Streaming Demo")
    print("=" * 60)
    
    # Check/install moshi
    if not install_moshi():
        print("\n⚠️  Please install moshi manually:")
        print("  pip install moshi")
        print("\nOr with poetry:")
        print("  poetry add moshi")
        return
    
    # Audio file
    audio_path = "./samples/french-i-lesson-01.mp3"
    
    if Path(audio_path).exists():
        # Simple transcription
        transcription = simple_transcribe(audio_path)
        
        if transcription:
            # Save output
            output_path = Path("kyutai_demo_output.txt")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(transcription)
            print(f"\n💾 Saved to: {output_path}")
    else:
        print(f"\n⚠️  Audio file not found: {audio_path}")
        print("You can specify any audio file:")
        print(f"  python {sys.argv[0]} <audio_file>")
    
    # Show streaming example
    streaming_example()
    
    # Compare with WhisperKit
    compare_with_whisper()
    
    print("\n✨ Next Steps:")
    print("1. Try with your own audio files")
    print("2. Implement real-time streaming with microphone input")
    print("3. Compare performance with WhisperKit models")
    print("4. Test MLX version on Apple Silicon for best performance")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        if Path(audio_path).exists():
            simple_transcribe(audio_path)
        else:
            print(f"❌ File not found: {audio_path}")
    else:
        main()