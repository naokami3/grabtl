# 🎮 grabtl

> **Grab. Translate. Play.** — Drag-to-translate tool for on-screen text. Privacy-focused, works offline.

🇯🇵 [日本語版 README はこちら](README.ja.md)

## What is this?

A desktop tool for translating in-game chat and quest text by dragging to select text areas on screen. Unlike existing tools (RSTGameTranslation, Translumo) that auto-translate a fixed region, this tool lets you **translate on demand** — select exactly what you want, when you want.

**Key differences from existing tools:**
- **On-demand drag-to-translate** instead of fixed-region auto-capture
- **Works without API keys** — fully offline translation out of the box
- **Game glossary** auto-corrects terms (GG → お疲れ様, raid → レイド)
- **Japanese-first** UI and documentation

## Usage

### 1. Install

Download `grabtl-0.1.0-setup.exe` from [GitHub Releases](https://github.com/naokami3/grabtl/releases). No admin privileges required.

### 2. Translate

1. Launch grabtl — a blue "G" icon appears in the system tray
2. Press **Ctrl+Shift+G** to activate translation mode (screen dims)
3. **Drag to select** the text you want to translate
4. OCR + translation results appear near the selection
5. Click outside the result to dismiss

### 3. Change Settings

Right-click the tray icon → **"Settings..."** to change translation engine or hotkey.

## Translation Engines

| Engine | Description | Setup |
|--------|-------------|-------|
| **Machine Translation** (default) | Offline. No API key needed | None |
| **AI Translation (Ollama)** | High-quality local AI | Install [Ollama](https://ollama.com) |
| **DeepL API** | Best translation quality | Enter [DeepL](https://www.deepl.com) API key |
| **ChatGPT API** | OpenAI translation | Enter [OpenAI](https://platform.openai.com) API key |
| **Gemini API** | Google translation | Enter [Google AI Studio](https://aistudio.google.com) API key |

### Setting Up AI Translation (Ollama)

1. Install Ollama from [ollama.com](https://ollama.com/download)
2. Run `ollama pull qwen2.5:3b` in terminal (~2GB download)
3. In grabtl settings → select "AI Translation (Ollama)" → test connection

### Setting Up API Translation

1. In grabtl settings → select your preferred engine
2. Click "Open Console" to get an API key
3. Enter the key → "Test and Save"

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Ctrl+Shift+G** | Start translation mode (customizable in settings) |
| **Esc** | Cancel selection / dismiss result |
| Right-click | Cancel selection |

Hotkey can be changed in tray icon → Settings (Ctrl+Shift+T, Ctrl+Alt+T, F9, F10, etc.).

## System Requirements

- Windows 10 / 11 (64-bit)
- Games should run in **borderless windowed mode** (exclusive fullscreen is not supported)

## Security

- API keys are stored using OS-native encryption (Windows DPAPI) — same method as VS Code and Chrome
- Machine Translation mode has zero network traffic and zero API keys
- See [docs/security-design.md](docs/security-design.md) for details

## Disclaimer

This tool operates solely via screen capture and does not interact with game processes in any way. However, users are responsible for verifying that the use of this tool complies with the terms of service of their specific game.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and discussions in Japanese or English are welcome.

## License

[MIT License](LICENSE)

Third-party licenses are listed in [NOTICE](NOTICE).
