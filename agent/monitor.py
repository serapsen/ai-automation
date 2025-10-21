import argparse
import json
import os
import time
from typing import Dict, List, Tuple

from dotenv import load_dotenv

from src.utils.logger import get_logger
from src.pipeline.asset_ingestion import load_brief, aspect_to_dir
from main import run_pipeline
from src.notify.emailer import send_email, render_email_template

logger = get_logger("agent.monitor")

STATE_PATH = os.path.join("agent", ".processed.json")


def _load_state() -> Dict[str, float]:
    if not os.path.isfile(STATE_PATH):
        return {}
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(st: Dict[str, float]):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=2)


def _list_briefs(folder: str) -> List[str]:
    out = []
    for fn in os.listdir(folder):
        if fn.lower().endswith((".yaml", ".yml", ".json")):
            out.append(os.path.join(folder, fn))
    return sorted(out)


def _count_outputs(output_root: str, product: str, aspect: str) -> int:
    d = os.path.join(output_root, product, aspect_to_dir(aspect))
    if not os.path.isdir(d):
        return 0
    return len([fn for fn in os.listdir(d) if fn.lower().endswith("_final.png")])


def _compose_email(brief_path: str, summary: Dict, variant_target: int) -> Tuple[str, str, str]:
    brief = load_brief(brief_path)
    products = brief.get("products", [])
    output_root = brief.get("output_root", "output")
    name = os.path.basename(brief_path)
    region = brief.get("region")
    audience = brief.get("audience")
    brand = brief.get("brand", {}) or {}
    colors = brand.get("colors", {}) or {}
    brand_primary = colors.get("primary")
    brand_logo_path = (brand.get("logo_path") or "").strip() or None
    subject = f"Creative Pipeline Update – {name} (region={region or '-'}, audience={audience or '-'})"
    rows = []
    for p in products:
        for a in summary.get("aspects", []):
            cnt = None
            uniq = None
            try:
                cnt = ((summary or {}).get("products", {}).get(p, {}).get(a, {}) or {}).get("count")
                uniq = ((summary or {}).get("products", {}).get(p, {}).get(a, {}).get("unique", {}) or {}).get("count")
            except Exception:
                cnt = None
                uniq = None
            if cnt is None:
                cnt = _count_outputs(output_root, p, a)
            if cnt < variant_target:
                rows.append({"product": p, "aspect": a, "count": cnt, "unique": uniq})
    context = {
        "subject": subject,
        "brief_name": name,
        "region": region,
        "audience": audience,
        "variant_target": variant_target,
        "rows": rows,
        "brand_primary": brand_primary,
        "brand_logo": bool(brand_logo_path),
        "brand_logo_cid": "brandlogo" if brand_logo_path and os.path.isfile(brand_logo_path) else None,
    }
    text = render_email_template("alert.txt.j2", context) or ""
    html = render_email_template("alert.html.j2", context) or ""
    return subject, text, html


def process_once(briefs_dir: str, variant_target: int) -> int:
    st = _load_state()
    found = _list_briefs(briefs_dir)
    processed = 0
    for path in found:
        mtime = os.path.getmtime(path)
        if st.get(path) == mtime:
            continue
        logger.info("processing brief -> %s", path)
        try:
            res = run_pipeline(path)
            subject, body, html = _compose_email(path, res, variant_target)
            for line in (body or "").splitlines():
                logger.info(line)
            brief = load_brief(path)
            output_root = brief.get("output_root", "output")
            attachments = []
            json_p = os.path.join(output_root, "summary.json")
            csv_p = os.path.join(output_root, "summary.csv")
            if os.path.isfile(json_p):
                attachments.append({"path": json_p})
            if os.path.isfile(csv_p):
                attachments.append({"path": csv_p})
            brand = brief.get("brand", {}) or {}
            logo_path = (brand.get("logo_path") or "").strip() or None
            if logo_path and os.path.isfile(logo_path):
                attachments.append({"path": logo_path, "cid": "brandlogo"})

            def _as_list(v):
                if not v:
                    return []
                if isinstance(v, list):
                    return [str(x).strip() for x in v if str(x).strip()]
                return [s.strip() for s in str(v).split(",") if s.strip()]

            notif = brief.get("notifications", {}) or {}
            to_addrs = _as_list(notif.get("to"))
            cc_addrs = _as_list(notif.get("cc"))
            by_region = brief.get("notifications_by_region", {}) or {}
            if region := brief.get("region"):
                extra = by_region.get(region)
                if extra:
                    to_addrs = to_addrs or _as_list(extra.get("to"))
                    cc_addrs = cc_addrs or _as_list(extra.get("cc"))

            send_email(subject=subject, body_text=body, body_html=html, attachments=attachments, to_addrs=to_addrs or None, cc_addrs=cc_addrs or None)
            st[path] = mtime
            processed += 1
        except Exception as e:
            logger.error("pipeline error: %s", e)
    _save_state(st)
    return processed


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--briefs_dir", default=os.path.join("input", "briefs"))
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=int, default=10)
    parser.add_argument("--variant_target", type=int, default=3)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    if args.once or not args.watch:
        process_once(args.briefs_dir, args.variant_target)
        return

    while True:
        try:
            n = process_once(args.briefs_dir, args.variant_target)
            if n:
                logger.info("processed %d brief(s)", n)
            time.sleep(args.interval)
        except KeyboardInterrupt:
            logger.info("stopped by user")
            break


if __name__ == "__main__":
    main()
