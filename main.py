import argparse
import os
import shutil
from typing import Dict, List

from dotenv import load_dotenv

from src.utils.logger import get_logger
from src.pipeline.asset_ingestion import load_brief, get_assets_root, list_existing_assets, get_aspect_list, aspect_to_dir
from src.pipeline.asset_generation import generate_image, ASPECT_SIZES
from src.pipeline.post_processor import ensure_dir, overlay_text, overlay_logo, moderate_text, brand_compliance_summary

logger = get_logger("main")


def _copy(src: str, dst: str):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def run_pipeline(brief_path: str) -> Dict:
    load_dotenv()
    brief = load_brief(brief_path)

    products: List[str] = brief.get("products") or []
    if len(products) < 1:
        raise SystemExit("brief requires at least one product")

    aspects = get_aspect_list(brief)
    assets_root = get_assets_root(brief)
    output_root = brief.get("output_root", os.path.join("output"))
    message = brief.get("message", "")
    brand = brief.get("brand", {})
    brand_color = (brand.get("colors", {}) or {}).get("primary")
    logo_path = (brand.get("logo_path") or "").strip() or None

    mod = moderate_text(message)
    if mod:
        logger.warning("message contains prohibited terms: %s", mod)

    summary = {"products": {}, "aspects": aspects}

    for product in products:
        prod_summary = {}
        for aspect in aspects:
            size = ASPECT_SIZES.get(aspect)
            out_dir = os.path.join(output_root, product, aspect_to_dir(aspect))
            ensure_dir(out_dir)

            existing = list_existing_assets(product, aspect, assets_root)
            used = []
            if existing:
                for i, src in enumerate(existing):
                    tmp = os.path.join(out_dir, f"exist_{i+1}.png")
                    _copy(src, tmp)
                    over = os.path.join(out_dir, f"exist_{i+1}_msg.png")
                    overlay_text(tmp, message, over, brand_color)
                    with_logo = os.path.join(out_dir, f"exist_{i+1}_final.png")
                    overlay_logo(over, logo_path, with_logo)
                    used.append(with_logo)
            else:
                gen_path = os.path.join(out_dir, f"gen_1.png")
                generate_image(product, brief, aspect, gen_path)
                over = os.path.join(out_dir, f"gen_1_msg.png")
                overlay_text(gen_path, message, over, brand_color)
                with_logo = os.path.join(out_dir, f"gen_1_final.png")
                overlay_logo(over, logo_path, with_logo)
                used.append(with_logo)

            comp = brand_compliance_summary(brand_color, os.path.isfile(logo_path) if logo_path else False)
            prod_summary[aspect] = {"count": len(used), "files": used, "compliance": comp}
            logger.info("%s | %s -> %d creatives", product, aspect, len(used))
        summary["products"][product] = prod_summary

    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief", required=True, help="Path to a YAML/JSON campaign brief")
    args = parser.parse_args()
    res = run_pipeline(args.brief)
    logger.info("pipeline finished: %s", {k: (v if k != "products" else list(v.keys())) for k, v in res.items()})


if __name__ == "__main__":
    main()
