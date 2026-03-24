# Roadmap — grabtl

## 開発フェーズ

### Phase 1: PoC ✅
Python + mss + winocr + argostranslate でコンソールアプリ。GUI なし。

- [x] スクリーンキャプチャ (mss)
- [x] OCR (winocr / Windows OCR API)
- [x] 翻訳 (argostranslate / Opus-MT)
- [x] パイプライン (OCR → 翻訳)
- [x] CLI エントリポイント
- [x] WinRT/torch DLL 競合回避

### Phase 2: ドラッグ選択 ✅
PySide6 透過オーバーレイ + マウスドラッグ範囲選択 → OCR → 翻訳。

- [x] システムトレイ常駐
- [x] グローバルホットキー (Ctrl+Shift+G)
- [x] 全画面透過オーバーレイ + ドラッグ選択
- [x] DPI スケーリング対応
- [x] マルチモニター対応
- [x] 小画像の自動拡大（OCR 精度向上）

### Phase 3: オーバーレイ表示・品質改善 ✅
翻訳結果の表示改善、翻訳エンジンの拡充。

- [x] 段階的表示（OCR 結果 → 翻訳結果）
- [x] オーバーレイ外クリックで結果消去
- [x] ゲーム用語辞書 (Glossary) — PRE_REPLACE / POST_REPLACE
- [x] GlossaryTranslator デコレータ
- [x] Ollama 翻訳エンジン (Tier 1)
- [x] 設定ダイアログ（エンジン切替）
- [x] Ollama セットアップガイド（ダウンロードリンク、コマンドコピー、接続テスト）
- [x] 多重起動防止 (Windows Named Mutex)
- [x] QSettings による設定永続化

### Phase 4: 設定・配布（予定）
翻訳エンジン Tier 2、APIキー管理、ビルド・配布。

- [ ] DeepL API 実装 (Tier 2a)
- [ ] ChatGPT API 実装 (Tier 2b)
- [ ] Gemini API 実装 (Tier 2c)
- [ ] APIキー管理 (keyring)
- [ ] ホットキーのカスタマイズ
- [ ] カスタム用語辞書の UI 編集
- [ ] ゲーム別辞書パック
- [ ] 翻訳履歴
- [ ] 翻訳キャッシュ（同一テキストの再翻訳回避）
- [ ] 初回オンボーディングガイド
- [ ] Nuitka ビルド + Inno Setup
- [ ] AV 誤検知対策（コード署名）

### 将来の検討事項
- [ ] torch 排除（CTranslate2 で Opus-MT モデルを直接実行）
- [ ] 翻訳プロセス分離（subprocess でメモリ管理改善）
- [ ] 排他フルスクリーンゲーム対応
- [ ] 音フィードバック（翻訳完了 SE）
- [ ] Sugoi-14B-Ultra (Ollama) による ja→en 返信翻訳

## OSS ガバナンス

### v0.1.0 までに必須
- [x] LICENSE (MIT)
- [x] README.md (英語) + README.ja.md (日本語)
- [x] SECURITY.md（脆弱性報告: GitHub Private Vulnerability Reporting, 48時間確認目標）
- [x] CONTRIBUTING.md（開発環境セットアップ、コーディング規約、PRチェックリスト）
- [x] NOTICE（依存ライブラリライセンス一覧）
- [x] docs/security-design.md（セキュリティ設計書）

### v0.2.0 までに整備
- [ ] .github/ISSUE_TEMPLATE/（バグ報告・機能要望）
- [ ] .github/PULL_REQUEST_TEMPLATE.md

### v1.0.0 までに整備
- [x] CODE_OF_CONDUCT.md（Contributor Covenant）— 前倒しで作成済み
- [x] CHANGELOG.md（Keep a Changelog 形式、SemVer 準拠）— 前倒しで作成済み
- [x] docs/adr/（Architecture Decision Records）— ADR-0001, ADR-0002 作成済み
- [ ] docs/plugin-guide.md の実装に合わせた更新
