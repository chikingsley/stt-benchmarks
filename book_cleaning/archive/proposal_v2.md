# Book Formatting Automation - Proposal V2

## Version 1 Completed Features ✅

### Phase 1: Setup & Dependencies
- [x] Add Poetry dependencies (mistralai, alive-progress)
- [x] Set up project structure in `book_cleaning/`

### Phase 2: Core Architecture  
- [x] Create `book_formatter.py` with batch processor
- [x] Implement cascading retry pattern (mistral-medium → mistral-large)
- [x] Add progress tracking with alive-progress
- [x] Build text preprocessor for OCR cleanup

### Phase 3: Processing Pipeline
- [x] Batch processing strategy (100 lines/batch)
- [x] Infinite retry pattern with model alternation
- [x] Section-specific formatting rules (dialogues, exercises, language points)
- [x] Automatic Unit 2+ detection and processing

### Phase 4: Basic Output
- [x] Markdown generation following Unit 1 patterns
- [x] Processing summary and statistics
- [x] File organization and timestamped results

---

## Version 2 Enhancement Plan 🚀

### Core Improvements Needed

#### 1. Granular Processing Control
- [ ] Command line options for processing modes:
  ```bash
  --mode unit|section|chapter|full
  --start-unit 2 --end-unit 5
  --preview-only  # Show what would be processed
  --resume-from checkpoint.json
  ```
- [ ] Unit-by-unit processing capability
- [ ] Section-level granular control
- [ ] Preview mode before actual processing
- [ ] Checkpoint/resume functionality

#### 2. Token Usage & Rate Monitoring 📊
```python
class TokenTracker:
    - [ ] Real-time token counting (tiktoken integration)
    - [ ] Rate limit tracking: 1/s, 500k/min, 1B/mo  
    - [ ] Cost estimation ($0.002/1k tokens for medium/large)
    - [ ] ETA calculation based on current usage
    - [ ] Auto-pause when approaching limits
    - [ ] Token usage analytics and reporting
```

#### 3. Book-Agnostic Configuration 📚
```yaml
# book_config.yaml
book_type: "language_textbook"
section_patterns:
  unit: "Unit \\[?(\\d+)\\]?"
  dialogue: "Dialogue \\d+"
  exercise: "Exercise \\d+"
formatting:
  preserve_bold: true
  convert_italics_to: "**text**"
  heading_levels:
    unit: 2
    section: 3
```
- [ ] YAML configuration system
- [ ] Multiple book type templates
- [ ] Custom section pattern detection
- [ ] Flexible formatting rules
- [ ] Template library for different textbook types

#### 4. Interactive Decision Making 🤔
```python
# On ambiguous sections:
"Found potential heading: 'Les verbes irreguliers'"
[1] H2: ## Les verbes irreguliers  
[2] H3: ### Les verbes irreguliers
[3] Bold: **Les verbes irreguliers**
[s] Skip this section
Choice: _
```
- [ ] Interactive mode for ambiguous formatting decisions
- [ ] Decision caching to avoid repeated questions
- [ ] Confidence scoring for automatic vs manual decisions
- [ ] Batch decision review mode

#### 5. Quality Validation System ✅
```python
class QualityChecker:
    - [ ] Markdown syntax validation
    - [ ] French accent preservation check  
    - [ ] Reference link integrity validation
    - [ ] Section structure consistency verification
    - [ ] Content length preservation (±5% tolerance)
    - [ ] Table of contents link validation
    - [ ] CD track reference preservation
```

### Architecture Changes

**Current V1**: Monolithic batch processor
**Proposed V2**: Modular pipeline with checkpoints

```
Input → Analyzer → Sectioner → Formatter → Validator → Output
         ↓           ↓          ↓          ↓
    book_config  checkpoints  decisions  quality_report
```

### Key Variables to Make Configurable

#### Document Structure Detection
- [ ] Section detection patterns (regex-based)
- [ ] Heading hierarchy mapping (H1, H2, H3 assignment)
- [ ] Numbering schemes (1.1, 1.a, Exercise 1, etc.)
- [ ] Reference formats (CD 1;2, p.45, Figure 3.2)
- [ ] Language-specific patterns (French vs Spanish vs German)

#### Formatting Decision Framework
- [ ] Bold/italic/underline preservation vs conversion rules
- [ ] Table handling strategies (keep structure vs simplify)
- [ ] List formatting preferences (bullets vs numbers vs mixed)
- [ ] Code block detection for grammar rules and examples
- [ ] Quote formatting for dialogues and examples

#### Content Cleaning Intelligence
- [ ] Page header/footer removal patterns
- [ ] OCR artifact detection (broken words, spacing issues)
- [ ] Image caption handling and placement
- [ ] Copyright notice and publisher info removal
- [ ] Footnote and reference management

### Implementation Phases

#### Phase 1: Core Enhancements (Next 2-3 hours)
- [ ] Add tiktoken for token tracking and cost estimation
- [ ] Implement `--mode unit` for single unit processing
- [ ] Add `--preview` functionality to show processing plan
- [ ] Create basic YAML config file support
- [ ] Add real-time token usage monitoring with rate limits

#### Phase 2: Quality & Flexibility (Future sprint)
- [ ] Interactive mode for ambiguous formatting decisions
- [ ] Multiple book type configuration templates
- [ ] Advanced quality validation with detailed reports
- [ ] Resume/checkpoint system for large books
- [ ] Confidence scoring and automatic decision making

#### Phase 3: Advanced Features (Future enhancement)
- [ ] OCR integration for PDF comparison and correction
- [ ] Multi-language support and detection
- [ ] Batch book processing for series
- [ ] Integration with version control for change tracking
- [ ] Web interface for non-technical users

### Enhanced CLI Interface

```bash
# Preview Unit 2 only with token estimation
poetry run python book_formatter.py --mode unit --start 2 --end 2 --preview --track-tokens

# Process with cost controls and interactive decisions  
poetry run python book_formatter.py --max-cost 5.00 --interactive --config french_textbook.yaml

# Resume from checkpoint with quality validation
poetry run python book_formatter.py --resume-from checkpoint_20240618.json --validate-quality

# Batch process multiple units with progress checkpoints
poetry run python book_formatter.py --mode unit --start 2 --end 16 --checkpoint-every 3
```

### Success Metrics

#### Technical Metrics
- [ ] Token usage efficiency (tokens per formatted page)
- [ ] Processing speed (pages per minute)
- [ ] Quality score (markdown validation + content preservation)
- [ ] Error rate and retry statistics

#### User Experience Metrics  
- [ ] Setup time for new book types
- [ ] Manual intervention frequency
- [ ] Processing accuracy requiring minimal post-editing
- [ ] Configuration reusability across similar books

### Risk Mitigation

#### Rate Limiting & Costs
- [ ] Hard limits with auto-pause before hitting API limits
- [ ] Cost estimation with user confirmation for expensive operations
- [ ] Graceful degradation when rate limited
- [ ] Local caching to avoid re-processing same content

#### Quality Assurance
- [ ] Comprehensive validation before final output
- [ ] Diff reporting between input and output content
- [ ] Rollback capability for unsatisfactory results
- [ ] A/B testing framework for formatting improvements

---

## Current Status: V1 Complete ✅, V2 Phase 1 Ready 🚀

**Next Steps:**
1. Test V1 output quality and gather lessons learned
2. Implement Phase 1 enhancements based on V1 feedback  
3. Create first book-agnostic configuration template
4. Begin Phase 2 planning based on real-world usage patterns