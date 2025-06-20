# Kyutai STT Integration Guide

## Overview

The Kyutai STT models (`stt-1b-en_fr`) are streaming speech-to-text models optimized for real-time transcription with a 0.5 second delay. Unlike WhisperKit which processes complete audio files, Kyutai models can output text as audio arrives.

## Key Features

- **Real-time streaming**: 0.5 second delay
- **Languages**: English and French
- **Semantic VAD**: Intelligent voice activity detection
- **Model size**: ~1B parameters
- **Three implementations**: PyTorch, Candle (Rust), MLX (Apple Silicon)

## Quick Start

### 1. Install Dependencies

```bash
# Using pip
pip install moshi

# Using poetry
poetry add moshi

# For MLX version (Apple Silicon)
pip install mlx

# For Candle version (may require Rust toolchain)
cargo install candle
```

### 2. Basic Usage

```python
# Command line
python -m moshi.run_inference --hf-repo kyutai/stt-1b-en_fr audio.mp3

# Python script
import subprocess
result = subprocess.run([
    "python", "-m", "moshi.run_inference",
    "--hf-repo", "kyutai/stt-1b-en_fr",
    "audio.mp3"
], capture_output=True, text=True)
print(result.stdout)
```

### 3. Test Scripts

```bash
# Comprehensive testing
python test_kyutai_stt.py --audio your_audio.mp3

# Simple streaming demo
python kyutai_streaming_demo.py
```

## Model Versions

### Standard (PyTorch)
- **Path**: `stt-1b-en_fr/`
- **Use case**: General purpose, maximum compatibility
- **Pros**: Well-tested, broad hardware support
- **Cons**: Larger memory footprint

### Candle (Rust)
- **Path**: `stt-1b-en_fr-candle/`
- **Use case**: Edge devices, embedded systems
- **Pros**: Low memory usage, fast startup
- **Cons**: Requires Rust toolchain

### MLX (Apple Silicon)
- **Path**: `stt-1b-en_fr-mlx/`
- **Use case**: macOS/iOS applications
- **Pros**: Optimized for M1/M2/M3, best Mac performance
- **Cons**: Apple Silicon only

## Integration with WhisperKit Tools

### Comparison with WhisperKit

| Aspect | Kyutai STT | WhisperKit |
|--------|------------|------------|
| Processing | Streaming (real-time) | Batch (full audio) |
| Latency | 0.5 seconds | Depends on audio length |
| Accuracy | Good for live | Better for offline |
| Languages | EN, FR | 99+ languages |
| Use case | Live caption, voice assistants | Transcription, subtitles |

### Hybrid Approach

For optimal results, consider using both:

1. **Kyutai STT** for real-time preview during recording
2. **WhisperKit** for final high-accuracy transcription

```python
# Example hybrid workflow
def hybrid_transcription(audio_stream):
    # Real-time with Kyutai
    kyutai_text = stream_with_kyutai(audio_stream)
    display_live(kyutai_text)
    
    # Post-process with WhisperKit
    final_text = transcribe_with_whisperkit(audio_file)
    return final_text
```

## Performance Optimization

### GPU Acceleration
```python
# Check GPU availability
import torch
if torch.cuda.is_available():
    print("GPU available for acceleration")
```

### Batch Processing
```python
# Process multiple streams (up to 400 on H100)
streams = [stream1, stream2, ...]
results = model.process_batch(streams)
```

### Memory Management
- Standard model: ~4GB RAM
- Candle model: ~2GB RAM
- MLX model: Optimized for unified memory

## Real-time Streaming Example

```python
import pyaudio
import numpy as np

def real_time_transcription():
    # Audio setup
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    
    # Model setup
    model = KyutaiSTT("stt-1b-en_fr")
    
    print("🎙️ Listening... (Ctrl+C to stop)")
    
    try:
        while True:
            # Get audio chunk
            data = stream.read(CHUNK)
            audio_np = np.frombuffer(data, dtype=np.int16)
            
            # Process with model (0.5s delay)
            text = model.process_chunk(audio_np)
            if text:
                print(text, end='', flush=True)
                
    except KeyboardInterrupt:
        print("\n✅ Stopped")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
```

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'moshi'**
   - Solution: `pip install moshi`

2. **Model download fails**
   - Check internet connection
   - Try manual download from HuggingFace

3. **Out of memory**
   - Use Candle version for lower memory
   - Reduce batch size

4. **Poor quality on non-English/French**
   - Model is optimized for EN/FR only
   - Use WhisperKit for other languages

## Next Steps

1. **Test the models**: Run `test_kyutai_stt.py`
2. **Try streaming demo**: Run `kyutai_streaming_demo.py`
3. **Implement real-time**: Build live transcription app
4. **Compare performance**: Benchmark against WhisperKit
5. **Production deployment**: Choose best version for your use case

## Resources

- [Kyutai STT Paper](https://arxiv.org/abs/2410.00037)
- [GitHub Repository](https://github.com/kyutai-labs/delayed-streams-modeling/)
- [HuggingFace Model](https://huggingface.co/kyutai/stt-1b-en_fr)
- [Project Page](https://kyutai.org/next/stt)