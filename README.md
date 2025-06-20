# whisperkittools

![Unit and Functional Tests](https://github.com/argmaxinc/whisperkittools/actions/workflows/public-ci.yml/badge.svg)

Python tools for [WhisperKit](https://github.com/argmaxinc/whisperkit) and [WhisperKitAndroid](https://github.com/argmaxinc/WhisperKitAndroid)

## 🎯 Project Overview

This repository contains:
- **WhisperKit Core Tools**: Convert PyTorch Whisper models to WhisperKit format, apply optimizations, and evaluate performance
- **Audio Transcription Scripts**: Fast and accurate transcription tools for French and other languages
- **Book OCR Pipeline**: AI-powered OCR system for extracting and formatting textbook content
- **Kyutai STT Models**: Streaming speech-to-text models with French support

> [!IMPORTANT]
> If you are looking for more features such as speaker diarization and upgraded performance, check out [WhisperKit Pro](https://huggingface.co/argmaxinc/whisperkit-pro)!

## Table of Contents

- [whisperkittools](#whisperkittools)
  - [🎯 Project Overview](#-project-overview)
  - [🚀 Quick Start](#-quick-start)
    - [Audio Transcription](#audio-transcription)
    - [Book OCR](#book-ocr)
  - [📁 Project Structure](#-project-structure)
  - [🎙️ Audio Transcription Scripts](#️-audio-transcription-scripts)
    - [transcribe_clean.py](#transcribe_cleanpy)
    - [transcribe_fast.py](#transcribe_fastpy)
    - [transcribe_french.py](#transcribe_frenchpy)
    - [transcribe_french_enhanced.py](#transcribe_french_enhancedpy)
  - [🆕 Kyutai STT Models](#-kyutai-stt-models)
  - [📚 Book Cleaning Pipeline](#-book-cleaning-pipeline)
  - [⚙️ WhisperKit Core Features](#️-whisperkit-core-features)
    - [Installation](#installation)
    - [Model Generation (Apple)](#model-generation-apple)
    - [Model Generation (Android)](#model-generation-android)
    - [Model Evaluation](#model-evaluation)
    - [Python Inference](#python-inference)
  - [Example SwiftUI App](#example-swiftui-app)
  - [WhisperKit Quality and Performance Benchmarks](#whisperkit-quality-and-performance-benchmarks)
  - [FAQ](#faq)
  - [Citation](#citation)

## 🚀 Quick Start

### Audio Transcription

```bash
# Fast transcription with Whisper Tiny model
python transcribe_fast.py

# Clean transcription with multiple models and analysis
python transcribe_clean.py

# Enhanced transcription with WER analysis
python transcribe_french_enhanced.py
```

### Book OCR

```bash
cd book_cleaning

# Set up API keys
echo "GOOGLE_API_KEY=your_key" > .env

# Run OCR on PDF pages
python gemini_ocr_formatter.py "Colloquial French 1.pdf" --start-page 20 --end-page 25
```

## 📁 Project Structure

```
whisperkittools/
├── 🎙️ Audio Transcription Scripts
│   ├── transcribe_clean.py         # Production-ready transcription with file output
│   ├── transcribe_fast.py          # Quick transcription using Tiny model
│   ├── transcribe_french.py        # Basic French transcription
│   └── transcribe_french_enhanced.py # Advanced with WER analysis
│
├── 🆕 Kyutai STT Models (New!)
│   ├── stt-1b-en_fr/              # Standard PyTorch model
│   ├── stt-1b-en_fr-candle/       # Candle framework version
│   └── stt-1b-en_fr-mlx/          # MLX framework version
│
├── 📚 book_cleaning/               # OCR Pipeline for textbooks
│   ├── gemini_ocr_formatter.py     # Gemini 2.0 Flash OCR (recommended)
│   ├── ocr_comparison.py           # Compare multiple OCR models
│   └── README.md                   # Detailed OCR documentation
│
├── 🛠️ WhisperKit Core
│   ├── whisperkit/                 # Core Python package
│   ├── scripts/                    # Model generation scripts
│   └── tests/                      # Test suite
│
└── 📊 Output Directories
    ├── transcription_results/      # Audio transcription outputs
    ├── whisper_output/             # WhisperKit model files
    └── book_cleaning/formatted_output/ # OCR results
```

## 🎙️ Audio Transcription Scripts

We provide four transcription scripts optimized for different use cases:

### transcribe_clean.py
**Purpose**: Production-ready transcription with comprehensive output
- ✅ Progress bars with minimal terminal noise
- ✅ Saves transcription, SRT subtitles, timing info, and full JSON
- ✅ Word Error Rate (WER) analysis between models
- ✅ Automatic timeout handling for slow models

**Output Structure**:
```
transcription_results/session_YYYYMMDD_HHMMSS/
├── whisper-tiny/
│   ├── transcription.txt    # Clean text
│   ├── subtitles.srt       # Subtitle file
│   ├── timing.json         # Performance metrics
│   └── full_result.json    # Complete transcription data
└── whisper-large-v3-*/     # Results for each model
```

### transcribe_fast.py
**Purpose**: Quick transcription using only Whisper Tiny
- ⚡ Fastest option (~10-30 seconds)
- 🎯 Good for quick previews and testing
- 📊 Includes basic performance metrics

### transcribe_french.py
**Purpose**: Basic multi-model French transcription
- 🇫🇷 Tests Tiny, Large-v3, and Turbo models
- 📝 Simple console output
- 🔧 Good for debugging model issues

### transcribe_french_enhanced.py
**Purpose**: Advanced analysis with WER comparison
- 📊 Detailed Word Error Rate analysis
- 📈 Performance benchmarking
- 📄 Markdown analysis reports
- ⚠️ Handles subprocess output suppression

## 🆕 Kyutai STT Models

Three versions of the Kyutai STT 1B English/French model are included:

### stt-1b-en_fr (Standard)
- **Framework**: PyTorch
- **Size**: ~1B parameters
- **Languages**: English and French
- **Features**: 0.5 second delay, semantic VAD
- **Use Case**: General purpose streaming STT

### stt-1b-en_fr-candle
- **Framework**: Candle (Rust-based)
- **Benefits**: Fast inference, low memory usage
- **Use Case**: Edge devices, embedded systems

### stt-1b-en_fr-mlx
- **Framework**: MLX (Apple Silicon optimized)
- **Benefits**: Optimized for M1/M2/M3 Macs
- **Use Case**: macOS applications

**Key Features**:
- 🎯 Streaming speech-to-text (outputs as audio arrives)
- 🇫🇷 Native French support
- ⚡ 12.5 Hz frame rate
- 📝 Capitalization and punctuation included

## 📚 Book Cleaning Pipeline

AI-powered OCR system for extracting and formatting textbook content.

**Current Status**: ✅ Production-ready with Gemini 2.5 Flash

**Features**:
- 📖 Handles complex textbook layouts (multi-column, tables)
- 🇫🇷 Excellent French character support
- 📊 Model comparison framework
- ⚡ Fast processing (13.6s for 5 pages)

**Quick Start**:
```bash
cd book_cleaning
python gemini_ocr_formatter.py "your_pdf.pdf" --start-page 1 --end-page 10
```

See [book_cleaning/README.md](book_cleaning/README.md) for detailed documentation.

## ⚙️ WhisperKit Core Features

The original WhisperKit functionality for model conversion, evaluation, and deployment.

### Installation

### Option 1: Using Poetry (Recommended)

- **Step 1:** [Fork this repository](https://github.com/argmaxinc/whisperkittools/fork)
- **Step 2:** [Install Poetry](https://python-poetry.org/docs/#installation) if you haven't already:

```shell
curl -sSL https://install.python-poetry.org | python3 -
```

- **Step 3:** [Install dependencies and create a virtual environment](https://python-poetry.org/docs/basic-usage/#installing-dependencies):

```shell
cd WHISPERKIT_ROOT_DIR && poetry install
```

- **Step 4:** [Activate the virtual environment](https://python-poetry.org/docs/basic-usage/#activating-the-virtual-environment):

```shell
poetry shell
```

### Option 2: Using pip

- **Step 1:** [Fork the whisperkittools repository](https://github.com/argmaxinc/whisperkittools/fork)
- **Step 2:** Create a Python virtual environment, e.g.:

```shell
conda create -n whisperkit python=3.11 -y && conda activate whisperkit
```

- **Step 3:** Install the base package as editable

```shell
cd WHISPERKIT_ROOT_DIR && pip install -e .
```

### Optional Dependencies

To install optional dependency groups with Poetry:

```shell
# Install pipelines dependencies (for OpenAI and MLX Whisper integration)
poetry install --with pipelines

# Install evaluation dependencies (for model evaluation)
poetry install --with evals

# Install diarization dependencies (for speaker diarization)
poetry install --with diarization

# Install development dependencies (for contributing)
poetry install --with dev

# Install multiple groups at once
poetry install --with pipelines,evals,dev
```

With pip, you can install extras using:

```shell
# Install with optional dependencies
pip install -e ".[pipelines,evals,diarization]"
```

**Note on Android Dependencies:** Android-specific dependencies (`qai-hub`, `qai-hub-models`) are currently incompatible with torch 2.6.0 and must be installed manually in a compatible environment (Python <3.11, torch <2.6.0):

```shell
pip install qai-hub qai-hub-models
```

## Model Generation (Apple)

Convert [Hugging Face Whisper Models](https://huggingface.co/models?search=whisper) (PyTorch) to [WhisperKit](https://github.com/argmaxinc/whisperkit) (Core ML) format:

```shell
whisperkit-generate-model --model-version <model-version> --output-dir <output-dir>
```

For optional arguments related to model optimizations, please see the help menu with `-h`

### Publishing Models

We host several popular Whisper model versions [hosted models](https://huggingface.co/argmaxinc/whisperkit-coreml/tree/main). These hosted models are automatically over-the-air deployable to apps integrating WhisperKit such as our example app [WhisperAX on TestFlight](https://testflight.apple.com/join/LPVOyJZW). If you would like to publish custom Whisper versions that are not already published, you can do so as follows:

- **Step 1**: Find the user or organization name that you have write access to on [Hugging Face Hub](https://huggingface.co/settings/profile). If you are logged into `huggingface-cli` locally, you may simply do:

```shell
huggingface-cli whoami
```

If you don't have a write token yet, you can generate it [on Hugging Face](https://huggingface.co/settings/tokens).

- **Step 2**: Point to the model repository that you would like to publish to, e.g. `my-org/my-whisper-repo-name`, with the `MODEL_REPO_ID` environment variable and specify the name of the source PyTorch Whisper repository (e.g. [distil-whisper/distil-small.en](https://huggingface.co/distil-whisper/distil-small.en))

```shell
MODEL_REPO_ID=my-org/my-whisper-repo-name whisperkit-generate-model --model-version distil-whisper/distil-small.en --output-dir <output-dir>
```

If the above command is successfuly executed, your model will have been published to `hf.co/my-org/my-whisper-repo-name/distil-whisper_distil-small.en`!

## Model Generation (Android)

WhisperKit currently only supports Qualcomm AI Hub Whisper models on Hugging Face:

- [tiny.en](https://huggingface.co/qualcomm/Whisper-Tiny-En)
- [base.en](https://huggingface.co/qualcomm/Whisper-Base-En)
- [small.en](https://huggingface.co/qualcomm/Whisper-Small-En)

whisperkittools generates 3 more support models for input preprocessing and output postprocessing used in the WhisperKitAndroid pipeline. These are all published on Hugging Face [in this repository](https://huggingface.co/argmaxinc/whisperkit-android/tree/main). Nonetheless, you may regenerate these models if you wish by following these steps:

- **Step 1**: Create an account at [aihub.qualcomm.com](aihub.qualcomm.com)
- **Step 2**: Set your API key locally as `qai-hub configure --api_token`
- **Step 3**: Install extra dependencies via `pip install -e '.[android]'` (Note that this requires `python<3.11`)
- **Step 4**: Execute `python tests/test_aihub.py --persistent-cache-dir <output-path>`

Stay tuned for more options for generating models without creating an account and more model version coverage!

## Model Evaluation (Apple)

Evaluate ([Argmax-](https://huggingface.co/argmaxinc/whisperkit-coreml) or developer-published) models on speech recognition datasets:

```shell
whisperkit-evaluate-model --model-version <model-version> --output-dir <output-dir> --evaluation-dataset {librispeech-debug,librispeech,earnings22}
```

Install additional dependencies via:

```shell
pip install -e '.[evals,pipelines]'
```

By default, this command uses the latest `main` branch commits from `WhisperKit` and searches within [Argmax-published](https://huggingface.co/argmaxinc/whisperkit-coreml) model repositories. For optional arguments related to code and model versioning, please see the help menu with `-h`.
To explore these repositories, click [Argmax WhisperKit CoreML](https://huggingface.co/argmaxinc/whisperkit-coreml).

We continually publish the evaluation results of Argmax-hosted models [Argmax WhisperKit Evals](https://huggingface.co/datasets/argmaxinc/whisperkit-evals) as part of our continuous integration tests.

### Model Evaluation on Custom Dataset

If you would like to evaluate WhisperKit models on your own dataset:

- **Step 1**: Publish a dataset on the [Hub](https://huggingface.co/new-dataset) with the same simple structure as this [toy dataset](https://huggingface.co/datasets/argmaxinc/librispeech-debug) (audio files + `metadata.json`)
- **Step 2:** Run evaluation with environment variables as follows:

```shell
export CUSTOM_EVAL_DATASET="my-dataset-name-on-hub"
export DATASET_REPO_OWNER="my-user-or-org-name-on-hub"
export MODEL_REPO_ID="my-org/my-whisper-repo-name" # if evaluating self-published models
whisperkit-evaluate-model --model-version <model-version> --output-dir <output-dir> --evaluation-dataset my-dataset-name-on-hub
```

## Python Inference

Use the unified Python wrapper for several on-device Whisper frameworks:

- [WhisperKit](https://github.com/argmaxinc/whisperkit)
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp)
- [mlx-examples/whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper)
- [WhisperOpenAIAPI (Server-side)](https://platform.openai.com/docs/guides/speech-to-text)

Install additional dependencies via:

```shell
pip install -e '.[pipelines]'
```

```python
from whisperkit.pipelines import WhisperKit, WhisperCpp, WhisperMLX, WhisperOpenAIAPI

pipe = WhisperKit(whisper_version="openai/whisper-large-v3", out_dir="/path/to/out/dir")
print(pipe("audio.{wav,flac,mp3}"))
```

**Note:** `WhisperCpp` requires `ffmpeg` to be installed. Recommended installation is with `brew install ffmpeg`
**Note:** `WhisperOpenAIAPI` requires setting `OPENAI_API_KEY` as an environment variable

## Example SwiftUI App

[TestFlight](https://testflight.apple.com/join/LPVOyJZW)

[Source Code (MIT License)](https://github.com/argmaxinc/whisperkit/tree/main/Examples/WhisperAX)

This app serves two purposes:

- Base template for developers to freely customize and integrate parts into their own app
- Real-world testing/debugging utility for custom Whisper versions or WhisperKit features before/without building an app.

Note that the app is in beta and we are actively seeking feedback to improve it before widely distributing it.

## WhisperKit Quality and Performance Benchmarks

Please visit the [WhisperKit Benchmarks](https://huggingface.co/spaces/argmaxinc/whisperkit-benchmarks) Hugging Face Space for detailed benchmark results. Here is a [brief explanation](https://x.com/argmaxinc/status/1851723587423756680) to help with navigation of the results. This benchmark is updated for every non-patch release on virtually all supported devices.

## FAQ

**Q1**: `xcrun: error: unable to find utility "coremlcompiler", not a developer tool or in PATH`
**A1**: Ensure Xcode is installed on your Mac and run `sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer`.

## Citation

If you use WhisperKit for something cool or just find it useful, please drop us a note at [info@argmaxinc.com](mailto:info@argmaxinc.com)!

If you use WhisperKit for academic work, here is the BibTeX:

```bibtex
@misc{whisperkit-argmax,
title = {WhisperKit},
author = {Argmax, Inc.},
year = {2024},
URL = {https://github.com/argmaxinc/WhisperKit}
}
```
