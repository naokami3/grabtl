# ADR-0004: CTranslate2 直接利用による torch 排除

- **Status:** Accepted
- **Date:** 2026-03-24
- **Decision makers:** @naokami3

## Context

Tier 0 の翻訳エンジン argostranslate が stanza 経由で torch に依存しており、以下の問題があった:
- メモリ消費: torch だけで 200-500MB
- DLL 競合: WinRT (winocr) と torch の msvcp140.dll バージョン不一致（_dll_fix.py で回避）
- 起動時間: torch のロードに数秒

## 調査結果

torch は CTranslate2 ではなく **stanza** が引き込んでいた。CTranslate2 自体は torch に依存しない。
argostranslate の翻訳処理は CTranslate2 + SentencePiece で完結しており、stanza は文分割のみに使用。

## Decision

**argostranslate を CTranslate2 + SentencePiece + pysbd の直接利用に置き換える。**

- CTranslate2: Opus-MT モデルの推論エンジン（argostranslate と同じ）
- SentencePiece: トークナイザー（argostranslate と同じ）
- pysbd: 文分割（MIT ライセンス、純粋 Python、torch 不要）

argostranslate がダウンロードしたモデルファイル（model.bin, sentencepiece.model）をそのまま再利用する。

### 不採用にした文分割ライブラリ

| ライブラリ | 不採用理由 |
|-----------|-----------|
| stanza | torch に依存（排除したい対象） |
| minisbd | AGPL ライセンス（MIT プロジェクトと非互換） |
| spacy | 依存が大きすぎる（~200MB） |

## Consequences

- torch が不要になり、メモリ 200-500MB 削減
- DLL 競合のリスクが低減（ただし _dll_fix.py は防御的に維持）
- 翻訳品質は argostranslate と同一（同じモデル・同じエンジン）
- argos.py はフォールバック用に残す（translate-legacy extras）
- ctranslate2, sentencepiece, pysbd をコア依存に追加（計 ~63MB、torch 447MB の排除と比較して大幅削減）
