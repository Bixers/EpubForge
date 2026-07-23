from __future__ import annotations

from pathlib import Path

try:
    from charset_normalizer import from_bytes
except ImportError:  # pragma: no cover - exercised only without optional dependency
    from_bytes = None


def decode_text_file(path: str | Path) -> tuple[str, str]:
    return decode_bytes(Path(path).read_bytes())


def decode_bytes(raw: bytes) -> tuple[str, str]:
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig"), "utf-8-sig"
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16"), "utf-16"

    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass

    candidates: list[tuple[str, str]] = []
    for encoding in ("gb18030", "gbk", "big5", "big5hkscs"):
        try:
            candidates.append((raw.decode(encoding), encoding))
        except UnicodeDecodeError:
            continue

    if from_bytes is not None:
        result = from_bytes(raw).best()
        if result is not None and result.encoding:
            candidates.append((str(result), result.encoding))

    if candidates:
        return max(candidates, key=lambda item: readability_score(item[0]))
    return raw.decode("utf-8", errors="replace"), "utf-8-replace"


def readability_score(text: str) -> int:
    cjk = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    ascii_printable = sum(1 for char in text if char in "\n\t\r" or " " <= char <= "~")
    punctuation = sum(1 for char in text if char in "，。！？；：“”‘’、（）《》")
    suspicious = sum(
        1
        for char in text
        if char == "\ufffd"
        or "\u2e80" <= char <= "\u2eff"
        or "\ue000" <= char <= "\uf8ff"
    )
    return cjk * 4 + punctuation * 2 + ascii_printable - suspicious * 8
