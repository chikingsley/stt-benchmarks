# French Textbook OCR Processing

Automated OCR processing for "Colloquial French 1" textbook using Gemini 2.5-Flash with intelligent post-processing.

## 🚀 Current Pipeline

**PDF → Improved OCR (Gemini 2.5-Flash) → Smart Post-Processor → Clean Markdown**

This pipeline reduces manual editing work by **~90%** compared to basic OCR.

## 📁 Project Structure

```
book_cleaning/
├── Colloquial French 1.pdf          # Source textbook
├── unit2_processor.py               # Main processing script
├── markdown_post_processor.py       # Post-processing automation
├── .env                            # API keys (not in repo)
├── formatted_output/               # Current results
│   └── unit2_optimized_output/     # Latest Unit 2 processing
└── archive/                        # Archived experiments
    ├── v1_experiments/             # Old comparison tests
    └── old_sessions/               # Previous processing attempts
```

## 🛠️ Usage

### Process a unit (e.g., Unit 2)

```bash
poetry run python unit2_processor.py "Colloquial French 1.pdf" --start-page 20 --end-page 40
```

### Post-process existing OCR output

```bash
python markdown_post_processor.py input_file.md --output clean_file.md
```

## 🎯 Key Features

### Intelligent OCR Prompting

- **Paragraph merging**: Automatically combines broken lines within paragraphs
- **Header removal**: Strips page headers like "Unit 2: In town 23"
- **French formatting**: Preserves accents and special characters
- **Structure preservation**: Maintains exercises, dialogues, and tables

### Smart Post-Processing

- **Line merging**: Fixes remaining paragraph breaks (87% reduction vs basic OCR)
- **Header cleanup**: Removes any remaining page numbers/headers
- **Markdown formatting**: Applies consistent style (ruff-like auto-formatting)
- **Split formatting fix**: Repairs bold/italic text broken across lines

## 📊 Performance Results

**Unit 2 Test (21 pages, pages 20-40):**

| Metric                   | Baseline OCR | Optimized Pipeline | Improvement   |
| ------------------------ | ------------ | ------------------ | ------------- |
| Paragraphs needing merge | 220          | 29                 | 87% reduction |
| Headers removed          | 13           | 0 (prevented)      | 100%          |
| Processing time          | 81.6s        | 25.9s              | 68% faster    |
| Manual editing needed    | ~100 fixes   | ~10 fixes          | 90% reduction |

## 🔄 Processing Pipeline Details

### Step 1: PDF → Images

- High-resolution conversion (2x scale)
- Batch processing for memory efficiency
- PNG format for quality

### Step 2: Improved OCR (Gemini 2.5-Flash)

```
CRITICAL INSTRUCTIONS FOR TEXT EXTRACTION:
1. Merge lines that belong to the same paragraph
2. Skip page headers like "Unit 2: In town 23"
3. Preserve French accents and formatting
4. Keep exercises and dialogues structured
```

### Step 3: Post-Processing

- Intelligent paragraph detection and merging
- Regex-based header removal
- Markdown auto-formatting
- Split formatting repair

## 🧪 Archived Experiments

The `archive/v1_experiments/` contains:

- **Model comparisons**: Gemini 2.5-Pro vs 2.5-Flash vs 2.0-Flash
- **Hybrid QA testing**: Flash→Pro quality assurance attempts
- **Mistral OCR tests**: Alternative OCR provider evaluation
- **Baseline results**: Original processing without improvements

## 📈 Next Steps

1. **Scale to full book**: Process Units 3-16 using optimized pipeline
2. **Table formatting**: Add specific verb conjugation table handling
3. **Batch processing**: Create script for processing multiple units
4. **Quality metrics**: Implement automated accuracy scoring

## 🔧 Setup

1. Install dependencies: `poetry install`
2. Add API key to `.env`: `GOOGLE_API_KEY=your_key_here`
3. Run processing: `poetry run python unit2_processor.py "Colloquial French 1.pdf"`

## 📝 Manual Editing Workflow

After automated processing, typical remaining manual edits:

1. Fix any table formatting (verb conjugations)
2. Adjust dialogue speaker formatting if needed
3. Verify exercise numbering in complex layouts
4. Final markdown style check

The automated pipeline handles ~90% of the work, leaving only these edge cases for manual review.

---

## 📊 Historical Test Results (Archived)

For detailed comparison of models and experimental approaches, see `archive/v1_experiments/`:

- **5-page model comparison**: Gemini 2.5-Pro (74% accuracy, 47.7s) vs 2.5-Flash (63% accuracy, 13.6s)
- **Hybrid QA analysis**: Found to be impractical (6x slower for minimal improvement)
- **Layout challenge solutions**: Multi-column handling, exercise numbering fixes
