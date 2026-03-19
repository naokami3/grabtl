# CLAUDE.md — grabtl

## プロジェクト概要

ゲーム内チャットをドラッグ選択で日本語に翻訳するデスクトップアプリ。
日本人ゲーマーが海外サーバーでコミュニケーションするためのツール。

**既存ツール（RSTGameTranslation, Translumo 等）との差別化:**
- 「固定領域の自動翻訳」ではなく「都度ドラッグで翻訳」するオンデマンドモデル
- 読むだけでなく返信翻訳（日→英）も支援する双方向チャットツール
- 日本語ファーストの UI / ドキュメント
- APIキー不要で即使えるローカル完結モード（Tier 0）

## 技術スタック

| レイヤー | 技術 | 理由 |
|---------|------|------|
| 言語 | Python 3.11+ | OCR/ML/翻訳のエコシステム |
| OCR | winocr (Windows OCR API) | 追加インストール不要。日本語PCなら英日OCRがプリインストール済み |
| 翻訳 (Tier 0) | argostranslate | オフライン・APIキー不要・MIT |
| 翻訳 (Tier 1) | Ollama REST API | ローカルLLM・通信ゼロ・高品質 |
| 翻訳 (Tier 2) | DeepL / Claude / Gemini API | 最高品質・BYOK |
| キャプチャ | mss + Pillow | 軽量・高速 |
| GUI | **PySide6** (LGPL v3) | ※PyQt6(GPL)は不可。企業採用のため |
| APIキー保存 | keyring (Windows Credential Manager / DPAPI) | OS標準の暗号化。VS Codeと同じ方式 |
| ビルド | Nuitka (--onedir) | AV誤検知軽減。PyInstaller --onefileは避ける |
| インストーラー | Inno Setup | 正規ソフト感・アンインストーラー自動生成 |
| テスト | pytest + ruff + mypy | PR ごとに CI で実行 |

## アーキテクチャ

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
├── docs/
│   ├── security-design.md           # セキュリティ設計書（公開用）
│   └── plugin-guide.md             # プラグイン作成ガイド
│
├── CLAUDE.md                        # このファイル
├── LICENSE                          # MIT
├── README.md                        # 英語
├── README.ja.md                     # 日本語
├── SECURITY.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
├── NOTICE                           # 依存ライブラリのライセンス表記
└── pyproject.toml
```

**設計原則:**
- `core/` は PySide6 に一切依存しない。純粋な Python ライブラリとして単独利用可能
- OCR / 翻訳エンジンは Protocol (typing.Protocol) で定義。外部から差し替え可能
- 設定は `core/` では dict / dataclass で受け取り、GUI 層が QSettings ↔ dict 変換を担当

## ライセンス

**プロジェクト: MIT License**

PyQt6 ではなく PySide6 を選定した理由:
- PyQt6 は GPL v3 → プロジェクト全体が GPL に縛られ、企業の独自改変を非公開にできない
- PySide6 は LGPL v3 → MIT との互換性あり。企業の法務審査を通りやすい
- API は PyQt6 と 99% 同一で移行コストが極めて低い

依存ライブラリのライセンス互換性（すべて MIT 互換を確認済み）:
- PySide6: LGPL v3（動的リンクなので問題なし）
- winocr: MIT
- argostranslate: MIT / CC0
- mss: MIT
- Pillow: HPND
- keyring: MIT
- requests: Apache 2.0
- Nuitka: Apache 2.0（ビルドツール）

## セキュリティ方針

### 基本姿勢
**「完璧なセキュリティ」ではなく「誠実な透明性」で信頼を獲得する。**

Bitwarden（ホワイトペーパー公開）と VS Code（SecretStorage API）の事例から導いた方針。
VS Code ですら拡張機能間のシークレット隔離は完全ではなく、OS 標準暗号化に依存している。

### APIキー保存
- `keyring` ライブラリ（内部的に Windows DPAPI）で保存
- 設定ファイル（JSON等）に平文で保存しない
- **既知の限界を正直に説明する:**
  - 同じ Windows ユーザーで動作する他プロセスからは理論上読み取り可能（MITRE ATT&CK T1555.004）
  - Python はイミュータブル文字列のため、メモリの確実なゼロクリアが不可能
- **リスク最小化のアプローチ:**
  - DeepL API Free（無料枠）の利用を推奨（漏洩しても金銭被害なし）
  - LLM API は usage limit 付きキーの発行を案内
  - 各 API プロバイダーのキーローテーション手順へのリンクを設定画面に配置

### 通信の透明性
- 各 Translator 実装に `allowed_endpoints: list[str]` を定義
- CI テストで許可リスト外ドメインへの通信を検出したら fail
- GUI に通信ログタブ（送信先URL・OCRテキスト・翻訳結果・タイムスタンプ）
- APIキーはログ上でマスク表示（`sk-...xxxx`）
- `requests` の `verify=False` は絶対禁止（lint ルールにも追加）

### Ollama 連携の注意点
- Ollama はデフォルトで `0.0.0.0:11434` にバインドする場合がある
- アプリ側の接続先は `127.0.0.1` にハードコード
- ドキュメントに `OLLAMA_HOST=127.0.0.1:11434` の設定を推奨と明記

### スクリーンキャプチャのプライバシー
- キャプチャ画像はメモリ上でのみ処理。ディスクに保存しない
- Tier 2（クラウドAPI）使用時は「選択範囲の内容が翻訳サービスに送信されます」と初回確認
- OCR 結果のプレビュー表示オプション

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

## AV 誤検知対策

PyInstaller --onefile は使わない（誤検知率最高）。

**初期（v0.x）:** Nuitka --onedir + Inno Setup + 毎リリース Microsoft 誤検知報告 + VirusTotal 結果添付
**成長期（v1.x）:** Certum Open Source コード署名証明書（年€69）
**安定期:** EV 証明書・Microsoft Store（MSIX）検討

注意: Nuitka が PyInstaller より必ず誤検知が少ないとは限らない（矛盾する報告あり）。
--onedir + インストーラー + コード署名 が根本的解決策。

## OSS ガバナンス

### v0.1.0 までに必須
- LICENSE (MIT)
- README.md (英語) + README.ja.md (日本語)
- SECURITY.md（脆弱性報告: GitHub Private Vulnerability Reporting, 48時間確認目標）
- CONTRIBUTING.md（開発環境セットアップ、コーディング規約、PRチェックリスト）
- NOTICE（依存ライブラリライセンス一覧）
- docs/security-design.md（セキュリティ設計書）

### v0.2.0 までに整備
- CODE_OF_CONDUCT.md（Contributor Covenant）
- CHANGELOG.md（Keep a Changelog 形式、SemVer 準拠）
- .github/ISSUE_TEMPLATE/（バグ報告・機能要望）
- .github/PULL_REQUEST_TEMPLATE.md

### v1.0.0 までに整備
- docs/plugin-guide.md（OCR/翻訳エンジンの追加方法）

## CI/CD

### PR ごと
- `ruff check` + `ruff format --check`
- `mypy --strict src/`
- `pytest tests/unit/`
- 通信先テスト: テスト中に許可リスト外ドメインへ通信したら fail

### 週次
- `pip-audit`（依存パッケージの脆弱性スキャン）
- `pip-licenses`（ライセンス互換性チェック）

### リリース時（タグ push）
- Nuitka ビルド → Inno Setup → GitHub Releases に自動アップロード
- SHA256 ハッシュをリリースノートに記載
- VirusTotal API スキャン結果を添付

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

## コーディング規約

- フォーマッター: ruff format
- リンター: ruff check
- 型チェック: mypy --strict
- docstring: Google スタイル（日本語可だが、パブリック API は英語）
- テスト: pytest。core/ のカバレッジ 80% 以上を目標
- コミットメッセージ: Conventional Commits（feat: / fix: / docs: / refactor:）
- `requests` で `verify=False` は絶対禁止
- `core/` から PySide6 を import してはならない
- 新しい外部通信先を追加する場合は `allowed_endpoints` に登録必須

## ゲーム規約に関する免責事項

README に以下を記載:
「本ツールはスクリーンキャプチャのみで動作し、ゲームプロセスには一切介入しません。
ただし、本ツールの使用が各ゲームの利用規約に違反しないか、ユーザー自身の責任で確認してください。」

DirectX フック等のゲームプロセス介入機能は実装しない方針。

## 開発フェーズ

### Phase 1: PoC (1-2日)
Python + mss + winocr + argostranslate でコンソールアプリ。GUI なし。

### Phase 2: ドラッグ選択 (3-5日)
PySide6 透過オーバーレイ + マウスドラッグ範囲選択 → OCR → 翻訳。

### Phase 3: オーバーレイ表示 (3-5日)
翻訳結果を透過ウィンドウ表示。クリックスルー。ホットキー。

### Phase 4: 設定・品質改善 (1-2週間)
翻訳エンジン切替（Tier 0/1/2）、APIキー管理、通信ログ、翻訳履歴、用語辞書。
Nuitka ビルド + Inno Setup。

## パッケージ構成

```toml
# pyproject.toml
[project]
name = "grabtl"
dependencies = [
    "mss",
    "Pillow",
    "keyring",
]

[project.optional-dependencies]
ocr-windows = ["winocr"]
translate-local = ["argostranslate"]
translate-cloud = ["requests"]
gui = ["PySide6"]
all = ["grabtl[ocr-windows,translate-local,translate-cloud,gui]"]
```

他社がコアだけ使う場合: `pip install grabtl[ocr-windows,translate-local]`
フルインストール: `pip install grabtl[all]`

## バージョニング

Semantic Versioning (MAJOR.MINOR.PATCH)
- 0.x.x: 初期開発フェーズ。API 破壊変更あり得る
- 1.0.0: Protocol インターフェースの安定を宣言
- Protocol インターフェースの変更は MAJOR バージョンアップ

## README の冒頭に載せるコード例

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
