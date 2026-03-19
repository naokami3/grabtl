# Roadmap — grabtl

## 開発フェーズ

### Phase 1: PoC
Python + mss + winocr + argostranslate でコンソールアプリ。GUI なし。

### Phase 2: ドラッグ選択
PySide6 透過オーバーレイ + マウスドラッグ範囲選択 → OCR → 翻訳。

### Phase 3: オーバーレイ表示
翻訳結果を透過ウィンドウ表示。クリックスルー。ホットキー。

### Phase 4: 設定・品質改善
翻訳エンジン切替（Tier 0/1/2）、APIキー管理、通信ログ、翻訳履歴、用語辞書。
Nuitka ビルド + Inno Setup。

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
- [ ] docs/plugin-guide.md の実装に合わせた更新
