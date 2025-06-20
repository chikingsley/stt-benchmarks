# UV Migration Guide

## 🎉 Migration from Poetry to UV Complete!

### Quick Command Reference

| Task | Poetry | UV |
|------|--------|-----|
| Install dependencies | `poetry install` | `uv sync` |
| Install with extras | `poetry install --with evals` | `uv sync --extra evals` |
| Install all extras | `poetry install --all-extras` | `uv sync --all-extras` |
| Add dependency | `poetry add package` | `uv add package` |
| Add dev dependency | `poetry add --group dev package` | `uv add --dev package` |
| Run command | `poetry run python script.py` | `uv run python script.py` |
| Update lock file | `poetry lock` | `uv lock` |
| Build package | `poetry build` | `uv build` |
| Show environment | `poetry env info` | `uv venv` |

### Available Extras/Groups

**Optional Dependencies (extras):**
- `pipelines`: openai, mlx-whisper
- `diarization`: pyannote-audio  
- `evals`: jiwer, soundfile, librosa, datasets, evaluate, etc.

**Dev Dependencies:**
- Automatically included: flake8, pytest, alive-progress

### Usage Examples

```bash
# Basic install
uv sync

# Install with evaluation dependencies
uv sync --extra evals

# Install everything
uv sync --all-extras

# Run scripts
uv run python examples/benchmarks/comprehensive_stt_benchmark.py

# Run tests
uv run pytest

# Add new dependency
uv add new-package

# Add dev dependency
uv add --dev new-dev-package
```

### Benefits of UV

- **10-100x faster** than pip/poetry
- **Simpler commands** 
- **Built-in Python version management**
- **Universal lockfile** (uv.lock)
- **Automatic venv creation**

### Troubleshooting

If you see linking warnings:
```bash
export UV_LINK_MODE=copy
```

### Rollback (if needed)

Poetry files backed up:
- `pyproject.toml.poetry-backup`
- `poetry.lock.backup`