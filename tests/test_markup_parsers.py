from pathlib import Path
import tempfile
import unittest
import zipfile

from app.core.epub.epub_builder import EpubBuilder
from app.core.epub.validator import EpubValidator
from app.core.parser.html_parser import HtmlParser
from app.core.parser.markdown_parser import MarkdownParser


class MarkupParserTest(unittest.TestCase):
    def test_markdown_parser_splits_headings_and_keeps_basic_markup(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "demo.md"
            source.write_text(
                "# 第一章\n\n正文 **加粗** 和 `code`\n\n- 条目\n\n# 第二章\n内容",
                encoding="utf-8",
            )

            document = MarkdownParser().parse(source)

            self.assertEqual([chapter.title for chapter in document.chapters], ["第一章", "第二章"])
            self.assertIn("<strong>加粗</strong>", document.chapters[0].content)
            self.assertIn("<li>条目</li>", document.chapters[0].content)

    def test_html_parser_uses_document_title_and_splits_h1(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "demo.html"
            source.write_text(
                "<html><head><title>书名</title></head><body>"
                "<h1>第一章</h1><p>正文 <strong>加粗</strong></p>"
                "<script>alert(1)</script><h1>第二章</h1><ul><li>条目</li></ul>"
                "</body></html>",
                encoding="utf-8",
            )

            document = HtmlParser().parse(source)

            self.assertEqual(document.title, "书名")
            self.assertEqual([chapter.title for chapter in document.chapters], ["第一章", "第二章"])
            self.assertIn("<strong>加粗</strong>", document.chapters[0].content)
            self.assertNotIn("alert", document.chapters[0].content)

    def test_markup_epub_contains_clean_xhtml(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "demo.md"
            output = root / "demo.epub"
            source.write_text("# 第一章\n\n正文 **加粗**", encoding="utf-8")
            document = MarkdownParser().parse(source)

            EpubBuilder().build(document, output)
            ok, errors = EpubValidator().validate(output)

            self.assertTrue(ok, errors)
            with zipfile.ZipFile(output) as archive:
                chapter = archive.read("OEBPS/chapters/chapter001.xhtml").decode("utf-8")
            self.assertIn("<strong>加粗</strong>", chapter)


if __name__ == "__main__":
    unittest.main()
