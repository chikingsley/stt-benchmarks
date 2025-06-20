# Book Formatter V2 - Usage Examples

## Key Improvements Over V1

✅ **Structure Analysis** - Automatically generates YAML config based on book structure  
✅ **OCR Integration** - Uses mistral-ocr-latest for pristine text extraction  
✅ **Enhanced Formatting** - Preserves ALL content including English translations, bold terms  
✅ **Granular Control** - Unit-by-unit processing, preview mode  
✅ **Token Tracking** - Real-time usage monitoring and cost estimation  
✅ **Interactive Config** - Review and approve generated configurations  

## Usage Examples

### 1. Analyze Book Structure Only
```bash
# Generate YAML configuration from book structure
poetry run python book_cleaning/book_formatter_v2.py colloqual_french.md --mode analyze
```
**Output**: `generated_config.yaml` with detected patterns and formatting rules

### 2. Preview Single Unit Processing  
```bash
# Preview what Unit 2 processing would look like
poetry run python book_cleaning/book_formatter_v2.py colloqual_french.md --mode unit --start-unit 2 --preview
```
**Shows**: Token estimate, content boundaries, processing plan

### 3. Process Single Unit with Custom Config
```bash
# Process Unit 2 only with reviewed configuration
poetry run python book_cleaning/book_formatter_v2.py colloqual_french.md --mode unit --start-unit 2 --config my_config.yaml
```
**Output**: Enhanced formatting with preserved content

### 4. Process Unit Range
```bash
# Process Units 2-5 for batch validation
poetry run python book_cleaning/book_formatter_v2.py colloqual_french.md --mode unit --start-unit 2 --end-unit 5
```

### 5. Full Book Processing
```bash
# Process entire book with auto-generated config
poetry run python book_cleaning/book_formatter_v2.py colloqual_french.md --mode full
```

## Key Features in Action

### Structure Analysis → YAML Generation
The analyzer examines your book and creates configurations like:

```yaml
book_info:
  title: "Colloquial French"
  type: "language_textbook" 
  language: "french"

section_patterns:
  unit: "Unit \\[?(\\d+)\\]?"
  dialogue: "Dialogue \\d+"
  exercise: "Exercise \\d+"
  language_points: "Language points"

formatting_rules:
  preserve_bold: true
  bold_terms: ["UN", "UNE", "LE", "LA", "est-ce que"]
  heading_levels:
    unit: 2
    dialogue: 3
    exercise: 4

special_sections:
  - "Did you notice"
  - "Grammar rules"
```

### Enhanced Formatting Prompt
Based on your YAML config, creates targeted prompts that:
- **Preserve ALL content** (addresses V1 missing content issue)
- **Bold specific terms** (UN, UNE, LE, LA from your feedback)
- **Keep English translations** (fixes missing dialogue translations)
- **Maintain section structure** (proper heading hierarchy)

### Token Usage Tracking
```
📊 Real-time tracking:
- OCR tokens: 1,250
- Analysis tokens: 890
- Formatting tokens: 4,200
- Total cost estimate: $0.012
- Rate limit status: 45k/500k tokens this minute
```

### Interactive Configuration Review
```
📋 Generated config: ./generated_config.yaml
🔍 Review the configuration above and press Enter to continue...
```
*Allows you to edit YAML before processing starts*

## Addressing V1 Issues

| V1 Issue | V2 Solution |
|----------|-------------|
| Missing English translations | Enhanced prompt specifically preserves ALL translations |
| Un-bolded terms (UN, UNE) | YAML config specifies exact terms to bold |
| Missing "Did you notice" sections | Special sections list in config |
| Wrong unit naming | Structure analysis detects correct patterns |
| Incomplete dialogue formatting | Preserves both French and English parts |
| Missing intro text | "Preserve ALL content" requirement in prompt |

## Workflow Recommendation

1. **Analyze** → Generate YAML config for your book type
2. **Review** → Edit YAML to match your specific needs  
3. **Test** → Process single unit to validate quality
4. **Iterate** → Refine config based on test results
5. **Batch** → Process remaining units with validated config

## Next Steps

Ready to test V2? Let's start with structure analysis:

```bash
export MISTRAL_API_KEY="your_key"
poetry run python book_cleaning/book_formatter_v2.py book_cleaning/colloqual_french.md --mode analyze
```

This will generate a YAML config specific to your French textbook that we can review and refine before processing!