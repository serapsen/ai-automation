import base64
import io
import os
import random
import json
import requests
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageFont

from src.utils.logger import get_logger

logger = get_logger("asset_generation")


ASPECT_SIZES = {
    "1:1": (1024, 1024),
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
}

# Supported image generation models for OpenAI Images API
SUPPORTED_IMAGE_MODELS = {"gpt-image-1", "dall-e-3"}


def _hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _placeholder_image(product: str, size: Tuple[int, int], primary_color: str | None) -> Image.Image:
    w, h = size
    if primary_color:
        try:
            base = _hex_to_rgb(primary_color)
        except Exception:
            base = (80, 80, 80)
    else:
        base = (80, 80, 80)
    im = Image.new("RGB", (w, h), base)
    draw = ImageDraw.Draw(im)
    for y in range(0, h, 20):
        shade = int(30 + 40 * random.random())
        draw.line([(0, y), (w, y)], fill=(base[0]+shade if base[0]+shade <=255 else 255, base[1], base[2]))
    font = ImageFont.load_default()
    text = product
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        tw, th = draw.textsize(text, font=font)
    draw.text(((w - tw) // 2, (h - th) // 2), text, fill=(255, 255, 255), font=font)
    return im


def _resize_to_aspect(im: Image.Image, target: Tuple[int, int]) -> Image.Image:
    tw, th = target
    src_ratio = im.width / im.height
    tgt_ratio = tw / th
    if abs(src_ratio - tgt_ratio) < 1e-3:
        return im.resize((tw, th), Image.LANCZOS)
    if src_ratio > tgt_ratio:
        new_w = int(im.height * tgt_ratio)
        x0 = (im.width - new_w) // 2
        im_c = im.crop((x0, 0, x0 + new_w, im.height))
        return im_c.resize((tw, th), Image.LANCZOS)
    else:
        new_h = int(im.width / tgt_ratio)
        y0 = (im.height - new_h) // 2
        im_c = im.crop((0, y0, im.width, y0 + new_h))
        return im_c.resize((tw, th), Image.LANCZOS)


def _save_image(im: Image.Image, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, format="PNG")


def _save_meta(path: str, meta: Dict):
    try:
        with open(path + ".meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f)
    except Exception:
        pass


def _try_azure_openai_generate(prompt: str, size_square: int) -> Image.Image | None:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT") or os.getenv("DEPLOYMENT_NAME")
    api_version = os.getenv("OPENAI_API_VERSION", "2024-04-01-preview")
    style = os.getenv("AZURE_OPENAI_IMAGE_STYLE", "vivid")
    quality = os.getenv("AZURE_OPENAI_IMAGE_QUALITY", "standard")
    if not endpoint or not api_key or not deployment:
        return None
    try:
        from openai import AzureOpenAI
    except Exception as e:
        logger.warning("openai package not available for Azure OpenAI: %s", e)
        return None
    try:
        client = AzureOpenAI(api_version=api_version, azure_endpoint=endpoint, api_key=api_key)
        resp = client.images.generate(model=deployment, prompt=prompt, size=f"{size_square}x{size_square}", n=1, style=style, quality=quality)
        # Prefer b64 if available; otherwise download URL
        try:
            b64 = resp.data[0].b64_json
            if b64:
                img_bytes = base64.b64decode(b64)
                return Image.open(io.BytesIO(img_bytes)).convert("RGB")
        except Exception:
            pass
        try:
            url = resp.data[0].url
            if url:
                r = requests.get(url, timeout=30)
                r.raise_for_status()
                return Image.open(io.BytesIO(r.content)).convert("RGB")
        except Exception:
            pass
        return None
    except Exception as e:
        logger.error("Azure OpenAI image generation failed: %s", e)
        return None


def _try_openai_generate(prompt: str, size_square: int, api_key: str | None, model: str | None) -> Image.Image | None:
    if not api_key:
        return None
    try:
        from openai import OpenAI
    except Exception as e:
        logger.warning("openai package not available: %s", e)
        return None
    try:
        client = OpenAI(api_key=api_key)
        mdl = model or "gpt-image-1"
        if mdl not in SUPPORTED_IMAGE_MODELS:
            logger.warning("unsupported OPENAI_IMAGE_MODEL '%s'; defaulting to 'gpt-image-1'", mdl)
            mdl = "gpt-image-1"
        resp = client.images.generate(model=mdl, prompt=prompt, size=f"{size_square}x{size_square}")
        b64 = resp.data[0].b64_json
        img_bytes = base64.b64decode(b64)
        im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        return im
    except Exception as e:
        logger.error("OpenAI image generation failed: %s", e)
        return None


def generate_image(product: str, brief: Dict, aspect: str, out_path: str) -> str:
    size = ASPECT_SIZES.get(aspect, (1024, 1024))
    brand = brief.get("brand", {})
    primary = (brand.get("colors", {}) or {}).get("primary")
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_IMAGE_MODEL", brief.get("openai_image_model"))

    msg = brief.get("message", "")
    region = brief.get("region") or brief.get("target_region") or ""
    audience = brief.get("audience") or brief.get("target_audience") or ""
    lang = brief.get("language") or brief.get("target_language") or "en"
    prompt = (
        f"Product: {product}. Audience: {audience}. Region: {region}. "
        f"Language: {lang}. Message: {msg}. Stylized, ad-ready."
    )

    im = None
    source = None
    if aspect == "1:1":
        # Try Azure OpenAI first (if configured), then OpenAI Images API
        im = _try_azure_openai_generate(prompt, 1024)
        if im is not None:
            source = "azure"
        else:
            im = _try_openai_generate(prompt, 1024, api_key, model)
            if im is not None:
                source = "openai"
    else:
        base = _try_azure_openai_generate(prompt, 1024)
        if base is not None:
            source = "azure"
        else:
            base = _try_openai_generate(prompt, 1024, api_key, model)
            if base is not None:
                source = "openai"
        if base is not None:
            im = _resize_to_aspect(base, size)

    if im is None:
        source = "placeholder"
        im = _placeholder_image(product, size, primary)

    im = _resize_to_aspect(im, size)
    _save_image(im, out_path)
    try:
        _save_meta(out_path, {
            "source": source or "unknown",
            "product": product,
            "aspect": aspect,
            "model": (model or "") if isinstance(model, str) else "",
        })
    except Exception:
        pass
    logger.info("generated asset -> %s", out_path)
    return out_path
