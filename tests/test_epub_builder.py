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


if __name__ == "__main__":
    unittest.main()
