"""ゲーム用語辞書のテスト。"""

from __future__ import annotations

from grabtl.core.glossary.decorator import GlossaryTranslator
from grabtl.core.glossary.manager import EntryType, Glossary, GlossaryEntry


class FakeTranslator:
    """テスト用翻訳エンジン。入力をそのまま返す。"""

    def translate(self, text: str, source: str, target: str) -> str:
        return text

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def is_local(self) -> bool:
        return True

    @property
    def allowed_endpoints(self) -> list[str]:
        return []


class TestGlossaryPreReplace:
    def test_略語が翻訳前に置換される(self) -> None:
        glossary = Glossary(
            [
                GlossaryEntry("GG", "お疲れ様", EntryType.PRE_REPLACE),
            ]
        )
        result = glossary.pre_translate("GG")
        assert result == "お疲れ様"

    def test_大文字小文字を区別しない(self) -> None:
        glossary = Glossary(
            [
                GlossaryEntry("gg", "お疲れ様", EntryType.PRE_REPLACE),
            ]
        )
        result = glossary.pre_translate("GG")
        assert result == "お疲れ様"

    def test_単語境界でマッチする(self) -> None:
        glossary = Glossary(
            [
                GlossaryEntry("GG", "お疲れ様", EntryType.PRE_REPLACE),
            ]
        )
        # "GG" は単語として存在する
        result = glossary.pre_translate("GG everyone!")
        assert "お疲れ様" in result

    def test_部分一致はしない(self) -> None:
        glossary = Glossary(
            [
                GlossaryEntry("GG", "お疲れ様", EntryType.PRE_REPLACE),
            ]
        )
        # "EGG" の中の "GG" にはマッチしない
        result = glossary.pre_translate("EGG")
        assert result == "EGG"

    def test_長いフレーズが先にマッチする(self) -> None:
        glossary = Glossary(
            [
                GlossaryEntry("GG", "お疲れ様", EntryType.PRE_REPLACE),
                GlossaryEntry("gg wp", "お疲れ様、いいプレイだった", EntryType.PRE_REPLACE),
            ]
        )
        result = glossary.pre_translate("gg wp")
        assert result == "お疲れ様、いいプレイだった"

    def test_POST_REPLACEは適用されない(self) -> None:
        glossary = Glossary(
            [
                GlossaryEntry("raid", "レイド", EntryType.POST_REPLACE),
            ]
        )
        result = glossary.pre_translate("raid boss")
        assert result == "raid boss"


class TestGlossaryPostReplace:
    def test_用語が翻訳後に置換される(self) -> None:
        glossary = Glossary(
            [
                GlossaryEntry("raid", "レイド", EntryType.POST_REPLACE),
            ]
        )
        result = glossary.post_translate("Let's go raid")
        assert "レイド" in result

    def test_raiderにraidがマッチしない(self) -> None:
        glossary = Glossary(
            [
                GlossaryEntry("raid", "レイド", EntryType.POST_REPLACE),
            ]
        )
        result = glossary.post_translate("The raider attacks")
        assert result == "The raider attacks"

    def test_PRE_REPLACEは適用されない(self) -> None:
        glossary = Glossary(
            [
                GlossaryEntry("GG", "お疲れ様", EntryType.PRE_REPLACE),
            ]
        )
        result = glossary.post_translate("GG")
        assert result == "GG"


class TestGlossaryDefault:
    def test_デフォルト辞書が生成できる(self) -> None:
        glossary = Glossary.default()
        # PRE_REPLACE エントリが含まれる
        result = glossary.pre_translate("GG")
        assert result == "お疲れ様"

    def test_デフォルト辞書のPOST_REPLACE(self) -> None:
        glossary = Glossary.default()
        result = glossary.post_translate("dungeon raid")
        assert "ダンジョン" in result
        assert "レイド" in result


class TestGlossaryTranslator:
    def test_Protocolに準拠(self) -> None:
        from grabtl.core.translation.base import Translator

        translator = GlossaryTranslator(FakeTranslator(), Glossary.default())
        assert isinstance(translator, Translator)

    def test_前後処理が適用される(self) -> None:
        glossary = Glossary(
            [
                GlossaryEntry("LFG", "メンバー募集", EntryType.PRE_REPLACE),
                GlossaryEntry("raid", "レイド", EntryType.POST_REPLACE),
            ]
        )
        translator = GlossaryTranslator(FakeTranslator(), glossary)

        # FakeTranslator は入力をそのまま返すので
        # pre: "LFG for raid" → "メンバー募集 for raid"
        # translate: そのまま
        # post: "メンバー募集 for raid" → "メンバー募集 for レイド"
        result = translator.translate("LFG for raid", "en", "ja")
        assert "メンバー募集" in result
        assert "レイド" in result

    def test_プロパティが内部translatorに委譲される(self) -> None:
        translator = GlossaryTranslator(FakeTranslator(), Glossary.default())
        assert translator.requires_api_key is False
        assert translator.is_local is True
        assert translator.allowed_endpoints == []
