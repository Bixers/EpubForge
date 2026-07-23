import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402
from qfluentwidgets import Theme, setTheme, setThemeColor  # noqa: E402

from app.core.models import AppConfig, Chapter, ConvertTask  # noqa: E402
from app.ui.chapter_preview_panel import ChapterPreviewPanel, INSERT_BEFORE, INSERT_VOLUME_END  # noqa: E402


class ChapterPreviewPanelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        setTheme(Theme.LIGHT)
        setThemeColor("#1463ff")

    def make_panel(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        source = root / "book.txt"
        source.write_text("body", encoding="utf-8")
        task = ConvertTask(source, root / "book.epub", "txt")
        task.edited_chapters = [
            Chapter(1, "第一章", "内容一", volume_title="第一卷"),
            Chapter(2, "第二章", "内容二", volume_title="第一卷"),
            Chapter(3, "第三章", "内容三", volume_title="第二卷"),
        ]
        panel = ChapterPreviewPanel()
        panel.set_task(task, AppConfig(output_dir=str(root)))
        return panel, task

    def make_root_panel(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        source = root / "book.txt"
        source.write_text("body", encoding="utf-8")
        task = ConvertTask(source, root / "book.epub", "txt")
        task.edited_chapters = [
            Chapter(1, "第一章", "内容一"),
            Chapter(2, "第二章", "内容二"),
            Chapter(3, "第三章", "内容三"),
        ]
        panel = ChapterPreviewPanel()
        panel.set_task(task, AppConfig(output_dir=str(root)))
        return panel, task

    def tearDown(self):
        if hasattr(self, "tmp"):
            self.tmp.cleanup()

    def test_splitters_stay_draggable_without_task(self):
        with TemporaryDirectory() as tmp:
            panel = ChapterPreviewPanel()
            panel.set_task(None, AppConfig(output_dir=tmp))

            self.assertTrue(panel.isEnabled())
            self.assertTrue(panel.body_splitter.isEnabled())
            self.assertTrue(panel.editor_splitter.isEnabled())
            self.assertTrue(panel.body_splitter.handle(1).isEnabled())
            self.assertTrue(panel.editor_splitter.handle(1).isEnabled())
            self.assertFalse(panel.chapter_tree.isEnabled())

    def test_displays_volumes_and_chapters_as_tree(self):
        panel, _task = self.make_panel()

        self.assertEqual(panel.chapter_tree.topLevelItemCount(), 2)
        self.assertEqual(panel.volume_items["第一卷"].childCount(), 2)
        self.assertEqual(panel.volume_items["第二卷"].childCount(), 1)

    def test_adds_chapter_inside_selected_volume(self):
        panel, _task = self.make_panel()
        panel.chapter_tree.setCurrentItem(panel.volume_items["第一卷"])
        panel.insert_combo.setCurrentText(INSERT_VOLUME_END)

        panel.add_chapter()

        self.assertEqual([chapter.volume_title for chapter in panel.chapters], ["第一卷", "第一卷", "第一卷", "第二卷"])
        self.assertEqual(panel.chapters[2].title, "新建章节")

    def test_renames_volume_and_updates_child_chapters(self):
        panel, task = self.make_panel()
        panel.chapter_tree.setCurrentItem(panel.volume_items["第一卷"])
        panel.volume_edit.setText("新版第一卷")

        panel.save_current_chapter()

        self.assertEqual(panel.volume_order[0], "新版第一卷")
        self.assertEqual([chapter.volume_title for chapter in task.edited_chapters[:2]], ["新版第一卷", "新版第一卷"])

    def test_moves_selected_chapter_down(self):
        panel, _task = self.make_panel()
        panel.chapter_tree.setCurrentItem(panel.chapter_items[0])

        panel.move_selected_down()

        self.assertEqual([chapter.title for chapter in panel.chapters], ["第二章", "第一章", "第三章"])
        self.assertEqual([chapter.index for chapter in panel.chapters], [1, 2, 3])

    def test_deletes_selected_volume_with_children(self):
        panel, _task = self.make_panel()
        panel.chapter_tree.setCurrentItem(panel.volume_items["第一卷"])

        panel.delete_selected()

        self.assertEqual([chapter.title for chapter in panel.chapters], ["第三章"])
        self.assertNotIn("第一卷", panel.volume_order)

    def test_moves_multiple_selected_chapters_to_target_volume(self):
        panel, task = self.make_panel()
        panel.target_volume_combo.setCurrentText("第二卷")
        panel.chapter_tree.setCurrentItem(panel.chapter_items[0])
        panel.chapter_items[0].setSelected(True)
        panel.chapter_items[1].setSelected(True)

        panel.move_selected_to_volume()

        self.assertEqual([chapter.title for chapter in panel.chapters], ["第三章", "第一章", "第二章"])
        self.assertEqual([chapter.volume_title for chapter in panel.chapters], ["第二卷", "第二卷", "第二卷"])
        self.assertEqual([chapter.title for chapter in task.edited_chapters], ["第三章", "第一章", "第二章"])

    def test_adds_empty_volume_before_selected_root_chapter(self):
        panel, _task = self.make_root_panel()
        panel.chapter_tree.setCurrentItem(panel.chapter_items[1])
        panel.insert_combo.setCurrentText(INSERT_BEFORE)

        panel.add_volume()

        self.assertEqual(panel.chapter_tree.topLevelItem(1).text(1), "新建分卷")
        self.assertEqual(panel.chapter_tree.topLevelItem(2).text(1), "第二章")

    def test_adds_chapter_inside_empty_volume_at_its_position(self):
        panel, _task = self.make_root_panel()
        panel.chapter_tree.setCurrentItem(panel.chapter_items[1])
        panel.insert_combo.setCurrentText(INSERT_BEFORE)
        panel.add_volume()
        panel.insert_combo.setCurrentText(INSERT_VOLUME_END)

        panel.add_chapter()

        self.assertEqual([chapter.title for chapter in panel.chapters], ["第一章", "新建章节", "第二章", "第三章"])
        self.assertEqual(panel.chapters[1].volume_title, "新建分卷")

    def test_merges_multiple_selected_chapters(self):
        panel, _task = self.make_root_panel()
        panel.chapter_tree.setCurrentItem(panel.chapter_items[0])
        panel.chapter_items[0].setSelected(True)
        panel.chapter_items[1].setSelected(True)

        panel.merge_selected_chapters()

        self.assertEqual([chapter.title for chapter in panel.chapters], ["第一章", "第三章"])
        self.assertIn("内容一", panel.chapters[0].content)
        self.assertIn("内容二", panel.chapters[0].content)

    def test_splits_current_chapter_at_cursor(self):
        panel, _task = self.make_root_panel()
        panel.chapter_tree.setCurrentItem(panel.chapter_items[0])
        panel.content_view.setPlainText("前半段。\n\n后半段。")
        cursor = panel.content_view.textCursor()
        cursor.setPosition(5)
        panel.content_view.setTextCursor(cursor)

        panel.split_current_chapter()

        self.assertEqual([chapter.title for chapter in panel.chapters[:2]], ["第一章", "第一章 下"])
        self.assertEqual(panel.chapters[0].content, "前半段。")
        self.assertEqual(panel.chapters[1].content, "后半段。")

    def test_syncs_order_after_tree_drag_structure_change(self):
        panel, _task = self.make_root_panel()
        moved = panel.chapter_tree.takeTopLevelItem(2)
        panel.chapter_tree.insertTopLevelItem(0, moved)

        panel.sync_from_dragged_tree()

        self.assertEqual([chapter.title for chapter in panel.chapters], ["第三章", "第一章", "第二章"])

    def test_replaces_text_across_book(self):
        panel, task = self.make_root_panel()

        count = panel.replace_text("内容", "正文", all_chapters=True)

        self.assertEqual(count, 3)
        self.assertEqual([chapter.content for chapter in panel.chapters], ["正文一", "正文二", "正文三"])
        self.assertEqual([chapter.content for chapter in task.edited_chapters], ["正文一", "正文二", "正文三"])

    def test_builds_quality_report_for_problem_chapters(self):
        panel, _task = self.make_root_panel()
        panel.chapters = [
            Chapter(1, "重复", ""),
            Chapter(2, "重复", "短"),
        ]
        panel.current_node_type = ""

        issues = {(row["issue"], row["chapter"]) for row in panel.build_quality_report()}

        self.assertIn(("空章节", "重复"), issues)
        self.assertIn(("重复标题", "重复"), issues)
        self.assertIn(("内容过短", "重复"), issues)

    def test_builds_recognition_report_from_source_lines(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        source = root / "book.txt"
        source.write_text("Chapter 1: Start\nBody\nPart II: Middle\n", encoding="utf-8")
        task = ConvertTask(source, root / "book.epub", "txt")
        panel = ChapterPreviewPanel()
        panel.set_task(task, AppConfig(output_dir=str(root)))

        report = panel.build_recognition_report()

        self.assertEqual([row["text"] for row in report], ["Chapter 1: Start", "Part II: Middle"])
        self.assertEqual(report[1]["kind"], "分卷")

    def test_inserts_marker_from_recognition_debugger(self):
        panel, _task = self.make_root_panel()
        panel.chapter_tree.setCurrentItem(panel.chapter_items[0])

        panel.insert_chapter_marker("新增识别章节")
        panel.insert_volume_marker("新增识别分卷")

        self.assertEqual(panel.chapters[1].title, "新增识别章节")
        self.assertIn("新增识别分卷", panel.volume_order)

    def test_builds_reading_preview_text(self):
        panel, _task = self.make_panel()
        panel.chapter_tree.setCurrentItem(panel.chapter_items[0])

        current_preview = panel.preview_text(False)
        full_preview = panel.preview_text(True)

        self.assertIn("第一卷", current_preview)
        self.assertIn("第一章", current_preview)
        self.assertIn("第三章", full_preview)


if __name__ == "__main__":
    unittest.main()
