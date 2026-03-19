# 🎮 grabtl

> **掴んで、翻訳して、遊ぼう。** — 画面上のテキストをドラッグで翻訳。プライバシー重視、オフライン対応。

🇬🇧 [English README](README.md)

## これは何？

ゲーム画面上のチャットをドラッグで範囲選択して翻訳するデスクトップツールです。既存ツール（RSTGameTranslation, Translumo 等）が固定領域を自動翻訳するのに対し、このツールは**必要なときに必要な部分だけ**を翻訳します。

**既存ツールとの違い:**
- 固定領域ではなく**都度ドラッグで翻訳**
- 読むだけでなく**返信の翻訳（日→英）も支援**
- **APIキー不要**でそのまま使える（オフライン翻訳同梱）
- **日本語ファースト**の UI とドキュメント

## クイックスタート（ライブラリとして）

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

## インストール

### デスクトップアプリ（一般ユーザー向け）
[GitHub Releases](https://github.com/<owner>/grabtl/releases) からインストーラーをダウンロード。

### Python ライブラリとして
```bash
# コアのみ（GUI なし）
pip install grabtl[ocr-windows,translate-local]

# フルインストール（GUI 含む）
pip install grabtl[all]
```

## 翻訳モード

| モード | APIキー | 通信 | 品質 | セットアップ |
|--------|---------|------|------|------------|
| **Tier 0: ローカル**（デフォルト）| 不要 | なし | ★★★ | 設定不要 |
| **Tier 1: Ollama** | 不要 | localhost のみ | ★★★★ | Ollama をインストール |
| **Tier 2: クラウドAPI** | あなたのキー | HTTPS | ★★★★★ | APIキー入力 |

## セキュリティ

**「完璧なセキュリティ」ではなく「誠実な透明性」** を方針としています。詳細は [docs/security-design.md](docs/security-design.md) をご覧ください。

**ポイント:**
- APIキーは Windows 標準の暗号化（DPAPI）で保存。VS Code や Chrome と同じ方式です
- 通信ログで、翻訳サービスに送信されるデータを確認できます
- Tier 0 モードではネットワーク通信もAPIキーも一切不要です

### APIキーの保護について（正直な説明）

APIキーは Windows Credential Manager（DPAPI）で暗号化保存されます。これは VS Code が拡張機能のシークレットを保存するのと同じ方式です。

ただし、同じ Windows ユーザーで動作する他のプロセスからは理論上アクセス可能です。これは Windows の設計仕様であり、VS Code でも同じ制約があります（[詳細](docs/security-design.md#known-limitations-we-are-transparent-about-these)）。

リスクを最小化するため、以下を推奨します:
- **DeepL API Free**（無料枠）を使えば、漏洩しても金銭的被害がありません
- 有料 API は**利用上限を設定**してください
- 心配な場合は **Tier 0（完全ローカル）** でお使いください

## エンジンの追加

プラグインアーキテクチャを採用しています。OCR や翻訳エンジンの追加方法は [docs/plugin-guide.md](docs/plugin-guide.md) をご覧ください。

## 免責事項

本ツールはスクリーンキャプチャのみで動作し、ゲームプロセスには一切介入しません。ただし、本ツールの使用が各ゲームの利用規約に違反しないか、ユーザー自身の責任で確認してください。

## コントリビュート

[CONTRIBUTING.md](CONTRIBUTING.md) をご覧ください。Issue や Discussion は日本語・英語どちらでも歓迎です。

## ライセンス

[MIT License](LICENSE)

サードパーティライセンスは [NOTICE](NOTICE) に記載しています。
