# Release & CI/CD — grabtl

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

## AV 誤検知対策

PyInstaller --onefile は使わない（誤検知率最高）。

**初期（v0.x）:** Nuitka --onedir + Inno Setup + 毎リリース Microsoft 誤検知報告 + VirusTotal 結果添付
**成長期（v1.x）:** Certum Open Source コード署名証明書（年€69）
**安定期:** EV 証明書・Microsoft Store（MSIX）検討

注意: Nuitka が PyInstaller より必ず誤検知が少ないとは限らない（矛盾する報告あり）。
--onedir + インストーラー + コード署名 が根本的解決策。

## バージョニング

Semantic Versioning (MAJOR.MINOR.PATCH)
- 0.x.x: 初期開発フェーズ。API 破壊変更あり得る
- 1.0.0: Protocol インターフェースの安定を宣言
- Protocol インターフェースの変更は MAJOR バージョンアップ
