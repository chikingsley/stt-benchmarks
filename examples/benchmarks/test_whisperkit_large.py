#!/usr/bin/env python3
"""
WhisperKit Large Models Test Script
For testing large models with different optimizations
"""

import time
import io
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr


def test_whisperkit_large(
    audio_path, model_version="openai/whisper-large-v3-v20240930_626MB"
):
    """Test WhisperKit Large model"""
    print(f"🔧 Testing WhisperKit Large: {model_version}")
    print(f"🎵 Audio: {audio_path}")

    start_time = time.time()

    try:
        # Import WhisperKit pipeline
        from whisperkit.pipelines import WhisperKit

        print("📦 Loading WhisperKit Large model...")
        print("⚠️  This may take some time...")

        # Initialize pipeline
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            pipe = WhisperKit(whisper_version=model_version, out_dir="./whisper_output")

        print("🚀 Starting transcription...")

        # Transcribe
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = pipe(str(audio_path))

        duration = time.time() - start_time
        transcription = result["text"]

        print(f"✅ Success! Duration: {duration:.1f}s")
        print("📝 Transcription:")
        print(f"   {transcription}")

        return {
            "success": True,
            "duration": duration,
            "transcription": transcription,
            "model": model_version,
        }

    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Failed! Error: {str(e)}")

        return {
            "success": False,
            "duration": duration,
            "error": str(e),
            "model": model_version,
        }


def main():
    # Default audio file
    audio_path = "./samples/french-i-lesson-01-30s.mp3"

    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        print("Please ensure the audio file exists in samples/")
        return

    print("🏋️  WhisperKit Large Model Test")
    print("=" * 40)

    # Available large models
    models = [
        "openai/whisper-large-v3-v20240930_626MB",
        "openai/whisper-large-v3-v20240930_turbo_632MB",
        "distil-whisper/distil-large-v3",
        "distil-whisper_distil-large-v3_turbo_600MB",
    ]

    print("Available models:")
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")

    # Test first model by default (can be modified)
    selected_model = models[0]
    print(f"\n🎯 Testing: {selected_model}")

    # Test selected model
    result = test_whisperkit_large(audio_path, selected_model)

    if result["success"]:
        print("\n🏆 Results:")
        print(f"   Time: {result['duration']:.1f}s")
        print(f"   RT Factor: {result['duration'] / 30:.1f}x")  # assuming 30s audio
        print(f"   Model: {result['model']}")
    else:
        print(f"\n💔 Failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
