from contextlib import closing, redirect_stdout
import io
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile

from app.cli import main as cli_main
from app.core.batch.task_manager import TaskManager
from app.core.models import AppConfig, Chapter
from app.storage.task_repository import TaskRepository


class TaskManagerTest(unittest.TestCase):
    def test_keeps_folder_structure_when_importing_from_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "books" / "novel"
            source_dir.mkdir(parents=True)
            source = source_dir / "demo.txt"
            source.write_text("正文", encoding="utf-8")
            output_dir = root / "output"
            manager = TaskManager(
                AppConfig(output_dir=str(output_dir), keep_folder_structure=True),
                TaskRepository(root / "tasks.sqlite3"),
            )

            task = manager.create_task(source, base_dir=root / "books")

            self.assertEqual(task.output_path, output_dir / "novel" / "demo.epub")

    def test_avoids_existing_output_path_before_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "demo.txt"
            source.write_text("正文", encoding="utf-8")
            output_dir = root / "output"
            output_dir.mkdir()
            (output_dir / "demo.epub").write_text("exists", encoding="utf-8")
            manager = TaskManager(
                AppConfig(output_dir=str(output_dir), overwrite_existing=False),
                TaskRepository(root / "tasks.sqlite3"),
            )

            task = manager.create_task(source)

            self.assertEqual(task.output_path.name, "demo_1.epub")

    def test_persists_task_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "tasks.sqlite3"
            source = root / "demo.txt"
            source.write_text("正文", encoding="utf-8")
            repository = TaskRepository(db_path)
            manager = TaskManager(AppConfig(output_dir=str(root / "output")), repository)
            task = manager.create_task(source)
            task.title = "自定义书名"
            task.author = "作者"
            repository.save_task(task)

            with closing(sqlite3.connect(db_path)) as conn:
                row = conn.execute(
                    "SELECT title, author FROM convert_tasks WHERE id = ?",
                    (task.id,),
                ).fetchone()

            self.assertEqual(row, ("自定义书名", "作者"))

    def test_lists_recent_tasks_from_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repository = TaskRepository(root / "tasks.sqlite3")
            manager = TaskManager(AppConfig(output_dir=str(root / "output")), repository)
            source = root / "demo.txt"
            source.write_text("正文", encoding="utf-8")
            task = manager.create_task(source)
            task.title = "历史书名"
            task.file_size = 123
            repository.save_task(task)

            recent = repository.list_recent_tasks()

            self.assertEqual(len(recent), 1)
            self.assertEqual(recent[0].title, "历史书名")
            self.assertEqual(recent[0].file_size, 123)

    def test_cli_converts_txt_without_gui_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "demo.txt"
            source.write_text("第一章\n正文", encoding="utf-8")
            output_dir = root / "out"

            with redirect_stdout(io.StringIO()):
                exit_code = cli_main([str(source), "-o", str(output_dir)])

            self.assertEqual(exit_code, 0)
            self.assertTrue((output_dir / "demo.epub").exists())

    def test_cli_converts_markdown_and_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markdown = root / "demo.md"
            html = root / "page.html"
            markdown.write_text("# 第一章\n正文", encoding="utf-8")
            html.write_text("<h1>标题</h1><p>内容</p>", encoding="utf-8")
            output_dir = root / "out"

            with redirect_stdout(io.StringIO()):
                exit_code = cli_main([str(markdown), str(html), "-o", str(output_dir)])

            self.assertEqual(exit_code, 0)
            self.assertTrue((output_dir / "demo.epub").exists())
            self.assertTrue((output_dir / "page.epub").exists())

    def test_conversion_uses_edited_chapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "demo.txt"
            source.write_text("第一章\n原始内容", encoding="utf-8")
            manager = TaskManager(
                AppConfig(output_dir=str(root / "out")),
                TaskRepository(root / "tasks.sqlite3"),
            )
            task = manager.create_task(source)
            task.edited_chapters = [Chapter(1, "改后章节", "编辑后的内容")]

            manager.convert_task(task)

            self.assertEqual(task.status, "完成")
            epub_path = root / "out" / "demo.epub"
            with zipfile.ZipFile(epub_path) as archive:
                chapter = archive.read("OEBPS/chapters/chapter001.xhtml").decode("utf-8")
            self.assertIn("改后章节", chapter)
            self.assertIn("编辑后的内容", chapter)

    def test_conversion_logs_preflight_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "demo.txt"
            source.write_text("正文", encoding="utf-8")
            manager = TaskManager(
                AppConfig(output_dir=str(root / "out")),
                TaskRepository(root / "tasks.sqlite3"),
            )
            task = manager.create_task(source)
            task.edited_chapters = [
                Chapter(1, "重复", ""),
                Chapter(2, "重复", "短"),
            ]

            manager.convert_task(task)

            log_text = "\n".join(task.logs)
            self.assertIn("转换前检查：重复 内容为空", log_text)
            self.assertIn("转换前检查：重复章节标题：重复", log_text)
            self.assertIn("转换前检查：重复 内容过短", log_text)


if __name__ == "__main__":
    unittest.main()
