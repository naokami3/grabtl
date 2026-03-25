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
│       │   │   └── winocr_engine.py  # Windows OCR 実装（小画像自動拡大付き）
│       │   ├── translation/
│       │   │   ├── __init__.py
│       │   │   ├── base.py          # Translator Protocol
│       │   │   ├── engines.py       # EngineType (StrEnum: argos/ollama/deepl/chatgpt/gemini)
│       │   │   ├── exceptions.py   # 共通例外 (ConnectionFailedError, ServerError 等)
│       │   │   ├── _http.py        # 共通 HTTP クライアント (requests Session)
│       │   │   ├── _llm_utils.py   # LLM 共通 (clean_response, LANG_MAP, SYSTEM_PROMPT)
│       │   │   ├── argos.py         # argostranslate 実装 (Tier 0)
│       │   │   ├── ollama.py        # Ollama REST API 実装 (Tier 1)
│       │   │   ├── deepl.py         # DeepL API 実装 (Tier 2a)
│       │   │   ├── chatgpt.py       # ChatGPT API 実装 (Tier 2b)
│       │   │   ├── gemini.py        # Gemini API 実装 (Tier 2c)
│       │   │   ├── ct2_translator.py # CTranslate2 直接実行 (torch 不要)
│       │   │   ├── cache.py         # 翻訳キャッシュ (CachedTranslator デコレータ)
│       │   │   └── _dll_fix.py      # Windows DLL 競合回避 (レガシー)
│       │   ├── capture/
│       │   │   ├── __init__.py
│       │   │   └── screen.py        # mss スクリーンキャプチャ
│       │   ├── glossary/
│       │   │   ├── __init__.py
│       │   │   ├── manager.py       # ゲーム用語辞書 (Glossary, GlossaryEntry)
│       │   │   └── decorator.py     # GlossaryTranslator (Translator デコレータ)
│       │   ├── security/
│       │   │   ├── __init__.py
│       │   │   └── keystore.py      # APIキー保存 (keyring wrapper)
│       │   └── pipeline.py          # OCR → 翻訳パイプライン
│       │
│       ├── gui/                     # PySide6 デスクトップアプリ
│       │   ├── __init__.py
│       │   ├── main_window.py       # エントリポイント + システムトレイ + ホットキー
│       │   ├── overlay.py           # 翻訳結果フローティング表示
│       │   ├── region_selector.py   # ドラッグ範囲選択（透過オーバーレイ）
│       │   └── settings_dialog.py   # 設定画面（翻訳エンジン切替）
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
│   │   ├── test_glossary.py
│   │   ├── test_ollama.py
│   │   ├── test_deepl.py
│   │   ├── test_chatgpt.py
│   │   ├── test_gemini.py
│   │   ├── test_ct2_translator.py
│   │   ├── test_cache.py
│   │   └── test_capture.py
│   └── integration/                 # Windows 実機テスト（CI ではスキップ）
│       ├── test_winocr_engine.py    # ゲームチャット風画像の OCR テスト
│       ├── test_pipeline_e2e.py     # OCR → 翻訳フルパイプライン
│       └── test_dll_fix.py          # DLL 競合回避の動作確認
│
├── docs/
│   ├── architecture.md              # このファイル
│   ├── security-design.md           # セキュリティ設計書
│   ├── roadmap.md                   # ロードマップ・開発フェーズ
│   ├── release.md                   # リリース・CI/CD
│   └── adr/                         # Architecture Decision Records
│       ├── 0001-tier0-translation-engine.md
│       ├── 0002-translation-engine-tiers.md
│       ├── 0003-http-client-requests.md
│       └── 0004-ct2-direct-translation.md
│
├── assets/
│   └── grabtl.ico                   # アプリアイコン (16/32/48/256px)
│
├── build_entry.py                   # Nuitka ビルド用ランチャー
├── build.py                         # ビルドスクリプト（Nuitka + モデルコピー）
├── installer.iss                    # Inno Setup インストーラー定義
│
└── .claude/
    └── settings.json                # Claude Code hooks（コミット前チェック）
```

## 設計原則

- **`core/` は PySide6 に一切依存しない。** 純粋な Python ライブラリとして `pip install` で単独利用可能
- **OCR / 翻訳エンジンは Protocol (`typing.Protocol`) で定義。** 外部から差し替え可能
- **設定は `core/` では dict / dataclass で受け取る。** GUI 層が QSettings ↔ dict 変換を担当
- **Glossary はデコレータパターン。** Pipeline を変更せず、Translator をラップして用語辞書を適用

## Protocol インターフェース

```python
# core/ocr/base.py
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

## 翻訳エンジンの Tier 構成

ADR-0002 で決定。ユーザーは設定画面で選ぶだけ。

| Tier | 表示名 | エンジン | 要件 | 状態 |
|------|--------|---------|------|------|
| 0 | 機械翻訳 | Opus-MT + Glossary | なし（即使える） | ✅ 実装済み |
| 1 | AI翻訳 | Ollama + Qwen 2.5 3B | Ollama インストール | ✅ 実装済み |
| 2a | DeepL | DeepL API | APIキー | 未実装 |
| 2b | ChatGPT | OpenAI API | APIキー | 未実装 |
| 2c | Gemini | Google Gemini API | APIキー | 未実装 |

### ゲーム用語辞書（Glossary）

全 Tier で共通に適用される前後処理:
- **PRE_REPLACE**: 略語を翻訳前に完全置換（GG → お疲れ様, LFG → メンバー募集）
- **POST_REPLACE**: ゲーム用語を翻訳後に上書き（raid → レイド, dungeon → ダンジョン）

GlossaryTranslator デコレータで Translator をラップするため、Pipeline の変更は不要。

## GUI アーキテクチャ

### 操作フロー

1. アプリ起動 → システムトレイに常駐（多重起動防止: Windows Named Mutex）
2. Ctrl+Shift+G → 全画面透過オーバーレイ → ドラッグで領域選択
3. キャプチャ → OCR → 翻訳（バックグラウンド QThread）
4. 段階的表示: OCR 結果を先に表示 → 翻訳結果で更新
5. オーバーレイ外クリックで結果を消去

### グローバルホットキー

Win32 `RegisterHotKey` API + `QAbstractNativeEventFilter` で実装。
PySide6 の `QShortcut` はフォーカスが必要なため使用不可。

### DPI スケーリング

RegionSelector は論理座標と物理ピクセル座標を分離して emit。
`QScreen.devicePixelRatio()` で変換し、`mss` には物理座標を渡す。

## Windows DLL 競合の制約

winrt パッケージ（winocr が依存）と torch（argostranslate → ctranslate2 が依存）は、
それぞれ異なるバージョンの `msvcp140.dll` を使用する。
Windows では同名 DLL はプロセス内で先にロードされた方が使われるため、
winocr を先にインポートすると torch の `c10.dll` 初期化が失敗する（WinError 1114）。

**対策:** `core/translation/_dll_fix.py` の `preload_system_vcrt()` で、
システム版の VC ランタイムを先制ロードしている。

**新しいエントリポイント（GUI 等）を追加する際の注意:**
- `main()` 関数の最初で `preload_system_vcrt()` を呼ぶこと
- winocr や WinRT 関連の import より前に実行する必要がある

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

## ADR（Architecture Decision Records）

技術的な意思決定の記録は `docs/adr/` に保存:

- [ADR-0001: Tier 0 翻訳エンジンの選定](adr/0001-tier0-translation-engine.md) — NLLB/FuguMT/Sugoi を評価し Opus-MT + Glossary を採用
- [ADR-0002: 翻訳エンジンの Tier 構成](adr/0002-translation-engine-tiers.md) — Tier 0/1/2 の構成とモデル選定
- [ADR-0003: HTTP クライアントに requests を採用](adr/0003-http-client-requests.md) — urllib.request 廃止、linter 警告への構造的対処
- [ADR-0004: CTranslate2 直接利用による torch 排除](adr/0004-ct2-direct-translation.md) — メモリ 200-500MB 削減、DLL 競合解消
