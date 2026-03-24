"""ゲーム用語辞書の管理。

翻訳の前後にゲーム固有の用語を置換する。
- PRE_REPLACE: 翻訳前に完全置換（略語・定型文）
- POST_REPLACE: 翻訳後に用語を上書き
"""

from __future__ import annotations

import enum
import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class EntryType(enum.Enum):
    """辞書エントリの置換タイミング。"""

    PRE_REPLACE = "pre"
    POST_REPLACE = "post"


@dataclass
class GlossaryEntry:
    """辞書エントリ。"""

    source: str
    target: str
    entry_type: EntryType = EntryType.POST_REPLACE
    case_sensitive: bool = False
    _pattern: re.Pattern[str] | None = field(default=None, repr=False, compare=False)

    def pattern(self) -> re.Pattern[str]:
        """コンパイル済み正規表現パターンを返す。"""
        if self._pattern is None:
            flags = 0 if self.case_sensitive else re.IGNORECASE
            self._pattern = re.compile(r"\b" + re.escape(self.source) + r"\b", flags)
        return self._pattern


class Glossary:
    """ゲーム用語辞書。

    翻訳の前後にゲーム固有の用語を置換する。
    長いフレーズから先にマッチし、単語境界で区切ってマッチする。
    """

    def __init__(self, entries: list[GlossaryEntry] | None = None) -> None:
        self._entries = entries or []
        # 長いフレーズから先にマッチするようにソート
        self._entries.sort(key=lambda e: len(e.source), reverse=True)

    def pre_translate(self, text: str) -> str:
        """翻訳前に PRE_REPLACE エントリを適用する。"""
        for entry in self._entries:
            if entry.entry_type == EntryType.PRE_REPLACE:
                text = entry.pattern().sub(entry.target, text)
        return text

    def post_translate(self, text: str) -> str:
        """翻訳後に POST_REPLACE エントリを適用する。"""
        for entry in self._entries:
            if entry.entry_type == EntryType.POST_REPLACE:
                text = entry.pattern().sub(entry.target, text)
        return text

    def add(self, entry: GlossaryEntry) -> None:
        """エントリを追加する。"""
        self._entries.append(entry)
        self._entries.sort(key=lambda e: len(e.source), reverse=True)

    @classmethod
    def load_from_file(cls, path: str | Path) -> Glossary:
        """JSON ファイルから辞書を読み込む。

        JSON 形式:
        {
            "entries": [
                {"source": "raid", "target": "レイド", "type": "post"},
                {"source": "GG", "target": "お疲れ様", "type": "pre"}
            ]
        }
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        entries = []
        for item in data.get("entries", []):
            entries.append(
                GlossaryEntry(
                    source=item["source"],
                    target=item["target"],
                    entry_type=EntryType(item.get("type", "post")),
                    case_sensitive=item.get("case_sensitive", False),
                )
            )
        return cls(entries)

    @classmethod
    def default(cls) -> Glossary:
        """ビルトインのゲーム用語辞書を返す。"""
        entries = []

        # PRE_REPLACE: 略語・定型文（翻訳前に完全置換）
        pre_entries = {
            "gg wp": "お疲れ様、いいプレイだった",
            "gl hf": "頑張りましょう",
            "GG": "お疲れ様",
            "LFG": "メンバー募集",
            "LFM": "メンバー募集中",
            "AFK": "離席中",
            "BRB": "すぐ戻ります",
            "DC": "回線落ち",
            "ty": "ありがとう",
            "thx": "ありがとう",
            "np": "どういたしまして",
        }
        for source, target in pre_entries.items():
            entries.append(
                GlossaryEntry(
                    source=source,
                    target=target,
                    entry_type=EntryType.PRE_REPLACE,
                    case_sensitive=False,
                )
            )

        # POST_REPLACE: ゲーム用語（翻訳後に上書き）
        post_entries = {
            "raid": "レイド",
            "dungeon": "ダンジョン",
            "quest": "クエスト",
            "guild": "ギルド",
            "healer": "ヒーラー",
            "buff": "バフ",
            "debuff": "デバフ",
            "nerf": "ナーフ",
            "loot": "ルート",
            "respawn": "リスポーン",
            "aggro": "アグロ",
            "wipe": "ワイプ",
            "mob": "モブ",
        }
        for source, target in post_entries.items():
            entries.append(
                GlossaryEntry(
                    source=source,
                    target=target,
                    entry_type=EntryType.POST_REPLACE,
                    case_sensitive=False,
                )
            )

        return cls(entries)
