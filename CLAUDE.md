# CLAUDE.md — grabtl

## プロジェクト概要

ゲーム内チャットをドラッグ選択で日本語に翻訳するデスクトップアプリ。
日本人ゲーマーが海外サーバーでコミュニケーションするためのツール。

**差別化ポイント:**
- 固定領域の自動翻訳ではなく「都度ドラッグ」のオンデマンドモデル
- 読むだけでなく返信翻訳（日→英）も支援する双方向チャットツール
- APIキー不要で即使えるローカル完結モード（Tier 0）

## 技術スタック

| レイヤー | 技術 | 理由 |
|---------|------|------|
| 言語 | Python 3.11+ | OCR/ML/翻訳のエコシステム |
| OCR | winocr (Windows OCR API) | 追加インストール不要 |
| 翻訳 (Tier 0) | argostranslate | オフライン・APIキー不要・MIT |
| 翻訳 (Tier 1) | Ollama REST API | ローカルLLM・通信ゼロ |
| 翻訳 (Tier 2) | DeepL / Claude / Gemini API | 最高品質・BYOK |
| キャプチャ | mss + Pillow | 軽量・高速 |
| GUI | **PySide6** (LGPL v3) | ※PyQt6(GPL)は不可。企業採用のため |
| APIキー保存 | keyring (Windows DPAPI) | OS標準の暗号化 |
| ビルド | Nuitka (--onedir) | AV誤検知軽減 |
| テスト | pytest + ruff + mypy | PR ごとに CI で実行 |

## コーディング規約

- フォーマッター: `ruff format`
- リンター: `ruff check`
- 型チェック: `mypy --strict`
- docstring: Google スタイル（パブリック API は英語、内部は日本語可）
- テスト: pytest。`core/` のカバレッジ 80% 以上を目標
- コミットメッセージ: Conventional Commits（`feat:` / `fix:` / `docs:` / `refactor:`）

## 絶対に守るルール

1. **`core/` から PySide6 を import してはならない** — `core/` は GUI 非依存の純粋な Python ライブラリ
2. **`requests` で `verify=False` は絶対禁止** — TLS 証明書検証を常に有効にする
3. **新しい外部通信先を追加する場合は `allowed_endpoints` に登録必須** — CI で未登録ドメインへの通信を検出したら fail
4. **OCR / 翻訳エンジンは Protocol で定義** — `core/ocr/base.py` と `core/translation/base.py` の Protocol を実装する
5. **設定は `core/` では dict / dataclass で受け取る** — GUI 層が QSettings ↔ dict 変換を担当
6. **キャプチャ画像はメモリ上でのみ処理** — ディスクに保存しない
7. **APIキーは `keyring` で保存** — 設定ファイルに平文で保存しない。ログ出力時はマスク表示（`sk-...xxxx`）
8. **Ollama 接続先は `127.0.0.1` にハードコード** — `0.0.0.0` にしない
9. **DirectX フック等のゲームプロセス介入機能は実装しない**
10. **PyQt6 ではなく PySide6 を使用** — ライセンス互換性のため（GPL vs LGPL）

## 関連ドキュメント

- 設計・アーキテクチャ: [docs/architecture.md](docs/architecture.md)
- セキュリティ設計: [docs/security-design.md](docs/security-design.md)
- ロードマップ・開発フェーズ: [docs/roadmap.md](docs/roadmap.md)
- リリース・CI/CD: [docs/release.md](docs/release.md)
- コントリビュートガイド: [CONTRIBUTING.md](CONTRIBUTING.md)
