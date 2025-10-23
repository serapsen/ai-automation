import argparse
import os
import shutil
import json
from typing import Dict, List

from dotenv import load_dotenv

from src.utils.logger import get_logger
from src.pipeline.asset_ingestion import load_brief, get_assets_root, list_existing_assets, get_aspect_list, aspect_to_dir
from src.pipeline.asset_generation import generate_image, ASPECT_SIZES
from src.pipeline.post_processor import ensure_dir, overlay_text, overlay_logo, moderate_text, brand_compliance_summary
from src.storage.base import get_storage
from src.reporting.summary import compute_uniqueness, write_summary, write_summary_csv
from src.pipeline.brief import validate_and_normalize
from src.utils.translate import translate_message

logger = get_logger("main")


def _copy(src: str, dst: str):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def run_pipeline(brief_path: str) -> Dict:
    load_dotenv()
    dbx = get_storage()
    brief = load_brief(brief_path)
    brief = validate_and_normalize(brief)

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
    region = brief.get("region")
    audience = brief.get("audience")
    if region or audience:
        logger.info("brief: region=%s audience=%s", region, audience)

    languages_raw = brief.get("languages") or ["en"]
    if isinstance(languages_raw, str):
        languages = [languages_raw]
    else:
        languages = list(languages_raw)
    norm_langs: List[str] = []
    for l in languages:
        s = str(l).strip().lower()
        if s and s not in norm_langs:
            norm_langs.append(s)
    if "en" not in norm_langs:
        norm_langs = ["en"] + norm_langs
    languages = norm_langs

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
                    for lang in languages:
                        msg_lang = translate_message(message, lang)
                        over = os.path.join(out_dir, f"exist_{i+1}_{lang}_msg.png")
                        overlay_text(tmp, msg_lang, over, brand_color)
                        with_logo = os.path.join(out_dir, f"exist_{i+1}_{lang}_final.png")
                        overlay_logo(over, logo_path, with_logo)
                        used.append(with_logo)
                        if dbx.enabled():
                            rel = os.path.join(product, aspect_to_dir(aspect), os.path.basename(with_logo))
                            dbx.upload(with_logo, rel)
            else:
                for lang in languages:
                    gen_path = os.path.join(out_dir, f"gen_1_{lang}.png")
                    brief_lang = dict(brief)
                    if lang != "en":
                        msg_lang = translate_message(message, lang)
                    else:
                        msg_lang = message
                    brief_lang["language"] = lang
                    brief_lang["message"] = msg_lang
                    generate_image(product, brief_lang, aspect, gen_path)
                    source = None
                    try:
                        with open(gen_path + ".meta.json", "r", encoding="utf-8") as mf:
                            meta = json.load(mf)
                            source = (meta or {}).get("source")
                    except Exception:
                        pass
                    if source == "placeholder":
                        over = os.path.join(out_dir, f"gen_1_{lang}_msg.png")
                        overlay_text(gen_path, msg_lang, over, brand_color)
                        src_for_logo = over
                    else:
                        src_for_logo = gen_path
                    with_logo = os.path.join(out_dir, f"gen_1_{lang}_final.png")
                    overlay_logo(src_for_logo, logo_path, with_logo)
                    used.append(with_logo)
                    if dbx.enabled():
                        rel = os.path.join(product, aspect_to_dir(aspect), os.path.basename(with_logo))
                        dbx.upload(with_logo, rel)

            comp = brand_compliance_summary(brand_color, os.path.isfile(logo_path) if logo_path else False)
            uniq = compute_uniqueness(used)
            prod_summary[aspect] = {"count": len(used), "files": used, "compliance": comp, "unique": uniq}
            logger.info("%s | %s -> %d creatives", product, aspect, len(used))
        summary["products"][product] = prod_summary
    write_summary(output_root, summary)
    write_summary_csv(output_root, summary)

    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief", required=True, help="Path to a YAML/JSON campaign brief")
    args = parser.parse_args()
    res = run_pipeline(args.brief)
    logger.info("pipeline finished: %s", {k: (v if k != "products" else list(v.keys())) for k, v in res.items()})


if __name__ == "__main__":
    main()
