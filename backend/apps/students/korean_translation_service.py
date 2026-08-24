import os
import re
import json
import urllib.parse
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def get_ai_settings_from_request(request) -> Optional[Dict[str, Any]]:
    """Extracts custom AI settings saved in localStorage and passed via HTTP header."""
    if not request:
        return None
    header_val = getattr(request, 'headers', {}).get('X-AI-Settings') or getattr(request, 'META', {}).get('HTTP_X_AI_SETTINGS')
    if header_val:
        try:
            decoded = urllib.parse.unquote(header_val)
            return json.loads(decoded)
        except Exception as e:
            logger.debug(f"Failed to parse X-AI-Settings header: {e}")
    return None


def _translate_with_google(text: str) -> Optional[str]:
    """Instantaneous phonetic transliteration fallback via Google Translate."""
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": "ko",
            "dt": "t",
            "q": text
        }
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                translated_parts = [part[0] for part in data[0] if part and len(part) > 0 and part[0]]
                translated = "".join(translated_parts).strip()
                if translated and any('\uac00' <= char <= '\ud7a3' for char in translated):
                    return translated
    except Exception as e:
        logger.warning(f"Google Translate fallback failed for '{text}': {e}")
    return None


def _translate_with_openai(full_name: str, api_key: str, model: str = 'gpt-4o-mini') -> Optional[str]:
    """Transliterate name using OpenAI GPT models (gpt-4o, gpt-4o-mini, etc.)."""
    try:
        prompt = (
            "You are an expert Korean linguist and university admissions specialist in South Korea.\n"
            "Your task is to transliterate foreign names written in Latin (e.g. Uzbek, Central Asian, Russian, or International English names) "
            "into standard, natural Korean Hangul (한글) phonetically, as required on South Korean university applications and alien registration cards.\n\n"
            "Rules:\n"
            "1. Output ONLY the Korean Hangul transliteration. Do NOT include English letters, punctuation, notes, or explanations.\n"
            "2. Preserve all name components (Family Name, Given Name, Patronymic/Father's name like UGLI/QIZI if present) separated by single spaces.\n"
            "3. Examples:\n"
            "   - 'ABDUSALOMOV ZAYNIDDIN MAVLONBEK UGLI' -> '압두살로모프 자이니딘 마블론벡 우글리'\n"
            "   - 'ISMOILOVA POKIZA IKROMJON QIZI' -> '이스모일로바 포키자 이크롬존 키지'\n"
            "   - 'SAYFULLAEV SHOHJAHON ZOKHID UGLI' -> '사이풀라예프 쇼흐자혼 조히드 우글리'\n"
            "   - 'KIM DMITRIY' -> '김 드미트리'\n"
            "   - 'ALIEV AKMAL' -> '알리예프 악말'\n\n"
            f"Transliterate this full name into Korean Hangul: {full_name}"
        )

        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": model or "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a precise name transliterator that outputs only Korean Hangul."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 100
            },
            timeout=10
        )

        if resp.status_code == 200:
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            content = re.sub(r'[\'"`\*_]', '', content).strip()
            if content and any('\uac00' <= char <= '\ud7a3' for char in content):
                return content
        else:
            logger.warning(f"OpenAI API returned status {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"OpenAI translation failed for '{full_name}': {e}")
    return None


def _translate_with_gemini(full_name: str, api_key: str, model: str = 'gemini-3.7-flash') -> Optional[str]:
    """Transliterate name using Google Gemini multimodal/text models."""
    prompt = (
        "You are an expert Korean linguist and university admissions specialist in South Korea.\n"
        "Your task is to transliterate foreign names written in Latin (e.g. Uzbek, Central Asian, Russian, or International English names) "
        "into standard, natural Korean Hangul (한글) phonetically, as required on South Korean university applications and alien registration cards.\n\n"
        "Rules:\n"
        "1. Output ONLY the Korean Hangul transliteration. Do NOT include English letters, punctuation, notes, or explanations.\n"
        "2. Preserve all name components (Family Name, Given Name, Patronymic/Father's name like UGLI/QIZI if present) separated by single spaces.\n"
        "3. Examples:\n"
        "   - 'ABDUSALOMOV ZAYNIDDIN MAVLONBEK UGLI' -> '압두살로모프 자이니딘 마블론벡 우글리'\n"
        "   - 'ISMOILOVA POKIZA IKROMJON QIZI' -> '이스모일로바 포키자 이크롬존 키지'\n"
        "   - 'SAYFULLAEV SHOHJAHON ZOKHID UGLI' -> '사이풀라예프 쇼흐자혼 조히드 우글리'\n"
        "   - 'KIM DMITRIY' -> '김 드미트리'\n"
        "   - 'ALIEV AKMAL' -> '알리예프 악말'\n\n"
        f"Transliterate this full name into Korean Hangul: {full_name}"
    )

    models_to_try = [model or 'gemini-3.7-flash']
    if 'gemini-2.5-flash' not in models_to_try:
        models_to_try.append('gemini-2.5-flash')
    if 'gemini-1.5-flash' not in models_to_try:
        models_to_try.append('gemini-1.5-flash')

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 100
        }
    }

    for current_model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={api_key}"
        try:
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts:
                        text = parts[0].get("text", "").strip()
                        text = re.sub(r'[\'"`\*_]', '', text).strip()
                        if text and any('\uac00' <= char <= '\ud7a3' for char in text):
                            return text
            elif resp.status_code in (429, 503):
                continue
        except Exception as e:
            logger.warning(f"Gemini transliteration attempt with {current_model} failed: {e}")

    return None


def translate_name_to_korean(
    full_name: Optional[str],
    settings: Optional[Dict[str, Any]] = None,
    request: Optional[Any] = None
) -> Optional[str]:
    """
    Translates/transliterates an English/Latin full name into standard Korean Hangul.
    Respects the active AI settings saved on Document Extract Page (OpenAI or Gemini provider, custom model & API key).
    Falls back gracefully to server env keys and Google Translate.
    """
    if not full_name or not full_name.strip():
        return None

    cleaned_name = " ".join(full_name.strip().split()).upper()

    # If it's already entirely Hangul, return as is
    if all(('\uac00' <= char <= '\ud7a3' or char.isspace()) for char in cleaned_name):
        return cleaned_name

    # Merge settings from parameter or request header
    ai_cfg = settings or {}
    if not ai_cfg and request:
        ai_cfg = get_ai_settings_from_request(request) or {}

    provider = (ai_cfg.get('provider') or 'openai').lower().strip()

    # 1. If Gemini provider is configured in Document Extract AI Settings:
    if provider == 'gemini':
        gemini_key = (
            ai_cfg.get('apiKey') or
            ai_cfg.get('geminiApiKey') or
            os.environ.get('GEMINI_API_KEY') or
            os.environ.get('GOOGLE_API_KEY')
        )
        gemini_model = ai_cfg.get('model') or 'gemini-3.7-flash'

        if gemini_key:
            res = _translate_with_gemini(cleaned_name, gemini_key, gemini_model)
            if res:
                logger.info(f"AI Translated '{cleaned_name}' -> '{res}' (Gemini: {gemini_model})")
                return res

    # 2. If OpenAI provider is configured in Document Extract AI Settings (or default):
    openai_key = (
        ai_cfg.get('openaiApiKey') or
        ai_cfg.get('apiKey') or
        os.environ.get('OPENAI_API_KEY', '')
    ).strip()
    openai_model = ai_cfg.get('openaiModel') or ai_cfg.get('model') or 'gpt-4o-mini'

    if openai_key:
        res = _translate_with_openai(cleaned_name, openai_key, openai_model)
        if res:
            logger.info(f"AI Translated '{cleaned_name}' -> '{res}' (OpenAI: {openai_model})")
            return res

    # 3. If primary failed or key missing, check if Gemini key is available as secondary:
    if provider != 'gemini':
        fallback_gemini_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
        if fallback_gemini_key:
            res = _translate_with_gemini(cleaned_name, fallback_gemini_key, 'gemini-2.5-flash')
            if res:
                logger.info(f"AI Translated '{cleaned_name}' -> '{res}' (Gemini Fallback)")
                return res

    # 4. Instantaneous Google Translate fallback
    fallback_result = _translate_with_google(cleaned_name)
    if fallback_result:
        logger.info(f"AI Translated '{cleaned_name}' -> '{fallback_result}' (Google Fallback)")
        return fallback_result

    return None
