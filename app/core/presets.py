from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CssTemplate:
    name: str
    css: str


@dataclass(frozen=True, slots=True)
class ConversionPreset:
    name: str
    chapter_rule: str
    custom_chapter_regex: str
    fixed_chapter_chars: int
    css_template: str


CSS_TEMPLATES: dict[str, CssTemplate] = {
    "默认阅读": CssTemplate(
        "默认阅读",
        """body {
  font-family: "Microsoft YaHei", "Noto Serif CJK SC", serif;
  line-height: 1.8;
  margin: 1.2em;
}
h1 {
  font-size: 1.6em;
  margin-bottom: 1.2em;
}
p {
  text-indent: 2em;
  margin: 0.4em 0;
}
""",
    ),
    "网文舒适": CssTemplate(
        "网文舒适",
        """body {
  font-family: "Microsoft YaHei", "Noto Serif CJK SC", serif;
  line-height: 1.9;
  margin: 1em 1.15em;
}
h1 {
  font-size: 1.45em;
  text-align: center;
  margin: 1.4em 0 1.2em;
}
p {
  text-indent: 2em;
  margin: 0.45em 0;
}
""",
    ),
    "出版简洁": CssTemplate(
        "出版简洁",
        """body {
  font-family: "Noto Serif CJK SC", "Songti SC", serif;
  line-height: 1.75;
  margin: 1.4em;
}
h1 {
  font-size: 1.5em;
  font-weight: 700;
  margin: 1.5em 0 1.3em;
}
p {
  text-indent: 2em;
  margin: 0.5em 0;
}
""",
    ),
    "紧凑排版": CssTemplate(
        "紧凑排版",
        """body {
  font-family: "Microsoft YaHei", "Noto Serif CJK SC", serif;
  line-height: 1.65;
  margin: 0.9em;
}
h1 {
  font-size: 1.35em;
  margin-bottom: 1em;
}
p {
  text-indent: 2em;
  margin: 0.25em 0;
}
""",
    ),
}


CONVERSION_PRESETS: dict[str, ConversionPreset] = {
    "网文 TXT": ConversionPreset("网文 TXT", "default", "", 6000, "网文舒适"),
    "英文小说": ConversionPreset("英文小说", "default", "", 6000, "默认阅读"),
    "Markdown 文档": ConversionPreset("Markdown 文档", "default", "", 6000, "出版简洁"),
    "固定字数兜底": ConversionPreset("固定字数兜底", "fixed_size", "", 6000, "网文舒适"),
    "不自动分章": ConversionPreset("不自动分章", "none", "", 6000, "默认阅读"),
}


def css_template_names() -> list[str]:
    return list(CSS_TEMPLATES)


def conversion_preset_names() -> list[str]:
    return list(CONVERSION_PRESETS)
