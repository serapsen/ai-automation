from typing import Dict, List
from src.utils.logger import get_logger

logger = get_logger("pipeline.brief")


def validate_and_normalize(brief: Dict) -> Dict:
    products: List[str] = brief.get("products") or []
    if not products:
        raise SystemExit("brief requires at least one product")
    aspects = brief.get("aspect_ratios") or ["1:1", "9:16", "16:9"]
    brief["aspect_ratios"] = aspects
    region = brief.get("region")
    audience = brief.get("audience")
    if region or audience:
        logger.info("brief: region=%s audience=%s", region, audience)
    return brief
