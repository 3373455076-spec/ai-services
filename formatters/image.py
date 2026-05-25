"""Image (PNG) poster generator using Pillow."""

from PIL import Image, ImageDraw, ImageFont
import os
import textwrap
from config import OUTPUT_DIR, get_chinese_font_path

BG_COLOR = (34, 45, 65)
ACCENT_COLOR = (255, 180, 50)
TEXT_COLOR = (255, 255, 255)
SUB_COLOR = (200, 210, 220)
WIDTH = 1080
HEIGHT = 1920


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_path = get_chinese_font_path()
    if font_path:
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()


def create_poster(
    filename: str,
    main_title: str,
    subtitle: str,
    body_text: str,
    event_info: str = "",
    footer: str = "",
) -> str:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_title = _load_font(72)
    font_sub = _load_font(36)
    font_body = _load_font(32)
    font_info = _load_font(28)
    font_footer = _load_font(24)

    y = 180

    # Decorative top bar
    draw.rectangle([(0, 0), (WIDTH, 8)], fill=ACCENT_COLOR)

    # Main title
    lines = textwrap.wrap(main_title, width=12)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        tw = bbox[2] - bbox[0]
        x = (WIDTH - tw) // 2
        draw.text((x, y), line, fill=ACCENT_COLOR, font=font_title)
        y += bbox[3] - bbox[1] + 20
    y += 30

    # Decorative line
    draw.rectangle([(WIDTH // 2 - 100, y), (WIDTH // 2 + 100, y + 3)], fill=ACCENT_COLOR)
    y += 40

    # Subtitle
    if subtitle:
        lines = textwrap.wrap(subtitle, width=20)
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font_sub)
            tw = bbox[2] - bbox[0]
            x = (WIDTH - tw) // 2
            draw.text((x, y), line, fill=TEXT_COLOR, font=font_sub)
            y += bbox[3] - bbox[1] + 14
        y += 40

    # Body text
    if body_text:
        margin = 100
        max_chars = 22
        lines = []
        for paragraph in body_text.split("\n"):
            lines.extend(textwrap.wrap(paragraph, width=max_chars))
            lines.append("")
        for line in lines:
            if not line:
                y += 16
                continue
            draw.text((margin, y), line, fill=SUB_COLOR, font=font_body)
            y += 48
        y += 30

    # Event info
    if event_info:
        draw.rectangle([(60, y), (WIDTH - 60, y + 2)], fill=(80, 90, 110))
        y += 30
        for info_line in event_info.split("\n"):
            if info_line.strip():
                bbox = draw.textbbox((0, 0), info_line, font=font_info)
                tw = bbox[2] - bbox[0]
                x = (WIDTH - tw) // 2
                draw.text((x, y), info_line, fill=SUB_COLOR, font=font_info)
                y += bbox[3] - bbox[1] + 16

    # Footer
    if footer:
        footer_y = HEIGHT - 120
        draw.rectangle([(0, HEIGHT - 8), (WIDTH, HEIGHT)], fill=ACCENT_COLOR)
        bbox = draw.textbbox((0, 0), footer, font=font_footer)
        tw = bbox[2] - bbox[0]
        x = (WIDTH - tw) // 2
        draw.text((x, footer_y), footer, fill=SUB_COLOR, font=font_footer)

    path = os.path.join(OUTPUT_DIR, filename)
    img.save(path, "PNG")
    return path
