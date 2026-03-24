# ADR-0002: 翻訳エンジンの Tier 構成

- **Status:** Accepted
- **Date:** 2026-03-24
- **Decision makers:** @naokami3

## Context

翻訳エンジンを複数提供するにあたり、ユーザーが迷わない構成にしたい。
モデル名や技術的な選択肢を並べるのではなく、「機械翻訳 / AI翻訳 / API翻訳」の3段階でシンプルに提示する。

ローカル AI 翻訳は GPU メモリを圧迫しない軽量モデル1本に絞る。

## 調査したモデルとライセンス

### ライセンス安全（商用利用可）

| モデル | ライセンス | VRAM (Q4) | en→ja 品質 |
|--------|-----------|-----------|-----------|
| Qwen 2.5 3B | Apache 2.0 | 2GB | ⭐⭐⭐ |
| Qwen 2.5 7B | Apache 2.0 | 4.3GB | ⭐⭐⭐⭐ |
| DeepSeek-R1 8B | MIT | 5GB | ⭐⭐ |
| Phi-4 3.8B | MIT | 2.2GB | ⭐⭐ |
| Mistral 7B | Apache 2.0 | 4.3GB | ⭐⭐⭐ |

### ライセンスに問題あり（除外）

| モデル | 問題 |
|--------|------|
| Gemma 3 | Google Gemma Terms of Use が法的に曖昧 |
| Llama 3.x | 700M MAU 制限。商用スケール時に Meta の許可必要 |

## Decision

### 翻訳エンジンの Tier 構成

```
翻訳エンジン:
  ◉ 機械翻訳（デフォルト・オフライン）
  ○ AI翻訳（Ollama・要インストール）
  ○ DeepL API（要APIキー）
  ○ ChatGPT API（要APIキー）
  ○ Gemini API（要APIキー）
```

| Tier | 表示名 | エンジン | 要件 | 品質 |
|------|--------|---------|------|------|
| 0 | 機械翻訳 | Opus-MT + Glossary | なし（即使える） | 読める |
| 1 | AI翻訳 | Ollama + **Qwen 2.5 3B** | Ollama インストール | 自然 |
| 2a | DeepL | DeepL API | APIキー | 高品質 |
| 2b | ChatGPT | OpenAI API | APIキー | 高品質 |
| 2c | Gemini | Google Gemini API | APIキー | 高品質 |

### ローカル AI 翻訳のモデル選定: Qwen 2.5 3B

**選定理由:**
- **VRAM 2GB** — ゲーム起動中でも GPU メモリを圧迫しない
- **CPU でも動作** — GPU なしの環境でもフォールバック可能
- **Apache 2.0** — 商用利用に問題なし、MAU 制限なし
- **日本語性能** — 3B クラスで最も高い（Alibaba が日本語を含むアジア言語に注力）

**不採用理由（他モデル）:**
- Qwen 2.5 7B: 品質は上だが VRAM 4.3GB はゲーム中に重い
- DeepSeek-R1: MIT だが en→ja 翻訳品質が低評価
- Phi-4: MIT だが翻訳タスクに最適化されていない
- Gemma: 法的リスク
- Llama: MAU 制限

## Consequences

- ユーザーはモデル名を知る必要がない。「AI翻訳」を選ぶだけ
- Ollama のインストールガイドをアプリ内またはドキュメントで提供する必要がある
- Tier 2 の各 API は `core/translation/` に個別実装。`allowed_endpoints` に通信先を登録
- 将来モデルを変更する場合、ユーザー側の設定変更は不要（内部的に切り替えるだけ）
