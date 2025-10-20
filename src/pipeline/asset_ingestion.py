import os
import json
from typing import Dict, List

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

ASPECT_NORMALS = {
    "1:1": "1:1",
    "1x1": "1:1",
    "1_1": "1:1",
    "1-1": "1:1",
    "9:16": "9:16",
    "9x16": "9:16",
    "9_16": "9:16",
    "9-16": "9:16",
    "16:9": "16:9",
    "16x9": "16:9",
    "16_9": "16:9",
    "16-9": "16:9",
}


def normalize_aspect(r: str) -> str:
    return ASPECT_NORMALS.get(r.strip(), r.strip())


def load_brief(brief_path: str) -> Dict:
    ext = os.path.splitext(brief_path)[1].lower()
    with open(brief_path, "r", encoding="utf-8") as f:
        if ext in {".yaml", ".yml"}:
            if yaml is None:
                raise RuntimeError("PyYAML not installed")
            data = yaml.safe_load(f)
        else:
            data = json.load(f)
    return data or {}


def get_assets_root(brief: Dict) -> str:
    return brief.get("assets_root", os.path.join("input", "assets"))


def list_existing_assets(product: str, aspect_ratio: str, assets_root: str) -> List[str]:
    aspect_norm = normalize_aspect(aspect_ratio)
    candidates = [aspect_norm, aspect_norm.replace(":", "x"), aspect_norm.replace(":", "_"), aspect_norm.replace(":", "-")]
    out: List[str] = []
    for cand in candidates:
        d = os.path.join(assets_root, product, cand)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if os.path.splitext(fn)[1].lower() in IMAGE_EXTS:
                out.append(os.path.join(d, fn))
    return out


def get_aspect_list(brief: Dict) -> List[str]:
    aspects = brief.get("aspect_ratios") or ["1:1", "9:16", "16:9"]
    return [normalize_aspect(a) for a in aspects]


def aspect_to_dir(aspect: str) -> str:
    """Convert a human-readable aspect ratio to a filesystem-safe directory name.
    Example: "1:1" -> "1x1", "9:16" -> "9x16".
    """
    a = normalize_aspect(aspect)
    return a.replace(":", "x")
