import os
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger("translate")


_DEF_OPENAI_TRANSLATE_MODEL = os.getenv("OPENAI_TRANSLATE_MODEL", "gpt-4o-mini")


def _normalize_lang(lang: str) -> str:
    lang = (lang or "").strip().lower()
    if lang in ("en", "eng", "english"):  # normalize English
        return "en"
    return lang


def translate_message(text: str, target_lang: str) -> str:
    """
    Translate marketing message to target language using Azure OpenAI first,
    then OpenAI.com. If no provider is configured, return the input text.
    """
    target_lang = _normalize_lang(target_lang)
    if not text or target_lang in ("", "en"):
        return text

    # Try Azure OpenAI Chat
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_TRANSLATE_DEPLOYMENT")
    api_version = os.getenv("OPENAI_API_VERSION", "2024-04-01-preview")
    if endpoint and api_key and deployment:
        try:
            from openai import AzureOpenAI
            client = AzureOpenAI(api_version=api_version, azure_endpoint=endpoint, api_key=api_key)
            resp = client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": f"You are a helpful marketing translator. Translate the text to {target_lang}. Return ONLY the translated text. Preserve brand names and capitalization."},
                    {"role": "user", "content": text},
                ],
                temperature=0.2,
            )
            out = (resp.choices[0].message.content or "").strip()
            if out:
                return out
        except Exception as e:
            logger.warning("Azure translation failed: %s", e)

    # Try OpenAI.com Chat
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=_DEF_OPENAI_TRANSLATE_MODEL,
                messages=[
                    {"role": "system", "content": f"You are a helpful marketing translator. Translate the text to {target_lang}. Return ONLY the translated text. Preserve brand names and capitalization."},
                    {"role": "user", "content": text},
                ],
                temperature=0.2,
            )
            out = (resp.choices[0].message.content or "").strip()
            if out:
                return out
        except Exception as e:
            logger.warning("OpenAI.com translation failed: %s", e)

    # Fallback: identity
    return text
