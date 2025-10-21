import json
import os
import csv
from typing import Dict, List, Optional

from src.utils.hash import sha1_file
from src.utils.logger import get_logger

logger = get_logger("reporting.summary")


def compute_uniqueness(paths: List[str]) -> Dict:
    hashes: List[Optional[str]] = []
    for p in paths:
        hashes.append(sha1_file(p))
    unique_count = len({h for h in hashes if h})
    return {"count": unique_count, "hashes": hashes}


def write_summary(output_root: str, summary: Dict) -> Optional[str]:
    try:
        os.makedirs(output_root, exist_ok=True)
        summary_path = os.path.join(output_root, "summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        logger.info("wrote run summary -> %s", summary_path)
        return summary_path
    except Exception:
        return None


def write_summary_csv(output_root: str, summary: Dict) -> Optional[str]:
    try:
        os.makedirs(output_root, exist_ok=True)
        csv_path = os.path.join(output_root, "summary.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["product", "aspect", "count", "unique_count"])
            products = summary.get("products", {}) or {}
            for product, by_aspect in products.items():
                for aspect, data in (by_aspect or {}).items():
                    count = (data or {}).get("count", 0)
                    uniq = ((data or {}).get("unique", {}) or {}).get("count", 0)
                    w.writerow([product, aspect, count, uniq])
        logger.info("wrote run csv summary -> %s", csv_path)
        return csv_path
    except Exception:
        return None
