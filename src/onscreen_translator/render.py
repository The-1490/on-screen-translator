"""Draw English text over the original text boxes."""
from PIL import Image, ImageDraw, ImageFont


def _font(size):
    for n in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            pass
    return ImageFont.load_default()


def overlay(img, items):
    """items: [((x,y,w,h), english_text)]"""
    out = img.convert("RGB").copy()
    d = ImageDraw.Draw(out)
    for (x, y, w, h), text in items:
        size = max(10, int(h * 0.8))
        f = _font(size)
        while size > 8 and d.textlength(text, font=f) > max(w, 40) * 1.6:
            size -= 1
            f = _font(size)
        tw = d.textlength(text, font=f)
        d.rectangle([x - 2, y - 2, x + max(w, tw) + 2, y + h + 2], fill=(20, 20, 20))
        d.text((x, y), text, font=f, fill=(255, 255, 255))
    return out
