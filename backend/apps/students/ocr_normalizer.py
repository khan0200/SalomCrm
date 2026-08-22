import re
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class ExtractedField:
    value: str
    confidence: float  # 0.0 to 1.0
    validated: bool    # True if passed checksum/regex format validation
    source: str        # 'MRZ', 'VIZ', 'OCR_REGEX', 'LAYOUT', 'CALCULATED'

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def normalize_date(raw_date: str) -> Optional[str]:
    """
    Normalizes any raw date string to standard ISO YYYY-MM-DD.
    Supports:
    - '02 04 2009', '02.04.2009', '02/04/2009', '02-04-2009'
    - '2009 04 02', '2009.04.02', '2009/04/02', '2009-04-02'
    - '02042009' (DDMMYYYY)
    - '20090402' (YYYYMMDD)
    - '2006 2028' (missing middle separator)
    """
    if not raw_date:
        return None

    clean = re.sub(r'[^\d\.\-\/\s]', '', raw_date.strip())
    parts = [p for p in re.split(r'[\s\.\-\/]+', clean) if p]

    # 3 parts (e.g. DD MM YYYY or YYYY MM DD)
    if len(parts) == 3:
        p1, p2, p3 = parts
        if len(p1) == 4 and len(p2) in (1, 2) and len(p3) in (1, 2):
            try:
                y, m, d = int(p1), int(p2), int(p3)
                if 1900 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31:
                    return f"{y:04d}-{m:02d}-{d:02d}"
            except Exception:
                pass
        elif len(p3) == 4 and len(p1) in (1, 2) and len(p2) in (1, 2):
            try:
                d, m, y = int(p1), int(p2), int(p3)
                if 1900 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31:
                    return f"{y:04d}-{m:02d}-{d:02d}"
            except Exception:
                pass

    # 2 parts (e.g. DDMM YYYY)
    if len(parts) == 2:
        p1, p2 = parts
        if len(p1) == 4 and len(p2) == 4:
            try:
                d, m, y = int(p1[:2]), int(p1[2:]), int(p2)
                if 1900 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31:
                    return f"{y:04d}-{m:02d}-{d:02d}"
            except Exception:
                pass
        elif len(p1) == 2 and len(p2) == 6:
            try:
                d, m, y = int(p1), int(p2[:2]), int(p2[2:])
                if 1900 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31:
                    return f"{y:04d}-{m:02d}-{d:02d}"
            except Exception:
                pass

    # 1 continuous digit string (8 digits)
    digits = re.sub(r'\D', '', raw_date)
    if len(digits) == 8:
        try:
            # Try DDMMYYYY
            d, m, y = int(digits[:2]), int(digits[2:4]), int(digits[4:])
            if 1900 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31:
                return f"{y:04d}-{m:02d}-{d:02d}"
            # Try YYYYMMDD
            y, m, d = int(digits[:4]), int(digits[4:6]), int(digits[6:])
            if 1900 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31:
                return f"{y:04d}-{m:02d}-{d:02d}"
        except Exception:
            pass

    return None


def normalize_passport_number(raw_pass: str) -> Optional[str]:
    """
    Normalizes passport number to standard format (e.g. 'FA7958189', 'AA1234567').
    """
    if not raw_pass:
        return None
    clean = re.sub(r'[^A-Z0-9]', '', raw_pass.upper())
    # Match standard 2-letter prefix + 7-digit number
    m = re.search(r'([A-Z]{2}\d{7})', clean)
    if m:
        return m.group(1)
    # Check if 9 chars and starts with letter
    if len(clean) == 9 and clean[0].isalpha() and clean[1:].isdigit():
        return clean
    return clean if len(clean) >= 6 else None


def normalize_gender(raw_sex: str) -> Optional[str]:
    """
    Normalizes gender string to 'MALE' or 'FEMALE'.
    """
    if not raw_sex:
        return None
    s = raw_sex.strip().upper()
    if s in ('M', 'MALE', 'ERKAK', 'МУЖ', 'МУЖСКОЙ'):
        return 'MALE'
    if s in ('F', 'FEMALE', 'AYOL', 'ЖЕН', 'ЖЕНСКИЙ'):
        return 'FEMALE'
    return None


def normalize_phone_number(raw_phone: str) -> str:
    """
    Formats phone numbers to standard 9-digit mask: XX-XXX-XX-XX.
    """
    digits = re.sub(r'\D', '', raw_phone)
    if digits.startswith('998') and len(digits) == 12:
        digits = digits[3:]
    elif len(digits) > 9:
        digits = digits[-9:]

    if len(digits) == 9:
        return f"{digits[:2]}-{digits[2:5]}-{digits[5:7]}-{digits[7:9]}"
    return raw_phone


def normalize_patronymic(raw_father_name: str) -> str:
    """
    Normalizes Uzbek and Central Asian patronymics:
    - 'ABDULKHOSHIMAUGN' or 'ABDULKHOSHIMAUGL' -> 'ABDULKHOSHIM UGLI'
    - 'RUSTAMQIZI' or 'RUSTAM QIZ' -> 'RUSTAM QIZI'
    - 'BOTIR UGLT' or 'BOTIR UGL1' -> 'BOTIR UGLI'
    """
    if not raw_father_name:
        return ""
    from .ocr_suffix_normalizer import normalize_full_name
    return normalize_full_name(raw_father_name)


def normalize_name(raw_name: str) -> str:
    """
    Normalizes full names by fixing joined patronymics, OCR suffix errors, and stripping artifacts.
    """
    if not raw_name:
        return ""
    from .ocr_suffix_normalizer import normalize_full_name
    return normalize_full_name(raw_name)


def normalize_address(raw_addr: str) -> str:
    """
    Normalizes address and region strings by adding spaces between joined words.
    e.g. 'ANDIJANREGION' -> 'ANDIJAN REGION'
    """
    clean = re.sub(r'[^A-ZА-Яa-zа-я0-9\s\'-]', '', raw_addr).strip().upper()
    clean = re.sub(
        r'([A-ZА-Я]{3,})(REGION|CITY|DISTRICT|VILOYATI|VILOYAT|TUMANI|TUMAN|SHAHRI|SHAHAR|RESPUBLIKASI)',
        r'\1 \2',
        clean
    )
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean
