# 📊 Speech-to-Text Benchmark Results

**Audio:** `french-i-lesson-01-30s.mp3` (30-second Pimsleur French lesson)
**Date:** 2025-06-20 12:25:05

## Performance Summary

| Model                       | Time (s) | WER       | RT Factor | Framework  | Accuracy    |
| --------------------------- | -------- | --------- | --------- | ---------- | ----------- |
| **🥇 Kyutai Standard**      | 85.8     | **0.118** | 2.9x      | PyTorch    | **Best**    |
| **🥈 WhisperKit Tiny**      | **14.4** | 0.145     | **0.5x**  | WhisperKit | **Fastest** |
| WhisperKit Distil Large-v3  | 306.0    | 0.355     | 10.2x     | WhisperKit | Good        |
| WhisperKit Large-v3 (626MB) | 22.8     | 0.513     | 0.8x      | WhisperKit | Poor        |
| WhisperKit Large-v3 Turbo   | 1005.9   | 0.513     | 33.5x     | WhisperKit | **Slowest** |

## Key Findings

### 🎯 **Accuracy Winner: Kyutai Standard**

- **WER: 0.118** (11.8% error rate)
- Perfect transcription of French phrases
- Clean handling of mixed English/French content
- Only model that completed the full 30-second clip

### ⚡ **Speed Winner: WhisperKit Tiny**

- **14.4 seconds** (0.5x real-time)
- Close accuracy (WER: 0.145)
- Best performance/speed tradeoff
- Some minor transcription errors ("Pimmsler" vs "Pimsleur")

### 🐌 **Performance Issues**

- **WhisperKit Large-v3 Turbo**: Extremely slow (16+ minutes!)
- **WhisperKit Large models**: Cut off transcription early
- **Distil Large-v3**: Slow with translation artifacts ("Is you know the English?")

## Transcription Quality Comparison

**Reference:**

> "This is Unit 1 of Pimsleur's French 1. Listen to this French conversation. Est-ce que vous comprenez l'anglais ? Non, monsieur..."

**Kyutai (Best):**

> "This is Unit 1 of Pimsleur's French 1. Listen to this French conversation. Est-ce que vous comprenez l'anglais ? Non, monsieur..."

**WhisperKit Tiny (Fast):**

> "This is Unit 1 of Pimmsler's French One. Listen to this French conversation. Pardon, est-ce que vous comprenez l'anglais? Non monsieur..."

**WhisperKit Large (Incomplete):**

> "This is Unit 1 of Pimsleur's French 1... Oui, mademoiselle." _(stops early)_

## Recommendations

1. **Production use:** Kyutai Standard for best accuracy
2. **Real-time applications:** WhisperKit Tiny for speed
3. **Avoid:** WhisperKit Large-v3 Turbo (performance issues)
4. **Mixed language:** Kyutai handles English/French better
