"""LLM 翻訳エンジン共通ユーティリティ。

Ollama / ChatGPT / Gemini で共用する言語マッピング、
プロンプトテンプレート、レスポンスクリーニングを提供する。
"""

from __future__ import annotations

LANG_MAP: dict[str, str] = {
    "en": "English",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "pt": "Portuguese",
    "ru": "Russian",
}

SYSTEM_PROMPT = (
    "You are a translator for a video game. "
    "Translate the following text into {target_name}. "
    "Output ONLY the translated text, nothing else. "
    "Do not add explanations, notes, or alternatives."
)

_PREFIXES_TO_STRIP = [
    "Translation:",
    "Translated text:",
    "Here is the translation:",
    "翻訳:",
    "翻訳結果:",
]


def clean_response(raw: str) -> str:
    """LLM レスポンスから翻訳テキストのみを抽出する。"""
    text = raw.strip()

    # よくあるプレフィックスを除去
    for prefix in _PREFIXES_TO_STRIP:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix) :].strip()

    # 引用符を除去
    if len(text) >= 2 and (
        (text[0] == '"' and text[-1] == '"')
        or (text[0] == "'" and text[-1] == "'")
        or (text[0] == "「" and text[-1] == "」")
    ):
        text = text[1:-1].strip()

    # "Note:" "Explanation:" 行を除去
    lines = text.split("\n")
    filtered = []
    for line in lines:
        lower = line.strip().lower()
        if lower.startswith(("note:", "explanation:", "original:", "(note")):
            continue
        filtered.append(line)
    text = "\n".join(filtered).strip()

    return text if text else raw.strip()


