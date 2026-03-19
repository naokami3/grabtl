"""スクリーンキャプチャのテスト。"""

from __future__ import annotations

import pytest

from grabtl.core.capture.screen import capture_region


class TestCaptureRegion:
    def test_幅が0以下でValueError(self) -> None:
        with pytest.raises(ValueError, match="幅と高さは正の値"):
            capture_region(0, 0, 0, 100)

    def test_高さが0以下でValueError(self) -> None:
        with pytest.raises(ValueError, match="幅と高さは正の値"):
            capture_region(0, 0, 100, -1)

    def test_負の幅でValueError(self) -> None:
        with pytest.raises(ValueError, match="幅と高さは正の値"):
            capture_region(0, 0, -10, 100)
