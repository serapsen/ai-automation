import os
from typing import Dict, Tuple, List

from PIL import Image, ImageDraw, ImageFont

from src.utils.logger import get_logger

logger = get_logger("post_processor")


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _hex_to_rgb(hx: str):
    h = hx.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _get_font(size: int):
    fp = os.getenv("FONT_PATH")
    if fp and os.path.isfile(fp):
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            pass
    candidates = [
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\arialuni.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def overlay_text(in_path: str, text: str, out_path: str, color_hex: str | None):
    im = Image.open(in_path).convert("RGBA")
    w, h = im.size
    draw = ImageDraw.Draw(im)
    pad = max(16, w // 100)
    font = _get_font(max(20, w // 22))
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        tw, th = draw.textsize(text, font=font)
    box_h = th + pad * 2
    box = Image.new("RGBA", (w, box_h), (0, 0, 0, 140))
    im.alpha_composite(box, (0, h - box_h))
    color = (255, 255, 255)
    if color_hex:
        try:
            color = _hex_to_rgb(color_hex)
        except Exception:
            pass
    draw = ImageDraw.Draw(im)
    draw.text((pad, h - box_h + pad), text, fill=color + (255,), font=font)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    im.convert("RGB").save(out_path, format="PNG")


def overlay_logo(in_path: str, logo_path: str | None, out_path: str):
    if not logo_path or not os.path.isfile(logo_path):
        if in_path != out_path:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            Image.open(in_path).convert("RGB").save(out_path, format="PNG")
        return
    base = Image.open(in_path).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")
    bw, bh = base.size
    target_w = max(64, bw // 8)
    ratio = target_w / logo.width
    logo = logo.resize((target_w, int(logo.height * ratio)), Image.LANCZOS)
    margin = max(10, bw // 100)
    base.alpha_composite(logo, (margin, margin))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    base.convert("RGB").save(out_path, format="PNG")


PROHIBITED = {"fake", "scam", "illegal", "banned"}


def moderate_text(text: str) -> List[str]:
    lower = text.lower()
    found = [w for w in PROHIBITED if w in lower]
    return found


def brand_compliance_summary(text_color_hex: str | None, logo_present: bool) -> Dict:
    return {
        "text_color": text_color_hex or "#FFFFFF",
        "logo_present": bool(logo_present),
        "checks": [
            {"rule": "brand_color_used", "passed": bool(text_color_hex)},
            {"rule": "logo_overlay", "passed": bool(logo_present)},
        ],
    }
