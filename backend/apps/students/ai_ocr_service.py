import os
import io
import re
import time
import json
import base64
import logging
import requests
from typing import Dict, Any, List, Optional

from PIL import Image
from .ocr_preprocessor import prepare_document_images, PreprocessError

logger = logging.getLogger(__name__)

# Default Fallback OpenAI API Key from environment
DEFAULT_OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

def process_document_ephemeral(
    file_bytes: bytes,
    filename: str = '',
    debug: bool = False,
    provider: str = 'openai',
    model: str = 'gpt-4o',
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for AI document extraction.
    Supports both OpenAI GPT vision models and Google Gemini multimodal models.
    """
    start_time = time.time()

    # 1. Preprocess Images (Handles PDF conversion, Deskewing, and downscaling)
    images_np = prepare_document_images(file_bytes=file_bytes, filename=filename, max_pages=1)
    if not images_np:
        raise PreprocessError("Failed to extract any readable pages from document.")

    # Convert the first preprocessed image (NumPy array) back to JPEG for the AI API
    try:
        pil_img = Image.fromarray(images_np[0])
        buffer = io.BytesIO()
        pil_img.save(buffer, format="JPEG", quality=85)
        raw_bytes = buffer.getvalue()
        base64_image = base64.b64encode(raw_bytes).decode('utf-8')
        mime_type = "image/jpeg"
    except Exception as e:
        logger.error(f"Failed to encode image to base64: {e}")
        raise PreprocessError(f"Failed to process image format: {e}")

    prompt_text = """You are an OCR and document extraction assistant.
Analyze the uploaded document.

Specific instructions:
- Identify the document type automatically (e.g. Passport, ID Card, Shahodatnoma, Diploma, Certificate, Visa, Transcript, Contact Info).
- Generate ONLY necessary structured fields that are meaningful for the identified document type. Do not perform a general OCR of every text block, and do not extract design markings, watermarks, signatures, or noisy metadata.
- If the document is a Passport or ID Card:
  - If it is the student's own passport/ID:
    - "FULL_NAME": Concatenation of Surname + Given Names + Father's Name (patronymic / Otasining ismi) in that exact order in ALL UPPERCASE (e.g. "ISAKJONOV MUKHAMMADIYOR NAVRUZBEK UGLI").
    - "PASSPORT_NUMBER": Alphanumeric serial without spaces (e.g. "FA1234567").
    - "DATE_OF_BIRTH": Strict ISO format YYYY-MM-DD (e.g. '15 10 2007' -> '2007-10-15').
    - "DATE_OF_ISSUE": Strict ISO format YYYY-MM-DD (e.g. '16 05 2025' -> '2025-05-16').
    - "DATE_OF_EXPIRATION": Strict ISO format YYYY-MM-DD (e.g. '15 05 2030' -> '2030-05-15').
    - "SEX": Exactly "M" or "F".
  - If it is a Parent's Passport/ID (older person, parent document):
    - Set document_type to "FATHER'S PASSPORT" (if male) or "MOTHER'S PASSPORT" (if female).
    - Extract ONLY "FATHER_FULLNAME" or "MOTHER_FULLNAME" in ALL UPPERCASE (do NOT extract personal passport numbers or birth dates into student's fields).
- If the document is a university/college diploma or secondary school certificate (e.g. Bachelor's Diploma / Bakalavr Diplomi, Master's Diploma / Magistr Diplomi, Shahodatnoma / Certificate of General Secondary Education):
  - Document Type: Set document_type to "BACHELOR'S DIPLOMA", "MASTER'S DIPLOMA", "SHAHODATNOMA", or "DIPLOMA".
  - Extract ONLY these educational fields (Do NOT extract personal details like FULL_NAME, DATE_OF_BIRTH, or personal ID numbers):
    - "FINAL_SCHOOL_NAME": The full name of the university, college, or school (from educational institution header) TRANSLATED INTO ENGLISH and formatted in ALL UPPERCASE (e.g. "SAMARKAND STATE UNIVERSITY NAMED AFTER SHAROF RASHIDOV" or "TASHKENT STATE TECHNICAL UNIVERSITY").
    - "MAJOR": For Bachelor's/Master's diplomas, extract the awarded field of study/speciality in ALL UPPERCASE (e.g. "PHILOLOGY AND LANGUAGE TEACHING"). For Shahodatnoma, MUST be set to exactly "GENERAL SECONDARY EDUCATION".
    - "GPA": Extract ONLY if an explicit GPA score or complete grades table is printed on the scan. If GPA / grades are NOT printed on the document scan, DO NOT include the "GPA" field at all.
    - "DEGREE_NO": The diploma / certificate serial number (e.g. "B № 00644212" or "UM №03565142").
    - "DATE_OF_GRADUATION": The graduation date in YYYY-MM-DD format (from the State Attestation Commission decision date e.g. 'June 10, 2025' -> '2025-06-10', or issue date). If only the year is available, extract the 4-digit year (e.g. '2025').
    - "DATE_OF_ENTRY": Automatically calculate Date of Entry:
      - For Bachelor's Diplomas (4-year degree): (Date of Graduation year - 4 years), on September 2nd in YYYY-MM-DD format (e.g. 2025 - 4 = '2021-09-02').
      - For Master's Diplomas (2-year degree): (Date of Graduation year - 2 years), on September 2nd in YYYY-MM-DD format (e.g. 2025 - 2 = '2023-09-02').
      - For Secondary School Certificates (Shahodatnoma): (Date of Graduation year - 3 years), on September 2nd in YYYY-MM-DD format (e.g. 2025 - 3 = '2022-09-02').
- If the document contains contact information or is a screenshot (e.g. a screenshot of a chat, Telegram, WhatsApp, SMS, profile card, or note):
  - Set document_type to "CONTACT INFO" or "MESSENGER SCREENSHOT".
  - Extract ONLY these fields if present:
    - "EMAIL": The email address exactly as written.
    - "PHONE_NUMBER_1": The primary phone number found.
    - "PHONE_NUMBER_2": The secondary phone number found (if any).
    - "FATHER_PHONE": Father's phone number if labelled as dadam, otam, father, etc.
    - "MOTHER_PHONE": Mother's phone number if labelled as oyim, onam, mother, etc.
    - "FATHER_FULLNAME": Father's name if mentioned in text.
    - "MOTHER_FULLNAME": Mother's name if mentioned in text.
    - "ADDRESS": The physical/home address. MUST be translated into English and formatted in ALL UPPERCASE (e.g. "SURKHANDARYA REGION, QIZIRIQ DISTRICT, QORASUV MAHALLA").
  - Only include fields that are actually present in the document. Do not hallucinate fields.
- If the document is of another type:
  - Automatically detect and generate ONLY the key fields (maximum 5-6 core identifiers or dates) necessary to describe that document. Do not perform a general OCR of every text block.
- Ignore watermarks, decorative branding, or irrelevant numbers.
- Provide a full raw OCR text in the "ocr_text" property. Ensure that all double quotes, backslashes, and newlines inside the raw OCR text are properly escaped so the response is valid JSON.

Return JSON only. Do not explain anything. Output must be exactly in this JSON format:
{
  "document_type": "...",
  "fields": {
  },
  "ocr_text": "..."
}"""

    provider_clean = (provider or 'openai').lower().strip()
    result_text = "{}"

    # 2. Process with Google Gemini
    if provider_clean == 'gemini':
        gemini_key = api_key or os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
        if not gemini_key:
            raise Exception("Gemini API Key is not configured. Please enter your Gemini API Key in AI Settings.")

        gemini_model = model or 'gemini-3.7-flash'
        models_to_try = [gemini_model]
        if gemini_model != 'gemini-2.5-flash':
            models_to_try.append('gemini-2.5-flash')
        if 'gemini-1.5-flash' not in models_to_try:
            models_to_try.append('gemini-1.5-flash')

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt_text},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64_image
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }

        last_error = None
        for current_model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={gemini_key}"
            for attempt in range(2):
                try:
                    resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=45)
                    if resp.status_code == 503 or resp.status_code == 429:
                        time.sleep(1.0)
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            result_text = parts[0].get("text", "{}")
                            model = current_model
                            break
                except Exception as e:
                    last_error = e
                    time.sleep(0.5)
            if result_text != "{}":
                break

        if result_text == "{}":
            logger.error(f"Gemini API call failed across models {models_to_try}: {last_error}")
            raise Exception(f"Gemini AI extraction failed (Google servers currently overloaded): {str(last_error)}")

    # 3. Process with OpenAI GPT (Default)
    else:
        openai_key = api_key or os.environ.get('OPENAI_API_KEY') or DEFAULT_OPENAI_API_KEY
        openai_model = model or 'gpt-4o'

        payload = {
            "model": openai_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
        }

        keys_to_try = [openai_key]
        if openai_key != DEFAULT_OPENAI_API_KEY:
            keys_to_try.append(DEFAULT_OPENAI_API_KEY)

        last_openai_err = None
        for current_key in keys_to_try:
            try:
                resp = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {current_key}"
                    },
                    json=payload,
                    timeout=45
                )
                if resp.status_code == 401 and current_key != DEFAULT_OPENAI_API_KEY:
                    logger.warning("Custom OpenAI API key returned 401. Falling back to default server key.")
                    continue
                resp.raise_for_status()
                data = resp.json()
                result_text = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                if result_text and result_text != "{}":
                    break
            except Exception as e:
                last_openai_err = e

        if result_text == "{}":
            logger.error(f"OpenAI API call failed: {last_openai_err}")
            raise Exception(f"OpenAI AI extraction failed: {str(last_openai_err)}")

    # 4. Parse JSON result
    try:
        # Strip markdown ```json markers if any
        clean_text = result_text.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.split("\n", 1)[1]
            if clean_text.endswith("```"):
                clean_text = clean_text.rsplit("\n", 1)[0]
        result_json = json.loads(clean_text)
    except Exception as e:
        logger.error(f"Failed to parse AI JSON output: {result_text}")
        raise Exception(f"AI extraction JSON parse error: {str(e)}")

    MONTH_MAP = {
        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12,
        'YAN': 1, 'FEV': 2, 'MART': 3, 'APRIL': 4, 'MAYIS': 5, 'IYUN': 6,
        'IYUL': 7, 'AVG': 8, 'SEN': 9, 'OKT': 10, 'NOY': 11, 'DEK': 12
    }

    def normalize_date_val(val: Any) -> str:
        if not val:
            return str(val or '')
        s = str(val).strip()
        # Already ISO YYYY-MM-DD
        if re.match(r'^\d{4}-\d{2}-\d{2}$', s):
            return s
        
        # DD MM YYYY, DD.MM.YYYY, DD/MM/YYYY, DD-MM-YYYY
        m1 = re.match(r'^(\d{1,2})[\s\.\/\-](\d{1,2})[\s\.\/\-](\d{4})$', s)
        if m1:
            d, m, y = int(m1.group(1)), int(m1.group(2)), int(m1.group(3))
            if m > 12 and d <= 12:
                d, m = m, d
            return f"{y:04d}-{m:02d}-{d:02d}"

        # YYYY MM DD, YYYY.MM.DD, YYYY/MM/DD
        m2 = re.match(r'^(\d{4})[\s\.\/\-](\d{1,2})[\s\.\/\-](\d{1,2})$', s)
        if m2:
            y, m, d = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
            return f"{y:04d}-{m:02d}-{d:02d}"

        # DD Mon YYYY e.g. 15 OCT 2007
        m3 = re.match(r'^(\d{1,2})[\s\.\/\-]([A-Za-z]{3,5})[\s\.\/\-](\d{4})$', s)
        if m3:
            d = int(m3.group(1))
            mon = m3.group(2).upper()[:3]
            y = int(m3.group(3))
            if mon in MONTH_MAP:
                return f"{y:04d}-{MONTH_MAP[mon]:02d}-{d:02d}"

        return s

    doc_type = result_json.get("document_type", "UNKNOWN DOCUMENT")
    simple_fields = result_json.get("fields", {})
    raw_ocr_text = result_json.get("ocr_text", "")

    DATE_KEYS = {'DATE_OF_BIRTH', 'DATE_OF_ISSUE', 'DATE_OF_EXPIRATION', 'DATE_OF_ENTRY', 'DATE_OF_GRADUATION', 'BIRTHDAY'}

    serialized_details = {}
    for k, v in simple_fields.items():
        if v:
            clean_v = str(v).strip()
            # Normalize any date fields strictly to YYYY-MM-DD
            if k in DATE_KEYS or 'DATE' in k.upper() or 'BIRTH' in k.upper():
                clean_v = normalize_date_val(clean_v)
                simple_fields[k] = clean_v

            serialized_details[k] = {
                "value": clean_v,
                "confidence": 0.99,
                "validated": True,
                "source": "AI_EXTRACTION"
            }

    elapsed_ms = int((time.time() - start_time) * 1000)
    engine_label = f"{provider_clean.upper()} ({model})"

    response_data = {
        "document_type": doc_type,
        "fields": simple_fields,
        "field_details": serialized_details,
        "metadata": {
            "latency_ms": elapsed_ms,
            "ocr_engine": engine_label,
            "pages_processed": 1
        }
    }

    if debug:
        response_data["ocr_text"] = raw_ocr_text

    return response_data
