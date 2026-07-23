from __future__ import annotations

import zipfile
from pathlib import Path


REQUIRED_FILES = {
    "mimetype",
    "META-INF/container.xml",
    "OEBPS/content.opf",
    "OEBPS/nav.xhtml",
    "OEBPS/styles/style.css",
}


class EpubValidator:
    def validate(self, path: str | Path) -> tuple[bool, list[str]]:
        epub_path = Path(path)
        errors: list[str] = []
        if not epub_path.exists():
            return False, ["EPUB 文件不存在"]
        try:
            with zipfile.ZipFile(epub_path, "r") as archive:
                names = archive.namelist()
                if not names or names[0] != "mimetype":
                    errors.append("mimetype 必须是压缩包第一个文件")
                info = archive.getinfo("mimetype")
                if info.compress_type != zipfile.ZIP_STORED:
                    errors.append("mimetype 必须使用无压缩方式写入")
                missing = sorted(REQUIRED_FILES - set(names))
                if missing:
                    errors.append("缺少 EPUB 必需文件：" + ", ".join(missing))
                chapter_names = [name for name in names if name.startswith("OEBPS/chapters/")]
                if not chapter_names:
                    errors.append("EPUB 至少需要一个章节文件")
        except KeyError:
            errors.append("缺少 mimetype 文件")
        except zipfile.BadZipFile:
            errors.append("EPUB 不是有效的 ZIP 文件")
        return not errors, errors

