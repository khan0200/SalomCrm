import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from mrz.checker.td3 import TD3CodeChecker
from mrz.checker.td1 import TD1CodeChecker
from mrz.checker.td2 import TD2CodeChecker

from .ocr_normalizer import (
    ExtractedField,
    normalize_date,
    normalize_passport_number,
    normalize_gender,
    normalize_phone_number,
    normalize_name,
)


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


def is_passport_header_label(clean_up: str) -> bool:
    """Returns True if the string is a passport field header/label."""
    labels = [
        'TURI', 'TYPE', 'DAVLATKODI', 'COUNTRYCODE', 'PASPORTRAQAMI', 'PASSPORTNO',
        'PASSPORT', 'PASPORT', 'FAMILIYASI', 'SURNAME', 'ISMI', 'GIVENNAMES', 'GIVENNAME',
        'OTASININGISMI', 'FATHERSNAME', 'FATHERNAME', 'FUQAROLIGI', 'NATIONALITY',
        'TUGILGANSANASI', 'DATEOFBIRTH', 'JINSI', 'SEX', 'POL',
        'TUGILGANJOYI', 'PLACEOFBIRTH', 'BERILGANSANASI', 'DATEOFISSUE',
        'AMALQILISHMUDDATI', 'DATEOFEXPIRY', 'DATEOFEXPIRATION', 'KIMTOMONIDAN',
        'AUTHORITY', 'REPUBLICOFUZBEKISTAN', 'OZBEKISTONRESPUBLIKASI', 'RESPUBLIKASI'
    ]
    return any(lbl in clean_up for lbl in labels)


# =========================================================================
# 1. DOCUMENT CLASSIFIER
# =========================================================================
class DocumentClassifier:
    @staticmethod
    def classify(ocr_lines: List[str], full_text: str) -> str:
        up = full_text.upper()
        up_clean = re.sub(r'[^A-ZА-Я0-9]', '', up)

        # Check for MRZ lines
        mrz_count = sum(1 for line in ocr_lines if '<<' in line.replace(' ', '') and len(line.replace(' ', '')) >= 26)
        if mrz_count >= 2:
            return "PASSPORT"

        # Check Passport / ID Card keywords
        if any(k in up_clean for k in ['PASSPORT', 'PASPORT', 'REPUBLICOFUZBEKISTAN', 'OZBEKISTONRESPUBLIKASI', 'FAMILIYASI', 'TUGILGANSANASI']):
            return "PASSPORT"

        if any(k in up_clean for k in ['IDCARD', 'IDENTIFICATIONCARD', 'IDKARTA']):
            return "ID_CARD"

        # Check Diploma keywords
        if any(k in up_clean for k in ['DIPLOM', 'DIPLOMA', 'BAKALAVR', 'MAGISTR', 'BACHELOR', 'MASTER']):
            return "DIPLOMA"

        # Check School Certificate keywords
        if any(k in up_clean for k in ['SHAHODATNOMA', 'ATTESTAT', 'GENERALSECONDARYEDUCATION', 'ORTATALIM']):
            return "SCHOOL_CERTIFICATE"

        # Check Contact Screenshot keywords
        has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', full_text))
        has_phone = bool(re.search(r'(?:\+?998[\s-]*)?(?:9[0-9]|88|33|77|99|95|94|93|91|90)[\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}', full_text))
        if has_email or has_phone:
            return "CONTACT_SCREENSHOT"

        return "UNKNOWN"


# =========================================================================
# 2. PASSPORT EXTRACTOR
# =========================================================================
class PassportExtractor:
    @staticmethod
    def extract(ocr_lines: List[str], full_text: str, line_scores: Optional[List[float]] = None) -> Dict[str, ExtractedField]:
        fields: Dict[str, ExtractedField] = {}
        all_raw_lines = [l.strip() for l in ocr_lines if l.strip()]
        upper_text = full_text.upper()

        # Step 1: MRZ Parsing & Check Digit Verification
        mrz_lines = [l.replace(' ', '').upper() for l in all_raw_lines if '<<' in l.replace(' ', '') and len(l.replace(' ', '')) >= 26]
        mrz_success = False

        if len(mrz_lines) >= 2:
            for i in range(len(mrz_lines) - 1):
                l1 = mrz_lines[i]
                l2 = mrz_lines[i+1]
                if (l1.startswith('P<') or l1.startswith('P')) and len(l1) >= 36 and len(l2) >= 36:
                    l1_pad = (l1 + '<'*44)[:44]
                    l2_pad = (l2 + '<'*44)[:44]
                    try:
                        checker = TD3CodeChecker(f"{l1_pad}\n{l2_pad}")
                        mrz_fields = checker.fields()
                        check_digits_valid = bool(checker.result)

                        surname = (mrz_fields.surname or '').replace('<', ' ').strip()
                        given = (mrz_fields.names or '').replace('<', ' ').strip()
                        full_name = normalize_name(f"{surname} {given}".strip())

                        passport_num = normalize_passport_number(mrz_fields.document_number or '')
                        sex = normalize_gender(mrz_fields.sex or '')
                        dob = parse_mrz_date(mrz_fields.birth_date, is_expiration=False)
                        expiry = parse_mrz_date(mrz_fields.expiry_date, is_expiration=True)

                        base_conf = 0.98 if check_digits_valid else 0.85

                        if full_name:
                            fields['FULL_NAME'] = ExtractedField(full_name, base_conf, check_digits_valid, 'MRZ')
                        if passport_num:
                            fields['PASSPORT_NUMBER'] = ExtractedField(passport_num, base_conf, check_digits_valid, 'MRZ')
                        if dob:
                            fields['DATE_OF_BIRTH'] = ExtractedField(dob, base_conf, check_digits_valid, 'MRZ')
                        if expiry:
                            fields['DATE_OF_EXPIRATION'] = ExtractedField(expiry, base_conf, check_digits_valid, 'MRZ')
                        if sex:
                            fields['SEX'] = ExtractedField(sex, base_conf, check_digits_valid, 'MRZ')

                        mrz_success = True
                        break
                    except Exception:
                        pass

        # Step 2: Visual Inspection Zone (VIZ) Association
        viz_surname = None
        viz_given = None
        viz_father = None
        viz_dob = None
        viz_doi = None
        viz_doe = None
        viz_sex = None
        viz_address = None

        # Direct Passport Number regex
        if 'PASSPORT_NUMBER' not in fields:
            pass_m = re.search(r'\b([A-Z]{2}\s*[\d\s]{7,10})\b', upper_text)
            if pass_m:
                clean_p = normalize_passport_number(pass_m.group(1))
                if clean_p:
                    fields['PASSPORT_NUMBER'] = ExtractedField(clean_p, 0.95, True, 'VIZ')

        for i, raw_l in enumerate(all_raw_lines):
            up = raw_l.upper()
            clean_l = re.sub(r'[^A-ZА-Я0-9]', '', up)

            # Surname
            if any(k in clean_l for k in ['FAMILIYASI', 'SURNAME', 'ФАМИЛИЯ']) and not viz_surname:
                for j in range(i + 1, min(i + 4, len(all_raw_lines))):
                    cand = all_raw_lines[j].strip().upper()
                    cand_clean = re.sub(r'[^A-ZА-Я0-9]', '', cand)
                    if not is_passport_header_label(cand_clean) and re.match(r'^[A-ZА-Я\s\'-]{2,}$', cand):
                        viz_surname = cand
                        break

            # Given Name
            if any(k in clean_l for k in ['ISMI', 'GIVENNAMES', 'GIVENNAME', 'ИМЯ']) and 'OTASINING' not in clean_l and not viz_given:
                for j in range(i + 1, min(i + 4, len(all_raw_lines))):
                    cand = all_raw_lines[j].strip().upper()
                    cand_clean = re.sub(r'[^A-ZА-Я0-9]', '', cand)
                    if not is_passport_header_label(cand_clean) and re.match(r'^[A-ZА-Я\s\'-]{2,}$', cand):
                        viz_given = cand
                        break

            # Father's Name / Patronymic
            if any(k in clean_l for k in ['OTASININGISMI', 'FATHERSNAME', 'FATHERNAME', 'ОТЧЕСТВО']) and not viz_father:
                for j in range(i + 1, min(i + 4, len(all_raw_lines))):
                    cand = all_raw_lines[j].strip().upper()
                    cand_clean = re.sub(r'[^A-ZА-Я0-9]', '', cand)
                    if not is_passport_header_label(cand_clean) and re.match(r'^[A-ZА-Я\s\'-]{2,}$', cand):
                        viz_father = cand
                        break

            # Date of Birth
            if any(k in clean_l for k in ['TUGILGANSANASI', 'DATEOFBIRTH', 'ДАТАРОЖДЕНИЯ']) and not viz_dob:
                for j in range(i, min(i + 4, len(all_raw_lines))):
                    d = normalize_date(all_raw_lines[j])
                    if d:
                        viz_dob = d
                        break

            # Date of Issue
            if any(k in clean_l for k in ['BERILGANSANASI', 'DATEOFISSUE', 'ДАТАВЫДАЧИ']) and not viz_doi:
                for j in range(i, min(i + 4, len(all_raw_lines))):
                    d = normalize_date(all_raw_lines[j])
                    if d:
                        viz_doi = d
                        break

            # Date of Expiry
            if any(k in clean_l for k in ['AMALQILISHMUDDATI', 'DATEOFEXPIRY', 'DATEOFEXPIRATION', 'СРОКДЕЙСТВИЯ']) and not viz_doe:
                for j in range(i, min(i + 4, len(all_raw_lines))):
                    d = normalize_date(all_raw_lines[j])
                    if d:
                        viz_doe = d
                        break

            # Sex
            if any(k in clean_l for k in ['JINSI', 'SEX', 'POL']) and not viz_sex:
                for j in range(i, min(i + 4, len(all_raw_lines))):
                    g = normalize_gender(all_raw_lines[j])
                    if g:
                        viz_sex = g
                        break

            # Place of Birth
            if any(k in clean_l for k in ['TUGILGANJOYI', 'PLACEOFBIRTH']) and not viz_address:
                for j in range(i + 1, min(i + 4, len(all_raw_lines))):
                    cand = all_raw_lines[j].strip().upper()
                    cand_clean = re.sub(r'[^A-ZА-Я0-9]', '', cand)
                    if not is_passport_header_label(cand_clean) and len(cand) >= 3 and not cand.isdigit():
                        viz_address = cand
                        break

        # Fallback date collection in chronological order
        all_found_dates = []
        for line in all_raw_lines:
            d = normalize_date(line)
            if d and d not in all_found_dates:
                all_found_dates.append(d)

        if all_found_dates:
            sorted_dates = sorted(all_found_dates)
            if not viz_dob and len(sorted_dates) >= 1:
                viz_dob = sorted_dates[0]
            if not viz_doe and len(sorted_dates) >= 2:
                viz_doe = sorted_dates[-1]
            if not viz_doi and len(sorted_dates) >= 3:
                viz_doi = sorted_dates[1]

        # Combine VIZ Full Name (with Patronymic)
        if viz_surname or viz_given or viz_father:
            viz_name_parts = [p for p in [viz_surname, viz_given, viz_father] if p]
            full_viz_name = normalize_name(' '.join(viz_name_parts))
            # If MRZ only had surname + given, replace with richer VIZ full name including patronymic
            if full_viz_name:
                fields['FULL_NAME'] = ExtractedField(full_viz_name, 0.96, True, 'VIZ')

        if 'DATE_OF_BIRTH' not in fields and viz_dob:
            fields['DATE_OF_BIRTH'] = ExtractedField(viz_dob, 0.94, True, 'VIZ')
        if 'DATE_OF_ISSUE' not in fields and viz_doi:
            fields['DATE_OF_ISSUE'] = ExtractedField(viz_doi, 0.93, True, 'VIZ')
        if 'DATE_OF_EXPIRATION' not in fields and viz_doe:
            fields['DATE_OF_EXPIRATION'] = ExtractedField(viz_doe, 0.93, True, 'VIZ')
        if 'SEX' not in fields and viz_sex:
            fields['SEX'] = ExtractedField(viz_sex, 0.95, True, 'VIZ')
        if 'ADDRESS' not in fields and viz_address:
            fields['ADDRESS'] = ExtractedField(viz_address, 0.88, False, 'VIZ')

        return fields


# =========================================================================
# 3. DIPLOMA & SCHOOL CERTIFICATE EXTRACTOR
# =========================================================================
class DiplomaExtractor:
    @staticmethod
    def extract(ocr_lines: List[str], full_text: str, is_shahodatnoma: bool = False) -> Dict[str, ExtractedField]:
        fields: Dict[str, ExtractedField] = {}
        all_raw_lines = [l.strip() for l in ocr_lines if l.strip()]
        upper_text = full_text.upper()

        degree_duration = 3 if is_shahodatnoma else (2 if 'MAGISTR' in upper_text or 'MASTER' in upper_text else 4)

        if is_shahodatnoma:
            fields['MAJOR'] = ExtractedField("GENERAL SECONDARY EDUCATION", 0.98, True, 'CALCULATED')

        # 1. Degree / Certificate Serial Number
        deg_match = re.search(r'(?:SERIYA|SERIES|№|N|NO\.?)[:\s\-]*([A-ZА-Я]{0,3}\s*(?:№|N|NO\.?)?\s*\d{6,8})|\b([A-ZА-Я]{1,3}\s*\d{6,8})\b|\b(\d{7,8})\b', upper_text)
        if deg_match:
            deg_val = deg_match.group(1) or deg_match.group(2) or deg_match.group(3)
            if deg_val:
                fields['DEGREE_NO'] = ExtractedField(deg_val.strip(), 0.92, True, 'OCR_REGEX')

        # 2. School Name
        for line in all_raw_lines:
            l_up = line.upper()
            if any(sk in l_up for sk in ['UNIVERSITET', 'UNIVERSITY', 'INSTITUT', 'INSTITUTE', 'AKADEMIYA', 'ACADEMY', 'MAKTAB', 'SCHOOL', 'KOLLEJ', 'COLLEGE', 'LITSEY', 'LYCEUM']):
                clean_sch = re.sub(r'\s+', ' ', line).strip().upper()
                if len(clean_sch) >= 6:
                    fields['FINAL_SCHOOL_NAME'] = ExtractedField(clean_sch, 0.90, False, 'LAYOUT')
                    break

        # 3. Major
        if not is_shahodatnoma:
            for line in all_raw_lines:
                l_up = line.upper()
                if any(mk in l_up for mk in ['MUTAXASSISLIGI', 'YO\'NALISHI', 'YONALISHI', 'MAJOR', 'SPECIALTY', 'SPECIALITY', 'FIELD OF STUDY']):
                    clean_major = re.sub(r'^(MUTAXASSISLIGI|YO\'NALISHI|YONALISHI|MAJOR|SPECIALTY|SPECIALITY)[:\s\-]+', '', l_up).strip()
                    if clean_major and len(clean_major) >= 3:
                        fields['MAJOR'] = ExtractedField(clean_major, 0.88, False, 'LAYOUT')
                        break

        # 4. Graduation Date & Computed Entry Date
        grad_match = re.search(r'\b(20[1-2][0-9])[\s\-yY]*(?:yil|year|г|y)?\b', upper_text)
        if grad_match:
            grad_year = int(grad_match.group(1))
            fields['DATE_OF_GRADUATION'] = ExtractedField(f"{grad_year}-07-20", 0.95, True, 'CALCULATED')
            entry_year = grad_year - degree_duration
            fields['DATE_OF_ENTRY'] = ExtractedField(f"{entry_year}-09-02", 0.95, True, 'CALCULATED')

        # 5. GPA
        gpa_match = re.search(r'\bGPA[\s:]*([0-5]\.[0-9]{1,2})\b|\b([3-5]\.[0-9]{1,2})\b', upper_text)
        if gpa_match:
            gpa_val = gpa_match.group(1) or gpa_match.group(2)
            fields['GPA'] = ExtractedField(gpa_val, 0.85, True, 'OCR_REGEX')

        return fields


# =========================================================================
# 4. CONTACT SCREENSHOT EXTRACTOR
# =========================================================================
class ContactScreenshotExtractor:
    @staticmethod
    def extract(ocr_lines: List[str], full_text: str) -> Dict[str, ExtractedField]:
        fields: Dict[str, ExtractedField] = {}
        all_raw_lines = [l.strip() for l in ocr_lines if l.strip()]

        # 1. Email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', full_text)
        if email_match:
            fields['EMAIL'] = ExtractedField(email_match.group(0), 0.97, True, 'OCR_REGEX')

        # 2. Phone numbers
        phones = re.findall(r'(?:\+?998[\s-]*)?(?:9[0-9]|88|33|77|99|95|94|93|91|90)[\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}', full_text)
        if len(phones) >= 1:
            fields['PHONE_NUMBER_1'] = ExtractedField(normalize_phone_number(phones[0]), 0.95, True, 'OCR_REGEX')
        if len(phones) >= 2:
            fields['PHONE_NUMBER_2'] = ExtractedField(normalize_phone_number(phones[1]), 0.95, True, 'OCR_REGEX')

        # 3. Address / Location line
        for line in all_raw_lines:
            l_up = line.upper()
            if any(ak in l_up for ak in ['VILOYAT', 'TUMAN', 'SHAHAR', 'REGION', 'DISTRICT', 'CITY', 'MAHALLA', 'KO\'CHA', 'STREET', 'MANZIL', 'ADDRESS']):
                fields['ADDRESS'] = ExtractedField(line.strip().upper(), 0.85, False, 'LAYOUT')
                break

        return fields
