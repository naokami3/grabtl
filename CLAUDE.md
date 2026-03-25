# CLAUDE.md — grabtl

ゲーム内チャットをドラッグ選択で翻訳する Windows デスクトップアプリ。
Python 3.11+ / winocr / CTranslate2 / Ollama / PySide6。

## コマンド

- `ruff format src/ tests/` — フォーマット
- `ruff check src/ tests/` — リント
- `mypy src/` — 型チェック（pyproject.toml に strict 設定済み）
- `pytest tests/ -v` — テスト実行（unit + integration）
- `pip install -e ".[all,dev]"` — 開発環境セットアップ
- `python -m grabtl.gui.main_window` — GUI 起動
- `python build.py` — Nuitka ビルド（exe + モデル同梱）

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
7. **APIキーは `core/security/keystore.py` 経由で保存** — 平文保存禁止、ログ出力時はマスク
8. **Ollama 接続先は `127.0.0.1` にハードコード** — `0.0.0.0` にしない
9. **DirectX フック等のゲームプロセス介入機能は実装しない**
10. **PyQt6 ではなく PySide6 を使用** — ライセンス互換性のため（GPL vs LGPL）

## 既知の落とし穴

- **HTTP クライアントは requests を使う**: `urllib.request` は使わない。[ADR-0003](docs/adr/0003-http-client-requests.md)
- **Tier 0 は CTranslate2 直接実行**: argostranslate / torch は不要。[ADR-0004](docs/adr/0004-ct2-direct-translation.md)
- **WinRT/torch DLL 競合**: argostranslate を使う場合のみ `preload_system_vcrt()` が必要。CT2Translator では不要
- **Windows OCR 言語パック**: winocr は OS レベルの OCR 言語パックに依存。英語 OCR が未インストールの場合がある
- **Ollama のプロキシバイパス**: localhost 通信には `session.trust_env = False` でプロキシを無効化
- **Qt の camelCase メソッド**: `paintEvent` 等の Qt override は ruff N802 を `gui/**` で除外設定済み
- **linter の警告は `noqa` で抑制する前に構造的な解決を検討する**: `noqa` は誤検知の場合のみ使う
- **main ブランチは保護済み**: 直接 push 不可。ブランチを切って PR → CI パス → マージ
- **CI ジョブ名は英語**: GitHub の Required status checks が日本語名を検索できない問題を回避

## 関連ドキュメント

- 設計・アーキテクチャ: [docs/architecture.md](docs/architecture.md)
- セキュリティ設計: [docs/security-design.md](docs/security-design.md)
- ロードマップ: [docs/roadmap.md](docs/roadmap.md)
- リリース・CI/CD: [docs/release.md](docs/release.md)
- ADR: [docs/adr/](docs/adr/)
- コントリビュートガイド: [CONTRIBUTING.md](CONTRIBUTING.md)
