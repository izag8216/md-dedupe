# Contributing to md-dedupe

Thank you for your interest in contributing!

## Development Setup

```bash
# Clone and install with dev dependencies
git clone https://github.com/izag8216/md-dedupe.git
cd md-dedupe
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Development Workflow

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Run tests: `pytest tests/ -v`
4. Run linter: `ruff check src/ tests/`
5. Commit with conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
6. Push and open a Pull Request

## Coding Standards

- Python 3.10+ (use modern type hints)
- Line length: 100 characters
- Follow PEP 8 (enforced by ruff)
- All public functions need docstrings
- Tests required for new functionality

## Commit Convention

```
feat: add new detection method
fix: resolve false positive in URL comparison
docs: update CLI usage examples
test: add edge case tests for similarity
refactor: simplify cluster merging logic
```

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add tests for new features
4. Keep PRs focused and small
