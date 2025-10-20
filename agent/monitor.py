import argparse
import json
import os
import time
from typing import Dict, List

from dotenv import load_dotenv

from src.utils.logger import get_logger
from src.pipeline.asset_ingestion import load_brief, aspect_to_dir
from main import run_pipeline

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


def _compose_email(brief_path: str, summary: Dict, variant_target: int) -> str:
    brief = load_brief(brief_path)
    products = brief.get("products", [])
    output_root = brief.get("output_root", "output")
    lines = []
    lines.append("Subject: Creative Pipeline Update – Variants Below Target")
    lines.append("")
    lines.append("To: Creative Lead; AdOps")
    lines.append("Cc: IT; Legal/Compliance")
    lines.append("")
    lines.append("Hello Creative Lead and AdOps,")
    lines.append("")
    lines.append("The automation agent ran the creative pipeline for the latest brief and detected that some product/aspect combinations are below the target variant count.")
    lines.append("")
    for p in products:
        for a in summary.get("aspects", []):
            cnt = _count_outputs(output_root, p, a)
            if cnt < variant_target:
                lines.append(f"- {p} | {a}: {cnt}/{variant_target} variants available")
    lines.append("")
    lines.append("Root causes may include API rate limits, missing input assets, or provisioning delays. The agent will retry on the next cycle.")
    lines.append("")
    lines.append("Best regards,")
    lines.append("Automation Agent")
    return "\n".join(lines)


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
            email = _compose_email(path, res, variant_target)
            for line in email.splitlines():
                logger.info(line)
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
