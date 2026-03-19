# Plugin Guide — Adding OCR / Translation Engines

This guide explains how to add a new OCR engine or translation engine to grabtl.

## Architecture Overview

All engines implement a Protocol interface defined in `core/ocr/base.py` or `core/translation/base.py`. This allows the pipeline to use any engine without knowing its implementation details.

```
Pipeline:  capture → [OCREngine] → glossary → [Translator] → result
                         ↑                          ↑
                    Pluggable                   Pluggable
```

## Adding a Translation Engine

### 1. Create the implementation

```python
# src/grabtl/core/translation/my_engine.py
from grabtl.core.translation.base import Translator


class MyTranslator:
    """Example custom translator."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key

    def translate(self, text: str, source: str, target: str) -> str:
        # Your translation logic here
        return translated_text

    @property
    def requires_api_key(self) -> bool:
        return True  # or False for local engines

    @property
    def is_local(self) -> bool:
        return False  # True if no network communication

    @property
    def allowed_endpoints(self) -> list[str]:
        # REQUIRED: Declare all domains this engine communicates with.
        # CI tests will fail if the engine contacts undeclared domains.
        return ["api.my-service.com"]

    @property
    def name(self) -> str:
        return "My Translation Engine"
```

### 2. Key rules

- **`allowed_endpoints` is mandatory.** Return an empty list `[]` for local-only engines. Any network call to a domain not in this list will be caught by CI tests.
- **Never set `verify=False`** in any HTTP request. TLS verification must always be enabled.
- **Handle API keys via the `keystore` module**, not directly from environment variables or config files.
- **Do not import PySide6** from `core/`. The core library must remain GUI-independent.

### 3. Add tests

```python
# tests/unit/test_my_engine.py
import pytest
from grabtl.core.translation.my_engine import MyTranslator


class TestMyTranslator:
    def test_implements_protocol(self) -> None:
        engine = MyTranslator(api_key="test")
        assert hasattr(engine, "translate")
        assert hasattr(engine, "requires_api_key")
        assert hasattr(engine, "is_local")
        assert hasattr(engine, "allowed_endpoints")

    def test_allowed_endpoints_declared(self) -> None:
        engine = MyTranslator()
        endpoints = engine.allowed_endpoints
        assert isinstance(endpoints, list)
        # Verify all endpoints are valid domain patterns
        for ep in endpoints:
            assert "." in ep or ep.startswith("127.0.0.1")
```

### 4. Register in the pipeline

Add your engine to the available engines list in the settings/configuration layer (not in `core/pipeline.py` itself).

## Adding an OCR Engine

Same pattern as translation engines, but implement `OCREngine` Protocol from `core/ocr/base.py`:

```python
from grabtl.core.ocr.base import OCREngine, OCRResult


class MyOCREngine:
    def recognize(self, image: bytes, lang: str = "en") -> OCRResult:
        # Your OCR logic
        return OCRResult(text="recognized text", confidence=0.95, lang=lang)

    def available_languages(self) -> list[str]:
        return ["en", "ja", "ko", "zh"]

    @property
    def name(self) -> str:
        return "My OCR Engine"
```

## Security Checklist for New Engines

Before submitting a PR:

- [ ] `allowed_endpoints` accurately lists ALL domains the engine communicates with
- [ ] No use of `verify=False` in HTTP requests
- [ ] API keys are never logged (use masking: `key[:4] + "..." + key[-4:]`)
- [ ] No disk writes of captured images or OCR text
- [ ] Unit tests cover the Protocol interface
- [ ] License of any new dependency is MIT-compatible (check with `pip-licenses`)
