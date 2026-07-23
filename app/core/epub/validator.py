from __future__ import annotations

import subprocess
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
    def validate(self, path: str | Path, epubcheck_path: str = "") -> tuple[bool, list[str]]:
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
        if not errors:
            errors.extend(self._run_epubcheck(epub_path, epubcheck_path))
        return not errors, errors

    def _run_epubcheck(self, epub_path: Path, epubcheck_path: str) -> list[str]:
        tool_path = Path(epubcheck_path.strip()) if epubcheck_path.strip() else None
        if tool_path is None:
            return []
        if not tool_path.exists():
            return [f"EPUBCheck 路径不存在：{tool_path}"]
        if tool_path.suffix.lower() == ".jar":
            command = ["java", "-jar", str(tool_path), str(epub_path)]
        else:
            command = [str(tool_path), str(epub_path)]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )
        except FileNotFoundError as exc:
            return [f"无法运行 EPUBCheck：{exc}"]
        except subprocess.TimeoutExpired:
            return ["EPUBCheck 校验超时"]
        output = "\n".join(part.strip() for part in [result.stdout, result.stderr] if part.strip())
        if result.returncode == 0:
            return []
        return [output or f"EPUBCheck 返回码 {result.returncode}"]
