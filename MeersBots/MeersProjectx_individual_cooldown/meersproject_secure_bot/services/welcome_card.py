from __future__ import annotations

import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

BACKGROUND_PATH = Path(__file__).resolve().parent.parent / 'assets' / 'welcome_background.png'
CARD_SIZE = (1024, 356)
AVATAR_SIZE = 224
AVATAR_POSITION = (57, 65)


def _font(size: int, bold: bool = False):
    # Absolute paths are important: Pillow may not resolve font filenames on Windows.
    candidates = (
        ['C:/Windows/Fonts/arialbd.ttf', 'C:/Windows/Fonts/segoeuib.ttf',
         '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 'DejaVuSans-Bold.ttf']
        if bold else
        ['C:/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/segoeui.ttf',
         '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'DejaVuSans.ttf']
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    raise RuntimeError('Не найден шрифт Arial, Segoe UI или DejaVu Sans для welcome-карточки')


def generate_welcome_card(avatar_bytes: bytes, member_count: int | None = None) -> bytes:
    """Generate the Discord welcome card with a framed, readable text panel."""
    with Image.open(io.BytesIO(avatar_bytes)) as source:
        avatar = ImageOps.fit(source.convert('RGBA'), (AVATAR_SIZE, AVATAR_SIZE), method=Image.Resampling.LANCZOS)
    with Image.open(BACKGROUND_PATH) as background:
        canvas = background.convert('RGBA').resize(CARD_SIZE, Image.Resampling.LANCZOS)

    panel_box = (329, 42, 983, 309)
    panel_layer = Image.new('RGBA', CARD_SIZE, (0, 0, 0, 0))
    panel_draw = ImageDraw.Draw(panel_layer)
    panel_draw.rounded_rectangle(panel_box, radius=29, fill=(10, 6, 27, 190))
    canvas = Image.alpha_composite(canvas, panel_layer)

    border = Image.new('RGBA', CARD_SIZE, (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle(panel_box, radius=29, outline=(190, 148, 255, 220), width=4)
    canvas = Image.alpha_composite(canvas, border.filter(ImageFilter.GaussianBlur(12)))
    canvas = Image.alpha_composite(canvas, border.filter(ImageFilter.GaussianBlur(4)))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(panel_box, radius=29, outline=(223, 205, 255, 245), width=3)

    cx = AVATAR_POSITION[0] + AVATAR_SIZE // 2
    cy = AVATAR_POSITION[1] + AVATAR_SIZE // 2
    radius = AVATAR_SIZE // 2
    halo = Image.new('RGBA', CARD_SIZE, (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.ellipse((cx-radius-9, cy-radius-9, cx+radius+9, cy+radius+9), fill=(255, 255, 255, 245))
    canvas = Image.alpha_composite(canvas, halo.filter(ImageFilter.GaussianBlur(17)))
    canvas = Image.alpha_composite(canvas, halo.filter(ImageFilter.GaussianBlur(6)))
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((cx-radius-6, cy-radius-6, cx+radius+6, cy+radius+6), fill='white')
    mask = Image.new('L', (AVATAR_SIZE, AVATAR_SIZE))
    ImageDraw.Draw(mask).ellipse((0, 0, AVATAR_SIZE-1, AVATAR_SIZE-1), fill=255)
    canvas.paste(avatar, AVATAR_POSITION, mask)
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((cx-radius-2, cy-radius-2, cx+radius+2, cy+radius+2), outline='white', width=4)

    x = 363
    heading = 'Welcome to'
    count_label = f'Member #{member_count:,}' if member_count is not None else 'Member'
    heading_font = _font(66, True)
    count_size = 60
    while count_size > 30 and draw.textbbox((0, 0), count_label, font=_font(count_size, True))[2] > 574:
        count_size -= 2
    count_font = _font(count_size, True)
    draw.text((x, 81), heading, font=heading_font, fill=(255, 255, 255), stroke_width=1, stroke_fill=(215, 200, 255))
    draw.text((x, 174), count_label, font=count_font, fill=(242, 230, 255), stroke_width=1, stroke_fill=(110, 65, 170))
    draw.rounded_rectangle((x+3, 267, 730, 271), radius=2, fill=(217, 188, 255))

    signature = 'MeersProject'
    sig_font = _font(27, True)
    sig_width = draw.textbbox((0, 0), signature, font=sig_font)[2]
    draw.text((CARD_SIZE[0] - sig_width - 27, CARD_SIZE[1] - 39), signature,
              font=sig_font, fill=(250, 246, 255), stroke_width=1, stroke_fill=(84, 52, 128))
    output = io.BytesIO()
    canvas.convert('RGB').save(output, format='PNG', optimize=True)
    return output.getvalue()
