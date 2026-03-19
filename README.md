# 🎮 grabtl

> **Grab. Translate. Play.** — Drag-to-translate tool for on-screen text. Privacy-focused, works offline.

🇯🇵 [日本語版 README はこちら](README.ja.md)

## What is this?

A desktop tool for translating in-game chat by dragging to select text areas on screen. Unlike existing tools (RSTGameTranslation, Translumo) that auto-translate a fixed region, this tool lets you **translate on demand** — select exactly what you want, when you want.

**Key differences from existing tools:**
- **On-demand drag-to-translate** instead of fixed-region auto-capture
- **Bidirectional chat support** — not just reading, but also composing replies
- **Works without API keys** — fully offline translation out of the box
- **Japanese-first** UI and documentation

## Quick Start (as a library)

```python
from grabtl.core.ocr.winocr_engine import WinOCREngine
from grabtl.core.translation.argos import ArgosTranslator
from grabtl.core.pipeline import TranslationPipeline

pipeline = TranslationPipeline(
    ocr=WinOCREngine(),
    translator=ArgosTranslator(source="en", target="ja"),
)

result = pipeline.translate_image(screenshot_bytes)
print(result.translated_text)  # "レイド メンバー募集中"
```

## Installation

### Desktop App (recommended for end users)
Download the installer from [GitHub Releases](https://github.com/<owner>/grabtl/releases).

### As a Python library
```bash
# Core only (no GUI)
pip install grabtl[ocr-windows,translate-local]

# Full install with GUI
pip install grabtl[all]
```

## Translation Modes

| Mode | API Key | Network | Quality | Setup |
|------|---------|---------|---------|-------|
| **Tier 0: Local** (default) | Not required | None | ★★★ | Zero config |
| **Tier 1: Ollama** | Not required | localhost | ★★★★ | Install Ollama |
| **Tier 2: Cloud API** | Your own key | HTTPS | ★★★★★ | Enter API key |

## Security

We follow the principle of **transparent security**. See [docs/security-design.md](docs/security-design.md) for our full security architecture, including known limitations.

**Key points:**
- API keys are stored using OS-native encryption (Windows DPAPI) — same method as VS Code and Chrome
- Communication log lets you inspect exactly what data is sent to translation providers
- Tier 0 mode has zero network traffic and zero API keys

## Adding New Engines

grabtl uses a plugin architecture. See [docs/plugin-guide.md](docs/plugin-guide.md) for how to add OCR or translation engines.

## Disclaimer

This tool operates solely via screen capture and does not interact with game processes in any way. However, users are responsible for verifying that the use of this tool complies with the terms of service of their specific game.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and discussions in Japanese or English are welcome.

## License

[MIT License](LICENSE)

Third-party licenses are listed in [NOTICE](NOTICE).
