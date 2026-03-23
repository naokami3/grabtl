# CLAUDE.md — grabtl

ゲーム内チャットをドラッグ選択で翻訳する Windows デスクトップアプリ。
Python 3.11+ / winocr / argostranslate / PySide6。

## コマンド

- `ruff format src/ tests/` — フォーマット
- `ruff check src/ tests/` — リント
- `mypy src/` — 型チェック（pyproject.toml に strict 設定済み）
- `pytest tests/ -v` — テスト実行（unit + integration）
- `pip install -e ".[all,dev]"` — 開発環境セットアップ

## コーディング規約

- docstring: Google スタイル（パブリック API は英語、内部は日本語可）
- テスト: `core/` のカバレッジ 80% 以上を目標
- コミットメッセージ: Conventional Commits（`feat:` / `fix:` / `docs:` / `refactor:`）

## 絶対に守るルール

1. **`core/` から PySide6 を import してはならない** — GUI 非依存の純粋な Python ライブラリ
2. **`requests` で `verify=False` は絶対禁止**
3. **新しい外部通信先は `allowed_endpoints` に登録必須**
4. **OCR / 翻訳エンジンは Protocol で定義** — `core/ocr/base.py` / `core/translation/base.py`
5. **設定は `core/` では dict / dataclass で受け取る** — GUI 層が QSettings ↔ dict 変換を担当
6. **キャプチャ画像はメモリ上でのみ処理** — ディスクに保存しない
7. **APIキーは `keyring` で保存** — 平文保存禁止、ログ出力時はマスク（`sk-...xxxx`）
8. **Ollama 接続先は `127.0.0.1` にハードコード** — `0.0.0.0` にしない
9. **DirectX フック等のゲームプロセス介入機能は実装しない**
10. **PyQt6 ではなく PySide6 を使用** — ライセンス互換性のため（GPL vs LGPL）

## 既知の落とし穴

- **WinRT/torch DLL 競合**: winocr と argostranslate を同一プロセスで使う場合、エントリポイントの最初に `preload_system_vcrt()` を呼ぶ必要がある。詳細は `core/translation/_dll_fix.py` と [docs/architecture.md](docs/architecture.md) を参照
- **Windows OCR 言語パック**: winocr は OS レベルの OCR 言語パックに依存。英語 OCR が未インストールの場合がある

## 関連ドキュメント

- 設計・アーキテクチャ: [docs/architecture.md](docs/architecture.md)
- セキュリティ設計: [docs/security-design.md](docs/security-design.md)
- ロードマップ: [docs/roadmap.md](docs/roadmap.md)
- リリース・CI/CD: [docs/release.md](docs/release.md)
- コントリビュートガイド: [CONTRIBUTING.md](CONTRIBUTING.md)
