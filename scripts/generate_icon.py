from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "app" / "assets"
PNG_PATH = ASSETS / "app_icon.png"
ICO_PATH = ASSETS / "app.ico"


def rounded_rectangle(draw: ImageDraw.ImageDraw, box, radius: int, fill, outline=None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_icon(size: int = 1024) -> Image.Image:
    scale = size / 1024
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    radius = int(180 * scale)
    shadow_draw.rounded_rectangle(
        [int(80 * scale), int(92 * scale), int(944 * scale), int(956 * scale)],
        radius=radius,
        fill=(15, 23, 42, 90),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(int(24 * scale)))
    image.alpha_composite(shadow)

    draw = ImageDraw.Draw(image)
    rounded_rectangle(
        draw,
        [int(72 * scale), int(64 * scale), int(952 * scale), int(944 * scale)],
        radius,
        fill=(20, 99, 255, 255),
    )
    rounded_rectangle(
        draw,
        [int(108 * scale), int(100 * scale), int(916 * scale), int(908 * scale)],
        int(144 * scale),
        fill=(37, 99, 235, 255),
        outline=(96, 165, 250, 255),
        width=int(8 * scale),
    )

    # Open-book body.
    left_page = [
        (int(206 * scale), int(260 * scale)),
        (int(486 * scale), int(202 * scale)),
        (int(486 * scale), int(710 * scale)),
        (int(206 * scale), int(780 * scale)),
    ]
    right_page = [
        (int(538 * scale), int(202 * scale)),
        (int(818 * scale), int(260 * scale)),
        (int(818 * scale), int(780 * scale)),
        (int(538 * scale), int(710 * scale)),
    ]
    draw.polygon(left_page, fill=(255, 255, 255, 255))
    draw.polygon(right_page, fill=(239, 246, 255, 255))
    draw.line(
        [(int(512 * scale), int(206 * scale)), (int(512 * scale), int(724 * scale))],
        fill=(29, 78, 216, 255),
        width=int(18 * scale),
    )
    draw.line(
        [(int(250 * scale), int(344 * scale)), (int(430 * scale), int(306 * scale))],
        fill=(96, 165, 250, 255),
        width=int(14 * scale),
    )
    draw.line(
        [(int(250 * scale), int(430 * scale)), (int(430 * scale), int(392 * scale))],
        fill=(96, 165, 250, 255),
        width=int(14 * scale),
    )
    draw.line(
        [(int(594 * scale), int(306 * scale)), (int(774 * scale), int(344 * scale))],
        fill=(59, 130, 246, 255),
        width=int(14 * scale),
    )
    draw.line(
        [(int(594 * scale), int(392 * scale)), (int(774 * scale), int(430 * scale))],
        fill=(59, 130, 246, 255),
        width=int(14 * scale),
    )

    # Forge mark: anvil base and spark.
    draw.rounded_rectangle(
        [int(334 * scale), int(706 * scale), int(690 * scale), int(790 * scale)],
        radius=int(26 * scale),
        fill=(37, 99, 235, 255),
    )
    draw.polygon(
        [
            (int(408 * scale), int(790 * scale)),
            (int(616 * scale), int(790 * scale)),
            (int(660 * scale), int(858 * scale)),
            (int(364 * scale), int(858 * scale)),
        ],
        fill=(29, 78, 216, 255),
    )
    spark = [
        (int(512 * scale), int(540 * scale)),
        (int(546 * scale), int(640 * scale)),
        (int(646 * scale), int(674 * scale)),
        (int(546 * scale), int(708 * scale)),
        (int(512 * scale), int(808 * scale)),
        (int(478 * scale), int(708 * scale)),
        (int(378 * scale), int(674 * scale)),
        (int(478 * scale), int(640 * scale)),
    ]
    draw.polygon(spark, fill=(250, 204, 21, 255))
    draw.polygon(
        [
            (int(512 * scale), int(602 * scale)),
            (int(532 * scale), int(658 * scale)),
            (int(588 * scale), int(678 * scale)),
            (int(532 * scale), int(698 * scale)),
            (int(512 * scale), int(754 * scale)),
            (int(492 * scale), int(698 * scale)),
            (int(436 * scale), int(678 * scale)),
            (int(492 * scale), int(658 * scale)),
        ],
        fill=(255, 255, 255, 230),
    )
    return image


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    base = draw_icon(1024)
    base.save(PNG_PATH)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    icons = [draw_small_icon(size) if size <= 32 else base.resize((size, size), Image.Resampling.LANCZOS) for size in sizes]
    icons[-1].save(ICO_PATH, format="ICO", sizes=[(size, size) for size in sizes], append_images=icons[:-1])
    print(f"wrote {PNG_PATH}")
    print(f"wrote {ICO_PATH}")


def draw_small_icon(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    margin = max(1, round(size * 0.08))
    radius = max(3, round(size * 0.18))
    draw.rounded_rectangle(
        [margin, margin, size - margin - 1, size - margin - 1],
        radius=radius,
        fill=(20, 99, 255, 255),
    )
    stroke = max(1, round(size * 0.08))
    center = size // 2
    top = round(size * 0.26)
    bottom = round(size * 0.75)
    left = round(size * 0.22)
    right = round(size * 0.78)
    page_color = (255, 255, 255, 255)
    draw.line([(center, top), (center, bottom)], fill=page_color, width=stroke)
    draw.line([(left, top + stroke), (center, top), (center, bottom), (left, bottom - stroke)], fill=page_color, width=stroke)
    draw.line([(center, top), (right, top + stroke), (right, bottom - stroke), (center, bottom)], fill=page_color, width=stroke)
    spark = max(2, round(size * 0.12))
    draw.rectangle(
        [center - spark // 2, round(size * 0.58), center + spark // 2, round(size * 0.58) + spark],
        fill=(250, 204, 21, 255),
    )
    return image


if __name__ == "__main__":
    main()
