from pathlib import Path
import tempfile
import unittest
import zipfile

from app.core.epub.epub_builder import EpubBuilder
from app.core.epub.validator import EpubValidator
from app.core.models import BookDocument, Chapter


class EpubBuilderTest(unittest.TestCase):
    def test_epub_builder_writes_valid_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "demo.epub"
            document = BookDocument(
                title="测试书",
                author="作者",
                chapters=[Chapter(1, "第一章", "正文 & <内容>")],
            )

            EpubBuilder().build(document, output)
            ok, errors = EpubValidator().validate(output)

            self.assertTrue(ok, errors)
            with zipfile.ZipFile(output, "r") as archive:
                self.assertEqual(archive.namelist()[0], "mimetype")
                chapter = archive.read("OEBPS/chapters/chapter001.xhtml").decode("utf-8")
                self.assertIn("正文 &amp; &lt;内容&gt;", chapter)

    def test_validator_reports_missing_epubcheck_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "demo.epub"
            document = BookDocument(
                title="测试书",
                chapters=[Chapter(1, "第一章", "正文")],
            )
            EpubBuilder().build(document, output)

            ok, errors = EpubValidator().validate(output, str(Path(tmp) / "missing-epubcheck.jar"))

            self.assertFalse(ok)
            self.assertIn("EPUBCheck 路径不存在", errors[0])

    def test_nav_groups_chapters_by_volume(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "volume.epub"
            document = BookDocument(
                title="分卷书",
                chapters=[
                    Chapter(1, "第一章", "正文", volume_title="第一卷"),
                    Chapter(2, "第二章", "正文", volume_title="第一卷"),
                    Chapter(3, "第三章", "正文", volume_title="第二卷"),
                ],
            )

            EpubBuilder().build(document, output)

            with zipfile.ZipFile(output, "r") as archive:
                nav = archive.read("OEBPS/nav.xhtml").decode("utf-8")
            self.assertIn("<span>第一卷</span>", nav)
            self.assertIn("<span>第二卷</span>", nav)
            self.assertIn("chapter003.xhtml", nav)


if __name__ == "__main__":
    unittest.main()
