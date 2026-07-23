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

    def test_detects_multiple_title_styles(self):
        text = "\n".join(
            [
                "1. 数字标题",
                "内容一",
                "Chapter 2: English",
                "content",
                "卷三 风起",
                "内容三",
            ]
        )

        chapters = ChapterDetector().detect(text)

        self.assertEqual([chapter.title for chapter in chapters], ["1. 数字标题", "Chapter 2: English", "正文"])
        self.assertEqual(chapters[2].volume_title, "卷三 风起")

    def test_preserves_empty_consecutive_chapters(self):
        chapters = ChapterDetector().detect("第一章\n第二章\n第二章内容")

        self.assertEqual([chapter.title for chapter in chapters], ["第一章", "第二章"])
        self.assertEqual(chapters[0].content, "")

    def test_body_heading_after_preface_still_splits(self):
        chapters = ChapterDetector().detect("前言\n说明\n正文\n内容")

        self.assertEqual([chapter.title for chapter in chapters], ["前言", "正文"])

    def test_detects_volume_and_assigns_following_chapters(self):
        text = "\n".join(
            [
                "第一卷 地球往事",
                "第一章 疯狂年代",
                "内容一",
                "第二章 寂静的春天",
                "内容二",
                "第二卷 黑暗森林",
                "第一章 面壁者",
                "内容三",
            ]
        )

        chapters = ChapterDetector().detect(text)

        self.assertEqual([chapter.title for chapter in chapters], ["第一章 疯狂年代", "第二章 寂静的春天", "第一章 面壁者"])
        self.assertEqual([chapter.volume_title for chapter in chapters], ["第一卷 地球往事", "第一卷 地球往事", "第二卷 黑暗森林"])


if __name__ == "__main__":
    unittest.main()
