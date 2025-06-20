# 📊 Speech-to-Text Benchmark Results

**Audio:** `french-i-lesson-01-30s.mp3`  
**Date:** 2025-06-20 15:42:50  
**Reference:** 76 words  

## Performance Summary

| Model | Time (s) | WER | RT Factor | Framework | Status |
|-------|----------|-----|-----------|-----------|--------|
| **kyutai-standard** | 64.2 | **0.118** | 2.1x | PyTorch | 🥇 Best Accuracy |
| **whisperkit-tiny** | 42.8 | **0.145** | 1.4x | WhisperKit | ✅ Success |
| **whisperkit-distill-large-v3** | 12.1 | **0.355** | 0.4x | WhisperKit | ✅ Success |
| **whisperkit-large-v3-626mb** | 17.8 | **0.513** | 0.6x | WhisperKit | ✅ Success |
| **whisperkit-large-v3-turbo-632mb** | 19.4 | **0.513** | 0.6x | WhisperKit | ✅ Success |

## Key Findings

### 🎯 **Accuracy Winner: kyutai-standard**
- **WER: 0.118** (11.8% error rate)
- Time: 64.2s

### ⚡ **Speed Winner: whisperkit-distill-large-v3**
- **12.1 seconds** (0.4x real-time)
- WER: 0.355


## Transcription Quality Comparison

**Reference:**
> this is unit 1 of pimsleur's french 1 listen to this french conversation est-ce que vous comprenez l'anglais  non monsieur je ne comprends pas l'anglais je comprends un peu le français est-ce que vous...

**kyutai-standard (WER: 0.118):**
> [1;34m[Info][0m retrieving checkpoint [1;34m[Info][0m mimi loaded [1;34m[Info][0m moshi loaded This is Unit 1 of Pimsleur's French 1. Listen to this French conversation. Est-ce que vous comprene...

**whisperkit-tiny (WER: 0.145):**
> -This is Unit 1 of Pimmsler's French One. -Listen to this French conversation. -Pardon, est-ce que vous comprenez l'anglais? -Non monsieur, je ne comprends pas l'anglais. -Je comprends un peu le franç...

**whisperkit-large-v3-626mb (WER: 0.513):**
> This is Unit 1 of Pimsleur's French 1. Listen to this French conversation. Pardon, est-ce que vous comprenez l'anglais? Non, monsieur. Je ne comprends pas l'anglais. Je comprends un peu le français. E...

**whisperkit-large-v3-turbo-632mb (WER: 0.513):**
> This is Unit 1 of Pimsleur's French 1. Listen to this French conversation. Pardon, est-ce que vous comprenez l'anglais? Non, monsieur. Je ne comprends pas l'anglais. Je comprends un peu le français. E...

**whisperkit-distill-large-v3 (WER: 0.355):**
> This is Unit 1 of Pimzler's French 1. Listen to this French conversation. Pardon. Is you know the English? No, monsieur. I don't understand the English. I understand a little the French. Is that you a...


---
*Generated on 2025-06-20 at 15:42:50*