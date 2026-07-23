from contextlib import closing, redirect_stdout
import io
from pathlib import Path
import sqlite3
import tempfile
import unittest

from app.cli import main as cli_main
from app.core.batch.task_manager import TaskManager
from app.core.models import AppConfig
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


if __name__ == "__main__":
    unittest.main()
