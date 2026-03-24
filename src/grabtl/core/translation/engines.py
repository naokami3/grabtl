"""翻訳エンジンの種別定義。"""

from __future__ import annotations

import enum


class EngineType(enum.StrEnum):
    """翻訳エンジンの種別。"""

    ARGOS = "argos"
    OLLAMA = "ollama"
    DEEPL = "deepl"
    CHATGPT = "chatgpt"
    GEMINI = "gemini"
