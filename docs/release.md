# Release & CI/CD — grabtl

## CI/CD

### PR ごと / main push
- `ruff check` + `ruff format --check`
- `mypy --strict src/`
- `pytest --cov=src/grabtl`（全テスト + カバレッジ）
- `pip-audit`（依存パッケージの脆弱性スキャン）
- 通信先テスト: テスト中に許可リスト外ドメインへ通信したら fail

### リリース時（タグ push）
- Nuitka ビルド → Inno Setup → GitHub Releases に自動アップロード
- SHA256 ハッシュをリリースノートに記載
- VirusTotal API スキャン結果を添付

## ローカルビルド手順

### 前提条件
- Python 3.11+（開発環境セットアップ済み）
- [Nuitka](https://nuitka.net/)（`pip install nuitka`）
- [Inno Setup 6](https://jrsoftware.org/ispack.php)（インストーラー生成用）
- C コンパイラ（Visual Studio Build Tools の cl.exe）
- 翻訳モデル（`~/.local/share/argos-translate/packages/en_ja`）— 未インストールの場合 build.py が WARNING を出すが、ビルド自体は完了する

### 手順

#### 1. バージョン番号を更新

以下のファイルのバージョンを揃える:

| ファイル | 変更箇所 |
|---|---|
| `pyproject.toml` | `version` |
| `src/grabtl/__init__.py` | `__version__` |
| `build.py` | `--windows-file-version` / `--windows-product-version` |
| `installer.iss` | `AppVersion` / `OutputBaseFilename` |

#### 2. exe をビルド（Nuitka）

```bash
python build.py
```

出力先: `build/release/build_entry.dist/grabtl.exe`

#### 3. インストーラーを生成（Inno Setup）

```bash
# ISCC.exe が PATH に入っている場合
iscc installer.iss

# フルパス指定（デフォルトのインストール先）
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

出力先: `build/installer/grabtl-<version>-setup.exe`

#### 4. タグを作成・push

```bash
git tag -a v<version> -m "v<version> — リリースノート"
git push origin v<version>
```

#### 5. 旧バージョンのインストーラーを削除

`build/installer/` 内の古い setup.exe を削除する。

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
