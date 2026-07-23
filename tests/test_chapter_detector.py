import unittest

from app.core.chapter.chapter_detector import ChapterDetector


class ChapterDetectorTest(unittest.TestCase):
    def test_detects_chinese_and_english_chapters(self):
        text = "\n".join(
            [
                "序章",
                "开场内容",
                "第一章 开始",
                "正文内容",
                "CHAPTER 2 Next",
                "English content",
            ]
        )

        chapters = ChapterDetector().detect(text)

        self.assertEqual([chapter.title for chapter in chapters], ["序章", "第一章 开始", "CHAPTER 2 Next"])
        self.assertEqual(chapters[1].content, "正文内容")

    def test_none_rule_keeps_single_chapter(self):
        chapters = ChapterDetector(rule="none").detect("第一章\n内容")

        self.assertEqual(len(chapters), 1)
        self.assertEqual(chapters[0].title, "正文")


if __name__ == "__main__":
    unittest.main()
