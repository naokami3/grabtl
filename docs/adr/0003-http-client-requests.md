# ADR-0003: HTTP クライアントに requests を採用

- **Status:** Accepted
- **Date:** 2026-03-24
- **Decision makers:** @naokami3

## Context

Tier 2 API 翻訳エンジン（DeepL / ChatGPT / Gemini）の実装中に、ruff の S310（`suspicious-url-open-usage`）が `urllib.request` の全呼び出しで発火した。

当初は `# noqa: S310` コメントで抑制する方針だったが、以下の理由で方針を見直した:

- `noqa` が散在すると linter の警告が形骸化する
- 後から見て「なぜ抑制しているか」の判断が難しい
- linter のエラーには意味があり、根本原因に対処すべき

## 不採用にした対処法

### `# noqa: S310` で個別抑制
- **問題:** 4ファイル×2箇所 = 8箇所に `noqa` が散在。将来の開発者が「本当に安全か」を毎回判断する必要がある
- **教訓:** `noqa` は最後の手段であり、構造的な解決を先に検討すべき

### `per-file-ignores` でディレクトリ単位の除外
```toml
"src/grabtl/core/translation/**" = ["S310"]
```
- **問題:** 真の S310 脆弱性（ユーザー入力由来の URL）を見落とすリスク
- **教訓:** ルールを無効化するのではなく、ルールが発火しない設計にすべき

### `_http.py` に集約して1箇所だけ `noqa`
- **問題:** `noqa` の数は減るが本質は変わらない。urllib.request 自体を使い続ける限り S310 は潜在リスクとして残る

## Decision

**`urllib.request` を廃止し、`requests` ライブラリに統一する。**

### 理由

1. **S310 が根本的に発生しない** — requests は bandit/ruff の URL 監査対象外
2. **業界標準** — OpenAI SDK (httpx), DeepL SDK (requests), litellm (httpx) 等、主要 OSS は全て requests または httpx を採用。urllib.request を使うプロジェクトは皆無
3. **Session でコネクション再利用** — urllib.request より効率的
4. **プロキシ管理が簡潔** — `session.trust_env = False` で localhost のプロキシバイパスが1行
5. **エラーハンドリングが明瞭** — `resp.ok`, `resp.status_code`, `resp.json()` でシンプルに処理

### 実装

- `core/translation/_http.py` に共通 HTTP ユーティリティを集約
- 全翻訳エンジン（Ollama / DeepL / ChatGPT / Gemini）が `_http.py` 経由で通信
- `requests>=2.31` をコア依存に移動（`translate-cloud` extras を廃止）
- `types-requests` を dev 依存に追加（mypy の型チェック用）

## Consequences

- ruff S310 は 0 件（`noqa` コメントなし）
- `requests` がコア依存に入るため、Tier 0 のみのユーザーにも requests がインストールされる（~2MB、実害なし）
- 将来 httpx に移行する場合も、`_http.py` の内部実装のみ変更すれば全エンジンに反映される

## 教訓

**linter の警告は抑制する前に「なぜ発火しているか」を理解し、構造的な解決を検討する。**
`noqa` は「ルールが誤検知している」場合にのみ使うべきであり、「ルールが正しいが対処が面倒」な場合は設計を見直すサイン。
