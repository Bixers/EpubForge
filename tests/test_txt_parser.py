from pathlib import Path
import tempfile
import unittest

from app.core.parser.txt_parser import TxtParser


class TxtParserTest(unittest.TestCase):
    def test_txt_parser_reads_gbk_and_detects_chapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "中文小说.txt"
            source.write_bytes("第一章 开始\n内容".encode("gbk"))

            document = TxtParser().parse(source)

            self.assertIn(document.metadata["source_encoding"].lower(), {"gb18030", "gbk"})
            self.assertEqual(document.title, "中文小说")
            self.assertEqual(document.chapters[0].title, "第一章 开始")
            self.assertIn("内容", document.chapters[0].content)

    def test_txt_parser_does_not_misdetect_short_gbk_as_big5(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "short.txt"
            source.write_bytes("第一章\n正文".encode("gbk"))

            document = TxtParser().parse(source)

            self.assertEqual(document.chapters[0].title, "第一章")
            self.assertEqual(document.chapters[0].content, "正文")


if __name__ == "__main__":
    unittest.main()
