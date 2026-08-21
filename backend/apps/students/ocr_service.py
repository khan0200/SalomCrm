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
        century = 2000 if yy <= 80 else 1900
    else:
        century = 2000 if yy <= current_year_last2 else 1900
    full_year = century + yy
    return f"{full_year:04d}-{mm}-{dd}"


def normalize_date_string(date_str: str) -> Optional[str]:
    """
    Parses dates in formats:
    - '02 04 2009', '02.04.2009', '02/04/2009', '02-04-2009' -> '2009-04-02'
    - '2009 04 02', '2009.04.02', '2009/04/02', '2009-04-02' -> '2009-04-02'
    - '02042009' -> '2009-04-02'
    - '2006 2028' (e.g. 20 06 2028 where first space missed) -> '2028-06-20'
    - '21062023' -> '2023-06-21'
    """
    if not date_str:
        return None
    
    clean = re.sub(r'[^\d\.\-\/\s]', '', date_str.strip())
    parts = [p for p in re.split(r'[\s\.\-\/]+', clean) if p]
    
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

    digits = re.sub(r'\D', '', date_str)
    if len(digits) == 8:
        try:
            d, m, y = int(digits[:2]), int(digits[2:4]), int(digits[4:])
            if 1900 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31:
                return f"{y:04d}-{m:02d}-{d:02d}"
            y, m, d = int(digits[:4]), int(digits[4:6]), int(digits[6:])
            if 1900 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31:
                return f"{y:04d}-{m:02d}-{d:02d}"
        except Exception:
            pass

    return None


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


def is_passport_label(line_up: str) -> bool:
    """Returns True if the line is a passport field header/label."""
    clean = re.sub(r'[^A-ZА-Я]', '', line_up.upper())
    if not clean:
        return True
    labels = [
        'TURI', 'TYPE', 'DAVLATKODI', 'COUNTRYCODE', 'PASPORTRAQAMI', 'PASSPORTNO',
        'PASSPORT', 'PASPORT', 'FAMILIYASI', 'SURNAME', 'ISMI', 'GIVENNAMES', 'GIVENNAME',
        'OTASININGISMI', 'FATHERSNAME', 'FATHERNAME', 'FUQAROLIGI', 'NATIONALITY',
        'TUGILGANSANASI', 'DATEOFBIRTH', 'JINSI', 'SEX', 'POL',
        'TUGILGANJOYI', 'PLACEOFBIRTH', 'BERILGANSANASI', 'DATEOFISSUE',
        'AMALQILISHMUDDATI', 'DATEOFEXPIRY', 'DATEOFEXPIRATION', 'KIMTOMONIDAN',
        'AUTHORITY', 'REPUBLICOFUZBEKISTAN', 'OZBEKISTONRESPUBLIKASI', 'RESPUBLIKASI'
    ]
    return any(lbl in clean for lbl in labels)


def extract_document_from_bytes(file_bytes: bytes, filename: str = '') -> Dict[str, Any]:
    """
    Extracts text and structured fields from an uploaded image or PDF in RAM memory.
    """
    is_pdf = filename.lower().endswith('.pdf') or file_bytes.startswith(b'%PDF')
    images: List[Image.Image] = []

    if is_pdf:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        for page_num in range(min(len(doc), 3)):
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
    mrz_lines = []
    for line in all_raw_lines:
        clean = line.replace(' ', '').upper()
        if '<<' in clean and len(clean) >= 28:
            mrz_lines.append(clean)

    mrz_success = False

    # Check TD3 MRZ (2 lines of 44 chars)
    if len(mrz_lines) >= 2:
        for i in range(len(mrz_lines) - 1):
            l1 = mrz_lines[i]
            l2 = mrz_lines[i+1]
            if (l1.startswith('P<') or l1.startswith('P')) and len(l1) >= 38 and len(l2) >= 38:
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

    # =========================================================================
    # 2. VISUAL INSPECTION ZONE (VIZ) PARSING (Cropped or clear photo scans)
    # =========================================================================
    is_passport_doc = (
        mrz_success or
        any(k in upper_text for k in ['PASSPORT', 'PASPORT', 'REPUBLIC OF UZBEKISTAN', 'O\'ZBEKISTON RESPUBLIKASI', 'FAMILIYASI', 'SURNAME', 'FA7', 'FA8', 'FA9', 'AA', 'AB'])
    )

    if is_passport_doc:
        doc_type = "PASSPORT"

        # 2.1 Passport Number (e.g. FA7958189, FA 7958189, AB1234567)
        if 'PASSPORT_NUMBER' not in extracted_fields:
            pass_match = re.search(r'\b([A-Z]{2}\s*\d{7})\b', upper_text)
            if pass_match:
                extracted_fields['PASSPORT_NUMBER'] = pass_match.group(1).replace(' ', '')

        # 2.2 Visual Inspection Zone: Surname, Given Names, Father's Name, Dates, Sex
        viz_surname = None
        viz_given = None
        viz_father = None
        viz_dob = None
        viz_doi = None
        viz_doe = None
        viz_sex = None
        viz_address = None

        for i, raw_l in enumerate(all_raw_lines):
            l = raw_l.strip()
            up = l.upper()
            up_clean = re.sub(r'[^A-ZА-Я0-9]', '', up)

            # SURNAME
            if any(k in up_clean for k in ['FAMILIYASI', 'SURNAME', 'ФАМИЛИЯ']) and not viz_surname:
                for j in range(i + 1, min(i + 4, len(all_raw_lines))):
                    cand = all_raw_lines[j].strip().upper()
                    if not is_passport_label(cand) and re.match(r'^[A-ZА-Я\s\'-]{2,}$', cand):
                        viz_surname = cand
                        break

            # GIVEN NAMES
            if any(k in up_clean for k in ['ISMI', 'GIVENNAMES', 'GIVENNAME', 'ИМЯ']) and 'OTASINING' not in up_clean and not viz_given:
                for j in range(i + 1, min(i + 4, len(all_raw_lines))):
                    cand = all_raw_lines[j].strip().upper()
                    if not is_passport_label(cand) and re.match(r'^[A-ZА-Я\s\'-]{2,}$', cand):
                        viz_given = cand
                        break

            # FATHER'S NAME / PATRONYMIC
            if any(k in up_clean for k in ['OTASININGISMI', 'FATHERSNAME', 'FATHERNAME', 'ОТЧЕСТВО']) and not viz_father:
                for j in range(i + 1, min(i + 4, len(all_raw_lines))):
                    cand = all_raw_lines[j].strip().upper()
                    if not is_passport_label(cand) and re.match(r'^[A-ZА-Я\s\'-]{2,}$', cand):
                        viz_father = cand
                        break

            # DATE OF BIRTH
            if any(k in up_clean for k in ['TUGILGANSANASI', 'DATEOFBIRTH', 'ДАТАРОЖДЕНИЯ']) and not viz_dob:
                for j in range(i, min(i + 4, len(all_raw_lines))):
                    d = normalize_date_string(all_raw_lines[j])
                    if d:
                        viz_dob = d
                        break

            # DATE OF ISSUE
            if any(k in up_clean for k in ['BERILGANSANASI', 'DATEOFISSUE', 'ДАТАВЫДАЧИ']) and not viz_doi:
                for j in range(i, min(i + 4, len(all_raw_lines))):
                    d = normalize_date_string(all_raw_lines[j])
                    if d:
                        viz_doi = d
                        break

            # DATE OF EXPIRY
            if any(k in up_clean for k in ['AMALQILISHMUDDATI', 'DATEOFEXPIRY', 'DATEOFEXPIRATION', 'СРОКДЕЙСТВИЯ']) and not viz_doe:
                for j in range(i, min(i + 4, len(all_raw_lines))):
                    d = normalize_date_string(all_raw_lines[j])
                    if d:
                        viz_doe = d
                        break

            # SEX
            if any(k in up_clean for k in ['JINSI', 'SEX', 'POL']) and not viz_sex:
                for j in range(i, min(i + 4, len(all_raw_lines))):
                    cand = all_raw_lines[j].strip().upper()
                    if cand in ('M', 'MALE', 'ERKAK'):
                        viz_sex = 'MALE'
                        break
                    elif cand in ('F', 'FEMALE', 'AYOL'):
                        viz_sex = 'FEMALE'
                        break

            # PLACE OF BIRTH / ADDRESS
            if any(k in up_clean for k in ['TUGILGANJOYI', 'PLACEOFBIRTH']) and not viz_address:
                for j in range(i + 1, min(i + 4, len(all_raw_lines))):
                    cand = all_raw_lines[j].strip().upper()
                    if not is_passport_label(cand) and len(cand) >= 3 and not cand.isdigit():
                        viz_address = cand
                        break

        # Fallback for dates by scanning all 3-part dates in document if any missing
        all_found_dates = []
        for line in all_raw_lines:
            d = normalize_date_string(line)
            if d and d not in all_found_dates:
                all_found_dates.append(d)

        # In standard passports, dates ordered chronologically: [DOB, DOI, DOE]
        if all_found_dates:
            sorted_dates = sorted(all_found_dates)
            if not viz_dob and len(sorted_dates) >= 1:
                viz_dob = sorted_dates[0]
            if not viz_doe and len(sorted_dates) >= 2:
                viz_doe = sorted_dates[-1]
            if not viz_doi and len(sorted_dates) >= 3:
                viz_doi = sorted_dates[1]

        # Assemble Full Name
        if 'FULL_NAME' not in extracted_fields:
            name_parts = [p for p in [viz_surname, viz_given, viz_father] if p]
            if name_parts:
                extracted_fields['FULL_NAME'] = ' '.join(name_parts)

        # Dates & Attributes fallback
        if 'DATE_OF_BIRTH' not in extracted_fields and viz_dob:
            extracted_fields['DATE_OF_BIRTH'] = viz_dob
        if 'DATE_OF_ISSUE' not in extracted_fields and viz_doi:
            extracted_fields['DATE_OF_ISSUE'] = viz_doi
        if 'DATE_OF_EXPIRATION' not in extracted_fields and viz_doe:
            extracted_fields['DATE_OF_EXPIRATION'] = viz_doe
        if 'SEX' not in extracted_fields and viz_sex:
            extracted_fields['SEX'] = viz_sex
        if 'ADDRESS' not in extracted_fields and viz_address:
            extracted_fields['ADDRESS'] = viz_address

    # =========================================================================
    # 3. DIPLOMA & SHAHODATNOMA DETECTION
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

            # Degree / Certificate Serial Number
            deg_match = re.search(r'([A-ZА-Я]{1,3}\s*(?:№|N|NO\.?)\s*\d{6,8}|\b\d{7,8}\b)', upper_text)
            if deg_match:
                extracted_fields['DEGREE_NO'] = deg_match.group(1)

            # School Name Detection
            for line in all_raw_lines:
                l_up = line.upper()
                if any(sk in l_up for sk in ['UNIVERSITET', 'UNIVERSITY', 'INSTITUT', 'INSTITUTE', 'AKADEMIYA', 'ACADEMY', 'MAKTAB', 'SCHOOL', 'KOLLEJ', 'COLLEGE', 'LITSEY', 'LYCEUM']):
                    extracted_fields['FINAL_SCHOOL_NAME'] = line.strip().upper()
                    break

            # Major Detection
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
    # 4. CONTACT INFO DETECTION
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
