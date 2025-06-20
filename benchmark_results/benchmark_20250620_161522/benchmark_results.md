# 📊 Speech-to-Text Benchmark Results

**Audio:** `french-i-lesson-01-30s.mp3`
**Date:** 2025-06-20 16:17:44
**Reference:** 76 words

## Performance Summary

| Model                               | Time (s) | WER       | RT Factor | Framework  | Status           |
| ----------------------------------- | -------- | --------- | --------- | ---------- | ---------------- |
| **kyutai-standard**                 | 72.2     | **0.000** | 2.4x      | PyTorch    | 🥇 Best Accuracy |
| **whisperkit-tiny**                 | 20.0     | **0.145** | 0.7x      | WhisperKit | ✅ Success       |
| **whisperkit-distill-large-v3**     | 12.9     | **0.355** | 0.4x      | WhisperKit | ✅ Success       |
| **whisperkit-large-v3-turbo-632mb** | 17.5     | **0.513** | 0.6x      | WhisperKit | ✅ Success       |
| **whisperkit-large-v3-626mb**       | 19.0     | **0.513** | 0.6x      | WhisperKit | ✅ Success       |

## Key Findings

### 🎯 **Accuracy Winner: kyutai-standard**

- **WER: 0.000** (0.0% error rate)
- Time: 72.2s

### ⚡ **Speed Winner: whisperkit-distill-large-v3**

- **12.9 seconds** (0.4x real-time)
- WER: 0.355

## Transcription Quality Comparison

**Reference:**

> this is unit 1 of pimsleur's french 1 listen to this french conversation est-ce que vous comprenez l'anglais non monsieur je ne comprends pas l'anglais je comprends un peu le français est-ce que vous...

**kyutai-standard (WER: 0.000):**

> This is Unit 1 of Pimsleur's French 1. Listen to this French conversation. Est-ce que vous comprenez l'anglais ? Non, monsieur. Je ne comprends pas l'anglais. Je comprends un peu le français. Est-ce q...

**whisperkit-tiny (WER: 0.145):**

> -This is Unit 1 of Pimmsler's French One. -Listen to this French conversation. -Pardon, est-ce que vous comprenez l'anglais? -Non monsieur, je ne comprends pas l'anglais. -Je comprends un peu le franç...

**whisperkit-large-v3-626mb (WER: 0.513):**

> This is Unit 1 of Pimsleur's French 1. Listen to this French conversation. Pardon, est-ce que vous comprenez l'anglais? Non, monsieur. Je ne comprends pas l'anglais. Je comprends un peu le français. E...

**whisperkit-large-v3-turbo-632mb (WER: 0.513):**

> This is Unit 1 of Pimsleur's French 1. Listen to this French conversation. Pardon, est-ce que vous comprenez l'anglais? Non, monsieur. Je ne comprends pas l'anglais. Je comprends un peu le français. E...

**whisperkit-distill-large-v3 (WER: 0.355):**

> This is Unit 1 of Pimzler's French 1. Listen to this French conversation. Pardon. Is you know the English? No, monsieur. I don't understand the English. I understand a little the French. Is that you a...

---

_Generated on 2025-06-20 at 16:17:44_
