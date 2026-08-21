import io
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from PIL import Image
import pymupdf  # PyMuPDF
from rapidocr_onnxruntime import RapidOCR
from mrz.checker.td3 import TD3CodeChecker
from mrz.checker.td1 import TD1CodeChecker
from mrz.checker.td2 import TD2CodeChecker

# Singleton instance of RapidOCR
_ocr_engine = None

def get_ocr_engine() -> RapidOCR:
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = RapidOCR()
    return _ocr_engine


def parse_mrz_date(yy_mm_dd: str, is_expiration: bool = False) -> Optional[str]:
    """Converts YYMMDD from MRZ to YYYY-MM-DD."""
    if not yy_mm_dd or len(yy_mm_dd) != 6 or not yy_mm_dd.isdigit():
        return None
    yy = int(yy_mm_dd[:2])
    mm = yy_mm_dd[2:4]
    dd = yy_mm_dd[4:6]
    current_year_last2 = datetime.now().year % 100
    if is_expiration:
        # Expiry is almost always 2000s
        century = 2000 if yy <= 80 else 1900
    else:
        # Birth date: if yy > current year, it's 1900s, else 2000s
        century = 2000 if yy <= current_year_last2 else 1900
    full_year = century + yy
    return f"{full_year:04d}-{mm}-{dd}"


def format_phone_number(raw_phone: str) -> str:
    """Formats phone number to 9-digit mask: XX-XXX-XX-XX."""
    digits = re.sub(r'\D', '', raw_phone)
    if digits.startswith('998') and len(digits) == 12:
        digits = digits[3:]
    elif len(digits) > 9:
        digits = digits[-9:]
    
    if len(digits) == 9:
        return f"{digits[:2]}-{digits[2:5]}-{digits[5:7]}-{digits[7:9]}"
    return raw_phone


def extract_document_from_bytes(file_bytes: bytes, filename: str = '') -> Dict[str, Any]:
    """
    Extracts text and structured fields from an uploaded image or PDF in RAM memory.
    Returns:
    {
        "document_type": "PASSPORT" | "BACHELOR'S DIPLOMA" | "SHAHODATNOMA" | "CONTACT INFO" | "GENERAL DOCUMENT",
        "fields": { ... },
        "ocr_text": "..."
    }
    """
    is_pdf = filename.lower().endswith('.pdf') or file_bytes.startswith(b'%PDF')
    images: List[Image.Image] = []

    if is_pdf:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        for page_num in range(min(len(doc), 3)):  # process up to 3 pages
            page = doc[page_num]
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
    else:
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        images.append(img)

    engine = get_ocr_engine()
    all_raw_lines: List[str] = []

    for img in images:
        img_np = np.array(img)
        result, _ = engine(img_np)
        if result:
            for item in result:
                # item is [box, text, score]
                text = item[1].strip()
                if text:
                    all_raw_lines.append(text)

    full_ocr_text = "\n".join(all_raw_lines)
    upper_text = full_ocr_text.upper()

    extracted_fields: Dict[str, str] = {}
    doc_type = "GENERAL DOCUMENT"

    # =========================================================================
    # 1. PASSPORT & MRZ DETECTION
    # =========================================================================
    # Look for TD3 MRZ (2 lines of 44 chars) or TD1 MRZ (3 lines of 30 chars)
    mrz_lines = []
    for line in all_raw_lines:
        clean = line.replace(' ', '').upper()
        # MRZ lines usually have multiple << and are >= 28 chars
        if '<<' in clean and len(clean) >= 28:
            mrz_lines.append(clean)

    mrz_success = False

    # Check TD3 (standard passport: line 1 starts with P<, line 2 has numbers and <<)
    if len(mrz_lines) >= 2:
        for i in range(len(mrz_lines) - 1):
            l1 = mrz_lines[i]
            l2 = mrz_lines[i+1]
            if (l1.startswith('P<') or l1.startswith('P')) and len(l1) >= 40 and len(l2) >= 40:
                # Pad to 44 if needed
                l1_pad = (l1 + '<'*44)[:44]
                l2_pad = (l2 + '<'*44)[:44]
                try:
                    checker = TD3CodeChecker(f"{l1_pad}\n{l2_pad}")
                    fields = checker.fields()
                    
                    surname = (fields.surname or '').replace('<', ' ').strip().upper()
                    given = (fields.names or '').replace('<', ' ').strip().upper()
                    full_name = f"{surname} {given}".strip()
                    
                    passport_num = (fields.document_number or '').replace('<', '').strip().upper()
                    sex_raw = (fields.sex or '').upper()
                    sex = 'MALE' if sex_raw == 'M' else ('FEMALE' if sex_raw == 'F' else '')
                    
                    dob = parse_mrz_date(fields.birth_date, is_expiration=False)
                    expiry = parse_mrz_date(fields.expiry_date, is_expiration=True)

                    if full_name:
                        extracted_fields['FULL_NAME'] = full_name
                    if passport_num:
                        extracted_fields['PASSPORT_NUMBER'] = passport_num
                    if dob:
                        extracted_fields['DATE_OF_BIRTH'] = dob
                    if expiry:
                        extracted_fields['DATE_OF_EXPIRATION'] = expiry
                    if sex:
                        extracted_fields['SEX'] = sex

                    doc_type = "PASSPORT"
                    mrz_success = True
                    break
                except Exception:
                    pass

    # If MRZ parsed or text clearly says PASSPORT / PASSPORT OF UZBEKISTAN
    if not mrz_success and ('PASSPORT' in upper_text or 'PASPORT' in upper_text or 'REPUBLIC OF UZBEKISTAN' in upper_text):
        doc_type = "PASSPORT"
        
        # Passport number regex (e.g. FA1234567, AA1234567)
        pass_match = re.search(r'\b([A-Z]{2}\s*\d{7})\b', upper_text)
        if pass_match:
            extracted_fields['PASSPORT_NUMBER'] = pass_match.group(1).replace(' ', '')

        # Date of birth regex
        dob_match = re.search(r'(?:DATE OF BIRTH|TUG\'ILGAN SANASI|TUGILGAN SANASI|ДАТА РОЖДЕНИЯ)[\s:]*([0-9]{2}[\.\/\-][0-9]{2}[\.\/\-][0-9]{4}|[0-9]{4}[\.\/\-][0-9]{2}[\.\/\-][0-9]{2})', upper_text)
        if dob_match:
            raw_d = dob_match.group(1).replace('/', '-').replace('.', '-')
            if len(raw_d.split('-')[0]) == 4:
                extracted_fields['DATE_OF_BIRTH'] = raw_d
            else:
                p = raw_d.split('-')
                extracted_fields['DATE_OF_BIRTH'] = f"{p[2]}-{p[1]}-{p[0]}"

        # Sex
        if re.search(r'\b(SEX|JINSI|ПОЛ)[\s:]*\bM\b|\bMALE\b|\bERKAK\b', upper_text):
            extracted_fields['SEX'] = 'MALE'
        elif re.search(r'\b(SEX|JINSI|ПОЛ)[\s:]*\bF\b|\bFEMALE\b|\bAYOL\b', upper_text):
            extracted_fields['SEX'] = 'FEMALE'

    # If passport, search for Date of Issue
    if doc_type == "PASSPORT":
        issue_match = re.search(r'(?:DATE OF ISSUE|BERILGAN SANASI|ДАТА ВЫДАЧИ)[\s:]*([0-9]{2}[\.\/\-][0-9]{2}[\.\/\-][0-9]{4}|[0-9]{4}[\.\/\-][0-9]{2}[\.\/\-][0-9]{2})', upper_text)
        if issue_match:
            raw_i = issue_match.group(1).replace('/', '-').replace('.', '-')
            if len(raw_i.split('-')[0]) == 4:
                extracted_fields['DATE_OF_ISSUE'] = raw_i
            else:
                p = raw_i.split('-')
                extracted_fields['DATE_OF_ISSUE'] = f"{p[2]}-{p[1]}-{p[0]}"

    # =========================================================================
    # 2. DIPLOMA & SHAHODATNOMA DETECTION
    # =========================================================================
    if doc_type == "GENERAL DOCUMENT":
        is_diploma = any(kw in upper_text for kw in ['DIPLOM', 'DIPLOMA', 'BAKALAVR', 'MAGISTR', 'BACHELOR', 'MASTER'])
        is_shahodatnoma = any(kw in upper_text for kw in ['SHAHODATNOMA', 'ATTESTAT', 'GENERAL SECONDARY EDUCATION', 'O\'RTA TA\'LIM', 'ORTA TALIM'])

        if is_diploma or is_shahodatnoma:
            if 'MAGISTR' in upper_text or 'MASTER' in upper_text:
                doc_type = "MASTER'S DIPLOMA"
                degree_duration = 2
            elif is_shahodatnoma:
                doc_type = "SHAHODATNOMA"
                degree_duration = 3
                extracted_fields['MAJOR'] = "GENERAL SECONDARY EDUCATION"
            else:
                doc_type = "BACHELOR'S DIPLOMA"
                degree_duration = 4

            # Degree / Certificate Serial Number (e.g. B № 00644212, UM №03565142, K № 123456)
            deg_match = re.search(r'([A-ZА-Я]{1,3}\s*(?:№|N|NO\.?)\s*\d{6,8}|\b\d{7,8}\b)', upper_text)
            if deg_match:
                extracted_fields['DEGREE_NO'] = deg_match.group(1)

            # School Name Detection
            for line in all_raw_lines:
                l_up = line.upper()
                if any(sk in l_up for sk in ['UNIVERSITET', 'UNIVERSITY', 'INSTITUT', 'INSTITUTE', 'AKADEMIYA', 'ACADEMY', 'MAKTAB', 'SCHOOL', 'KOLLEJ', 'COLLEGE', 'LITSEY', 'LYCEUM']):
                    extracted_fields['FINAL_SCHOOL_NAME'] = line.strip().upper()
                    break

            # Major Detection (if not shahodatnoma)
            if doc_type != "SHAHODATNOMA":
                for line in all_raw_lines:
                    l_up = line.upper()
                    if any(mk in l_up for mk in ['MUTAXASSISLIGI', 'YO\'NALISHI', 'YONALISHI', 'MAJOR', 'SPECIALTY', 'SPECIALITY', 'FIELD OF STUDY']):
                        clean_major = re.sub(r'^(MUTAXASSISLIGI|YO\'NALISHI|YONALISHI|MAJOR|SPECIALTY|SPECIALITY)[:\s\-]+', '', l_up).strip()
                        if clean_major:
                            extracted_fields['MAJOR'] = clean_major
                            break

            # Graduation Date Detection
            grad_match = re.search(r'\b(20[1-2][0-9])[\s\-yY]*(?:yil|year|г|y)?\b', upper_text)
            if grad_match:
                grad_year = int(grad_match.group(1))
                extracted_fields['DATE_OF_GRADUATION'] = f"{grad_year}-07-20"
                entry_year = grad_year - degree_duration
                extracted_fields['DATE_OF_ENTRY'] = f"{entry_year}-09-02"

            # GPA Detection
            gpa_match = re.search(r'\bGPA[\s:]*([0-5]\.[0-9]{1,2})\b|\b([3-5]\.[0-9]{1,2})\b', upper_text)
            if gpa_match:
                extracted_fields['GPA'] = gpa_match.group(1) or gpa_match.group(2)

    # =========================================================================
    # 3. CONTACT INFO DETECTION
    # =========================================================================
    if doc_type == "GENERAL DOCUMENT":
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', full_ocr_text)
        phones = re.findall(r'(?:\+?998[\s-]*)?(?:9[0-9]|88|33|77|99|95|94|93|91|90)[\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}', full_ocr_text)

        if email_match or phones:
            doc_type = "CONTACT INFO"
            if email_match:
                extracted_fields['EMAIL'] = email_match.group(0)
            if len(phones) >= 1:
                extracted_fields['PHONE_NUMBER_1'] = format_phone_number(phones[0])
            if len(phones) >= 2:
                extracted_fields['PHONE_NUMBER_2'] = format_phone_number(phones[1])

            # Address line
            for line in all_raw_lines:
                l_up = line.upper()
                if any(ak in l_up for ak in ['VILOYAT', 'TUMAN', 'SHAHAR', 'REGION', 'DISTRICT', 'CITY', 'MAHALLA', 'KO\'CHA', 'STREET', 'MANZIL', 'ADDRESS']):
                    extracted_fields['ADDRESS'] = line.strip().upper()
                    break

    return {
        "document_type": doc_type,
        "fields": extracted_fields,
        "ocr_text": full_ocr_text
    }
