import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402
from qfluentwidgets import Theme, setTheme, setThemeColor  # noqa: E402

from app.core.models import ConvertTask  # noqa: E402
from app.ui.book_setting_panel import BookSettingPanel  # noqa: E402


class BookSettingPanelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        setTheme(Theme.LIGHT)
        setThemeColor("#1463ff")

    def test_generates_text_cover_and_applies_path(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "book.txt"
            source.write_text("body", encoding="utf-8")
            task = ConvertTask(source, root / "book.epub", "txt")
            panel = BookSettingPanel()
            panel.set_task(task)

            cover_path = panel.generate_cover()

            self.assertTrue(Path(cover_path).exists())
            self.assertEqual(panel.cover_edit.text(), cover_path)


if __name__ == "__main__":
    unittest.main()
