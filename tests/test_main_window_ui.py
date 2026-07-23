import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402
from qfluentwidgets import Theme, setTheme, setThemeColor  # noqa: E402


class MainWindowUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        setTheme(Theme.LIGHT)
        setThemeColor("#1463ff")

    def test_toolbar_actions_follow_empty_and_task_states(self):
        with TemporaryDirectory() as tmp:
            os.environ["APPDATA"] = tmp
            from app.ui.main_window import MainWindow

            window = MainWindow()
            buttons = window.toolbar_buttons

            self.assertTrue(buttons["import"].isEnabled())
            self.assertTrue(buttons["import_folder"].isEnabled())
            self.assertTrue(buttons["output"].isEnabled())
            self.assertTrue(buttons["settings"].isEnabled())
            self.assertTrue(buttons["history"].isEnabled())
            for key in ["start", "pause", "resume", "stop", "retry", "clear"]:
                self.assertFalse(buttons[key].isEnabled(), key)

            source = Path(tmp) / "book.txt"
            source.write_text("正文", encoding="utf-8")
            window.add_paths([str(source)])

            self.assertTrue(buttons["start"].isEnabled())
            self.assertTrue(buttons["clear"].isEnabled())
            self.assertFalse(buttons["pause"].isEnabled())
            self.assertFalse(buttons["resume"].isEnabled())
            self.assertFalse(buttons["stop"].isEnabled())
            self.assertFalse(buttons["retry"].isEnabled())
            window.close()

    def test_loads_recent_tasks_without_duplicates(self):
        with TemporaryDirectory() as tmp:
            os.environ["APPDATA"] = tmp
            from app.ui.main_window import MainWindow

            source = Path(tmp) / "book.txt"
            source.write_text("正文", encoding="utf-8")
            window = MainWindow()
            window.add_paths([str(source)])
            task_id = window.tasks[0].id
            window.clear_tasks()

            window.load_recent_tasks(show_empty=False)
            window.load_recent_tasks(show_empty=False)

            self.assertEqual([task.id for task in window.tasks], [task_id])
            window.close()

    def test_settings_dialog_applies_conversion_preset_and_css_template(self):
        with TemporaryDirectory() as tmp:
            os.environ["APPDATA"] = tmp
            from app.core.models import AppConfig
            from app.ui.main_window import SettingsDialog

            dialog = SettingsDialog(AppConfig(output_dir=str(Path(tmp) / "out")))

            dialog.apply_conversion_preset("固定字数兜底")

            self.assertEqual(dialog.chapter_rule_combo.currentText(), "fixed_size")
            self.assertEqual(dialog.fixed_chars_spin.value(), 6000)
            self.assertIn("line-height", dialog.default_css_edit.toPlainText())
            dialog.close()

    def test_side_panel_can_shrink_to_sidebar_width(self):
        with TemporaryDirectory() as tmp:
            os.environ["APPDATA"] = tmp
            from app.ui.main_window import MainWindow

            window = MainWindow()
            splitter = window.centralWidget()
            right_panel = splitter.widget(1)

            self.assertLessEqual(right_panel.minimumSizeHint().width(), 180)
            self.assertEqual(right_panel.minimumWidth(), 320)
            window.close()

    def test_book_settings_apply_to_checked_tasks(self):
        with TemporaryDirectory() as tmp:
            os.environ["APPDATA"] = tmp
            from app.ui.main_window import MainWindow

            first = Path(tmp) / "first.txt"
            second = Path(tmp) / "second.txt"
            first.write_text("正文", encoding="utf-8")
            second.write_text("正文", encoding="utf-8")
            window = MainWindow()
            window.add_paths([str(first), str(second)])

            window.apply_book_settings({"author": "批量作者"})

            self.assertEqual([task.author for task in window.tasks], ["批量作者", "批量作者"])
            window.close()


if __name__ == "__main__":
    unittest.main()
