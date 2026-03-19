# Architecture — grabtl

## ディレクトリ構造

```
grabtl/
├── src/
│   └── grabtl/
│       ├── core/                    # ← pip install 可能なライブラリ。PySide6に依存しない
│       │   ├── __init__.py
│       │   ├── ocr/
│       │   │   ├── __init__.py
│       │   │   ├── base.py          # OCREngine Protocol
│       │   │   └── winocr_engine.py  # Windows OCR 実装
│       │   ├── translation/
│       │   │   ├── __init__.py
│       │   │   ├── base.py          # Translator Protocol
│       │   │   ├── argos.py         # argostranslate 実装
│       │   │   ├── ollama.py        # Ollama 実装
│       │   │   └── deepl.py         # DeepL API 実装
│       │   ├── capture/
│       │   │   ├── __init__.py
│       │   │   └── screen.py        # mss スクリーンキャプチャ
│       │   ├── glossary/
│       │   │   ├── __init__.py
│       │   │   └── manager.py       # ゲーム用語辞書
│       │   ├── security/
│       │   │   ├── __init__.py
│       │   │   └── keystore.py      # APIキー保存（keyring wrapper）
│       │   └── pipeline.py          # OCR → 辞書適用 → 翻訳 パイプライン
│       │
│       ├── gui/                     # PySide6 デスクトップアプリ
│       │   ├── __init__.py
│       │   ├── main_window.py
│       │   ├── overlay.py           # 透過オーバーレイ（翻訳結果表示）
│       │   ├── region_selector.py   # ドラッグ範囲選択
│       │   ├── settings_dialog.py   # 設定画面（翻訳エンジン切替・APIキー・通信ログ）
│       │   └── resources/
│       │       └── i18n/            # Qt .ts 翻訳ファイル
│       │
│       └── cli/                     # CLI ツール（GUI不要で利用可能）
│           ├── __init__.py
│           └── main.py
│
├── tests/
│   ├── unit/
│   │   ├── test_ocr.py
│   │   ├── test_translation.py
│   │   ├── test_pipeline.py
│   │   └── test_keystore.py
│   └── integration/
│       └── test_network_isolation.py  # 許可外ドメインへの通信を検出するテスト
│
└── docs/
    ├── architecture.md              # このファイル
    ├── security-design.md           # セキュリティ設計書
    ├── plugin-guide.md              # プラグイン作成ガイド
    ├── roadmap.md                   # ロードマップ・開発フェーズ
    └── release.md                   # リリース・CI/CD
```

## 設計原則

- **`core/` は PySide6 に一切依存しない。** 純粋な Python ライブラリとして `pip install` で単独利用可能
- **OCR / 翻訳エンジンは Protocol (`typing.Protocol`) で定義。** 外部から差し替え可能
- **設定は `core/` では dict / dataclass で受け取る。** GUI 層が QSettings ↔ dict 変換を担当

## Protocol インターフェース

```python
# core/ocr/base.py
from typing import Protocol
from dataclasses import dataclass

@dataclass
class OCRResult:
    text: str
    confidence: float
    lang: str
    bounding_boxes: list[dict] | None = None

class OCREngine(Protocol):
    def recognize(self, image: bytes, lang: str = "en") -> OCRResult: ...
    def available_languages(self) -> list[str]: ...
    @property
    def name(self) -> str: ...

# core/translation/base.py
class Translator(Protocol):
    def translate(self, text: str, source: str, target: str) -> str: ...
    @property
    def requires_api_key(self) -> bool: ...
    @property
    def is_local(self) -> bool: ...
    @property
    def allowed_endpoints(self) -> list[str]: ...
```

## 利用モードの3段階設計

### Tier 0: 完全ローカル（APIキー不要・通信ゼロ）— 初期体験
- OCR: winocr（Windows 標準 OCR）
- 翻訳: argostranslate（オフライン。モデル約30MBをインストーラーに同梱）
- 起動 → ドラッグ → 翻訳が出る。設定画面を開く必要なし

### Tier 1: ローカル LLM（Ollama 連携・通信ゼロ）— 中級者
- 翻訳: Ollama + gemma3-translator:4b 等
- 設定画面で「Ollama を使う」を ON にするだけ
- Ollama インストールガイドとモデルプルコマンドをワンクリックコピー

### Tier 2: クラウド API（BYOK・最高品質）— 上級者
- DeepL / Claude / GPT / Gemini をユーザー自身の APIキーで利用
- keyring で暗号化保存。セキュリティ説明を表示

## パッケージ構成

コアのみ利用:
```bash
pip install grabtl[ocr-windows,translate-local]
```

フルインストール:
```bash
pip install grabtl[all]
```

詳細は [pyproject.toml](../pyproject.toml) を参照。

## ライセンス互換性

プロジェクトは MIT License。すべての依存ライブラリは MIT 互換を確認済み。

| ライブラリ | ライセンス | 備考 |
|-----------|----------|------|
| PySide6 | LGPL v3 | 動的リンクなので問題なし |
| winocr | MIT | |
| argostranslate | MIT / CC0 | |
| mss | MIT | |
| Pillow | HPND | |
| keyring | MIT | |
| requests | Apache 2.0 | |
| Nuitka | Apache 2.0 | ビルドツール |

PyQt6 ではなく PySide6 を選定した理由:
- PyQt6 は GPL v3 → プロジェクト全体が GPL に縛られ、企業の独自改変を非公開にできない
- PySide6 は LGPL v3 → MIT との互換性あり。企業の法務審査を通りやすい
- API は PyQt6 と 99% 同一で移行コストが極めて低い
