# ADR-0001: Tier 0 翻訳エンジンの選定

- **Status:** Accepted
- **Date:** 2026-03-24
- **Decision makers:** @naokami3

## Context

Tier 0（APIキー不要・オフライン完結）の翻訳エンジンとして、ゲーム内テキスト（クエスト本文、チャット、UI）の英日翻訳品質を改善したい。

現行の argostranslate（Opus-MT）は以下の問題がある:
- "watchtower" → "時計塔"（正: 見張り塔）
- "spotted" → "点在しています"（正: 目撃された）
- 主語の欠落、不自然な語順

## Candidates

### A. argostranslate（Opus-MT）— 現行

- Helsinki-NLP の en-ja 専用モデル（~70MB）
- CTranslate2 ベースだが argostranslate 経由で torch に依存
- 翻訳速度: 30-60ms
- メモリ: ~500MB（torch 込み）

### B. NLLB-200-distilled-600M（CTranslate2 直接）

- Meta の 200 言語対応汎用モデル（~2.4GB）
- torch 不要（CTranslate2 + SentencePiece のみ）
- 翻訳速度: 1000-5000ms
- メモリ: ~3GB

### C. argostranslate + Glossary（用語辞書）

- 現行エンジンにゲーム用語辞書の前後処理を追加
- 追加メモリ: ほぼゼロ
- 追加速度コスト: <1ms

## Evaluation

### NLLB-600M の実測結果（2026-03-24）

ゲームテキスト 12 文で比較した結果、NLLB-600M の出力は**壊滅的**だった:

```
EN: The dragon has been spotted near the northern watchtower.
Opus: 北部の時計塔付近にドラゴンが点在しています。
NLLB: -   ( ( (-- -- -- --   [ ( ( - - - ⁠ ⁠ ⁠   "  ... ... .（以下記号の羅列）

EN: Bring me 5 iron ingots and I shall forge you a mighty blade.
Opus: 5本の鉄のインゴットを持参し、あなたに大きな刃を鍛造します。
NLLB: -  5-5... { { { (-- -- { { \ { {{ { { [--（以下記号の羅列）
```

12 文中、NLLB が読める日本語を出力したのは 0 文。Opus-MT は全文で読める翻訳を出力。

**原因:** NLLB-600M は 200 言語を 600M パラメータで共有するため、en→ja の実効パラメータが極めて少ない。en-ja 専用で学習された Opus-MT に品質で大きく劣る。

### Glossary の実測結果

```
EN: LFG for raid at the dungeon
辞書なし: （そのまま英語）
辞書あり: ダンジョン で レイド を募集

EN: GG everyone!
辞書なし: （そのまま英語）
辞書あり: お疲れ様でした!
```

ゲーム用語・チャットスラングの翻訳品質が大幅に改善。

### FuguMT (staka/fugumt-en-ja) の実測結果（2026-03-24）

デフォルトパラメータでは NLLB 同様に繰り返し出力が発生し壊滅的だった。
`repetition_penalty=1.5`, `no_repeat_ngram_size=3`, `max_length=128` で調整後は出力が安定したが、
ゲーム用語の翻訳精度は Opus-MT と同等かやや劣る結果:

```
EN: Anyone want to raid tonight?
Opus: 誰が一晩寝たいですか?
Fugu: 今日は誰でも急ぐ気はする?

EN: Need a healer for the boss fight.
Opus: ボスの戦いのためのヒーラーが必要です。
Fugu: お手入れの必要な人、お手入れが出来るから
```

Opus-MT はゲーム用語をカタカナ音写する傾向があり、Glossary との相性が良い。
FuguMT は日本語として自然な意訳をするが、ゲーム文脈から外れた訳語が多い。

### Sugoi V4 の調査結果（2026-03-24）

HuggingFace で公開されている Sugoi V4 CTranslate2 モデルは **ja→en（日本語→英語）のみ**。
en→ja（英語→日本語）版は存在しないため評価不可。

Sugoi-14B-Ultra（Qwen2.5-14B ベース LLM、Apache 2.0）は en↔ja 双方向対応だが、
14B パラメータは Tier 0 の範囲を超える。Tier 1（Ollama）の候補として記録。

## Decision

**C. argostranslate + Glossary を採用する。**

- Opus-MT はゲームテキストの翻訳として「読める」品質を提供する
- Glossary（用語辞書）でゲーム固有の用語・略語を補正する
- NLLB は不採用（出力が壊滅的）
- FuguMT は不採用（Opus-MT + Glossary と比較してメリットなし）
- Sugoi V4 は不採用（en→ja モデルが存在しない）
- 本質的な翻訳品質の改善は Tier 1（Ollama/LLM）または Tier 2（DeepL API）で対応する
- Tier 1 の候補として Sugoi-14B-Ultra（GGUF、Apache 2.0）を記録

## Consequences

- Tier 0 の翻訳品質は「完璧ではないが読める」レベル。これは設計上意図的
- torch 依存は argostranslate 経由で残る（DLL 競合回避の `_dll_fix.py` が引き続き必要）
- 将来 torch 依存を外したい場合は、argostranslate を CTranslate2 直接利用に置き換える（Opus-MT モデルは CTranslate2 形式で利用可能）
- Glossary はユーザーがカスタム辞書を JSON で追加可能。ゲームごとの辞書パック配布も将来的に検討
