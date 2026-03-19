# Contributing to grabtl

Thank you for your interest in contributing! This document provides guidelines for development.

## Development Setup

### Prerequisites
- Python 3.11+
- Windows 10/11 (for winocr / Windows OCR)
- Git

### Environment Setup
```bash
git clone https://github.com/<owner>/grabtl.git
cd grabtl
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[all]"
pip install ruff mypy pytest pip-audit pip-licenses
```

### Running Tests
```bash
pytest tests/
ruff check src/
ruff format --check src/
mypy --strict src/
```

## Architecture Rules

These rules are enforced in CI and must not be violated:

1. **`core/` must not import PySide6.** The core library is a standalone Python package usable without GUI. This is verified by CI.

2. **All Translators must declare `allowed_endpoints`.** Any network communication to undeclared domains will cause CI tests to fail.

3. **`requests` must never use `verify=False`.** TLS certificate verification must always be enabled.

4. **New OCR/Translation engines must implement the Protocol interface.** See `core/ocr/base.py` and `core/translation/base.py`.

## Adding a New Translation Engine

1. Create `core/translation/your_engine.py`
2. Implement the `Translator` Protocol from `core/translation/base.py`
3. Define `allowed_endpoints` (empty list if local-only)
4. Add unit tests in `tests/unit/test_your_engine.py`
5. Add the engine to the README and docs

See [docs/plugin-guide.md](docs/plugin-guide.md) for detailed instructions.

## Code Style

- **Formatter:** `ruff format`
- **Linter:** `ruff check`
- **Type checker:** `mypy --strict`
- **Docstrings:** Google style. Public API docstrings in English; internal comments may be in Japanese.
- **Commit messages:** [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

## Pull Request Process

1. Create a branch from `main`
2. Ensure all tests pass locally
3. Fill in the PR template (will be provided)
4. **Security-sensitive changes:** PRs that modify anything in `core/security/`, `core/translation/` (especially network code), or `allowed_endpoints` require extra review attention
5. Wait for CI to pass and at least one approval

## Security Considerations for Contributors

When reviewing or writing code, pay special attention to:

- Any use of `requests`, `urllib`, `socket`, or `http.client`
- Changes to `allowed_endpoints` in any Translator implementation
- Any file I/O involving captured screenshots (should be memory-only)
- Any changes to `keystore.py` or API key handling
- Dependencies added to `pyproject.toml` — check license compatibility

## Versioning

This project follows [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH).

- **0.x.x:** Early development. Breaking API changes may occur.
- **1.0.0:** Stability declaration for Protocol interfaces (`OCREngine`, `Translator`).
- Protocol interface changes require a **MAJOR** version bump.

## Language

- **Issues / Discussions:** Japanese or English are both welcome
- **Code comments / docstrings (public API):** English
- **Commit messages:** English
- **Documentation:** English primary, Japanese translation provided for user-facing docs
