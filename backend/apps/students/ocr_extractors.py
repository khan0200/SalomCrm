import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from .ocr_normalizer import (
    ExtractedField,
    normalize_date,
    normalize_passport_number,
    normalize_gender,
    normalize_phone_number,
    normalize_name,
)


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

        # Check Passport / ID Card keywords from visual inspection text
        if any(k in up_clean for k in ['PASSPORT', 'PASPORT', 'REPUBLICOFUZBEKISTAN', 'OZBEKISTONRESPUBLIKASI', 'FAMILIYASI', 'TUGILGANSANASI', 'OTASININGISMI', 'BERILGANSANASI']):
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
# 2. PASSPORT EXTRACTOR (100% Visual Inspection Zone - No MRZ)
# =========================================================================
class PassportExtractor:
    @staticmethod
    def extract(ocr_lines: List[str], full_text: str, line_scores: Optional[List[float]] = None) -> Dict[str, ExtractedField]:
        fields: Dict[str, ExtractedField] = {}
        # Filter out any raw MRZ lines (<< or starting with P<) so they don't interfere
        all_raw_lines = [
            l.strip() for l in ocr_lines 
            if l.strip() and '<<' not in l and not (l.startswith('P<') or l.startswith('I<'))
        ]
        upper_text = "\n".join(all_raw_lines).upper()

        viz_surname = None
        viz_given = None
        viz_father = None
        viz_dob = None
        viz_doi = None
        viz_doe = None
        viz_sex = None
        viz_address = None

        # 1. Direct Passport Number regex (e.g. FA7958189, FA 7958189, AA1234567)
        pass_m = re.search(r'\b([A-Z]{2}\s*[\d\s]{7,10})\b', upper_text)
        if pass_m:
            clean_p = normalize_passport_number(pass_m.group(1))
            if clean_p:
                fields['PASSPORT_NUMBER'] = ExtractedField(clean_p, 0.98, True, 'VIZ')

        # 2. Visual Inspection Zone (VIZ) Label Association
        for i, raw_l in enumerate(all_raw_lines):
            up = raw_l.upper()
            clean_l = re.sub(r'[^A-ZА-Я0-9]', '', up)

            # Surname (FAMILIYASI / SURNAME)
            if any(k in clean_l for k in ['FAMILIYASI', 'SURNAME', 'ФАМИЛИЯ']) and not viz_surname:
                # Check line itself if value follows label
                after = re.sub(r'^.*?(FAMILIYASI|SURNAME|ФАМИЛИЯ)[/:\s]*', '', up).strip()
                after_clean = re.sub(r'[^A-ZА-Я0-9]', '', after)
                if after and not is_passport_header_label(after_clean) and len(after) >= 2:
                    viz_surname = after
                else:
                    for j in range(i + 1, min(i + 4, len(all_raw_lines))):
                        cand = all_raw_lines[j].strip().upper()
                        cand_clean = re.sub(r'[^A-ZА-Я0-9]', '', cand)
                        if not is_passport_header_label(cand_clean) and re.match(r'^[A-ZА-Я\s\'-]{2,}$', cand):
                            viz_surname = cand
                            break

            # Given Names (ISMI / GIVEN NAMES)
            if any(k in clean_l for k in ['ISMI', 'GIVENNAMES', 'GIVENNAME', 'ИМЯ']) and 'OTASINING' not in clean_l and not viz_given:
                after = re.sub(r'^.*?(ISMI|GIVENNAMES|GIVENNAME|ИМЯ)[/:\s]*', '', up).strip()
                after_clean = re.sub(r'[^A-ZА-Я0-9]', '', after)
                if after and not is_passport_header_label(after_clean) and len(after) >= 2:
                    viz_given = after
                else:
                    for j in range(i + 1, min(i + 4, len(all_raw_lines))):
                        cand = all_raw_lines[j].strip().upper()
                        cand_clean = re.sub(r'[^A-ZА-Я0-9]', '', cand)
                        if not is_passport_header_label(cand_clean) and re.match(r'^[A-ZА-Я\s\'-]{2,}$', cand):
                            viz_given = cand
                            break

            # Father's Name / Patronymic (OTASINING ISMI / FATHER'S NAME)
            if any(k in clean_l for k in ['OTASININGISMI', 'FATHERSNAME', 'FATHERNAME', 'ОТЧЕСТВО']) and not viz_father:
                after = re.sub(r'^.*?(OTASININGISMI|FATHERSNAME|FATHERNAME|ОТЧЕСТВО)[/:\s]*', '', up).strip()
                after_clean = re.sub(r'[^A-ZА-Я0-9]', '', after)
                if after and not is_passport_header_label(after_clean) and len(after) >= 2:
                    viz_father = after
                else:
                    for j in range(i + 1, min(i + 4, len(all_raw_lines))):
                        cand = all_raw_lines[j].strip().upper()
                        cand_clean = re.sub(r'[^A-ZА-Я0-9]', '', cand)
                        if not is_passport_header_label(cand_clean) and re.match(r'^[A-ZА-Я\s\'-]{2,}$', cand):
                            viz_father = cand
                            break

            # Date of Birth (TUG'ILGAN SANASI / DATE OF BIRTH)
            if any(k in clean_l for k in ['TUGILGANSANASI', 'DATEOFBIRTH', 'ДАТАРОЖДЕНИЯ']) and not viz_dob:
                for j in range(i, min(i + 4, len(all_raw_lines))):
                    d = normalize_date(all_raw_lines[j])
                    if d:
                        viz_dob = d
                        break

            # Date of Issue (BERILGAN SANASI / DATE OF ISSUE)
            if any(k in clean_l for k in ['BERILGANSANASI', 'DATEOFISSUE', 'ДАТАВЫДАЧИ']) and not viz_doi:
                for j in range(i, min(i + 4, len(all_raw_lines))):
                    d = normalize_date(all_raw_lines[j])
                    if d:
                        viz_doi = d
                        break

            # Date of Expiry (AMAL QILISH MUDDATI / DATE OF EXPIRY)
            if any(k in clean_l for k in ['AMALQILISHMUDDATI', 'DATEOFEXPIRY', 'DATEOFEXPIRATION', 'СРОКДЕЙСТВИЯ']) and not viz_doe:
                for j in range(i, min(i + 4, len(all_raw_lines))):
                    d = normalize_date(all_raw_lines[j])
                    if d:
                        viz_doe = d
                        break

            # Sex (JINSI / SEX)
            if any(k in clean_l for k in ['JINSI', 'SEX', 'POL']) and not viz_sex:
                for j in range(i, min(i + 4, len(all_raw_lines))):
                    g = normalize_gender(all_raw_lines[j])
                    if g:
                        viz_sex = g
                        break

            # Place of Birth (TUG'ILGAN JOYI / PLACE OF BIRTH)
            if any(k in clean_l for k in ['TUGILGANJOYI', 'PLACEOFBIRTH']) and not viz_address:
                for j in range(i + 1, min(i + 4, len(all_raw_lines))):
                    cand = all_raw_lines[j].strip().upper()
                    cand_clean = re.sub(r'[^A-ZА-Я0-9]', '', cand)
                    if not is_passport_header_label(cand_clean) and len(cand) >= 3 and not cand.isdigit():
                        viz_address = cand
                        break

        # Fallback date collection in chronological order [DOB, DOI, DOE]
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

        # Assemble Full Name (Surname + Given Names + Father's Name)
        if viz_surname or viz_given or viz_father:
            viz_name_parts = [p for p in [viz_surname, viz_given, viz_father] if p]
            full_viz_name = normalize_name(' '.join(viz_name_parts))
            if full_viz_name:
                fields['FULL_NAME'] = ExtractedField(full_viz_name, 0.98, True, 'VIZ')

        if viz_dob:
            fields['DATE_OF_BIRTH'] = ExtractedField(viz_dob, 0.97, True, 'VIZ')
        if viz_doi:
            fields['DATE_OF_ISSUE'] = ExtractedField(viz_doi, 0.95, True, 'VIZ')
        if viz_doe:
            fields['DATE_OF_EXPIRATION'] = ExtractedField(viz_doe, 0.95, True, 'VIZ')
        if viz_sex:
            fields['SEX'] = ExtractedField(viz_sex, 0.98, True, 'VIZ')
        if viz_address:
            fields['ADDRESS'] = ExtractedField(viz_address, 0.90, False, 'VIZ')

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
