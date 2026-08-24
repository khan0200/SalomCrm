import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from .ocr_normalizer import (
    ExtractedField,
    normalize_date,
    extract_dates_from_text,
    normalize_passport_number,
    normalize_gender,
    normalize_phone_number,
    normalize_name,
    normalize_patronymic,
    normalize_address,
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

        # 1. Check Diploma & University/College keywords first (Bachelor, Master, Diploma)
        if any(k in up_clean for k in ['BACHELORDIPLOMA', 'BACHELORSDIPLOMA', 'BACHELOR', 'BAKALAVR', 'MASTERDIPLOMA', 'MAGISTR', 'DIPLOM', 'DIPLOMA', 'TECHNICUM', 'TEXNIKUM', 'TEHNIKUM', 'KOLLEJ', 'ACADEMICLYCEUM']):
            return "DIPLOMA"

        # 2. Check School Certificate & Attestat keywords
        if any(k in up_clean for k in ['SHAHODATNOMA', 'ATTESTAT', 'ATTECTAT', 'GENERALSECONDARYEDUCATION', 'ORTATALIM', 'TALIMTOGRISIDA', 'USHBUSHAHODATNOMA', 'AVERAGEOF6YEARGRADES', 'BAHOLARIORTACHA']):
            return "SCHOOL_CERTIFICATE"

        # 3. Check ID Card keywords
        if any(k in up_clean for k in ['IDCARD', 'IDENTIFICATIONCARD', 'IDKARTA']):
            return "ID_CARD"

        # 4. Check Passport keywords
        if any(k in up_clean for k in ['PASSPORT', 'PASPORT', 'PASPORTRAQAMI', 'PASSPORTNO', 'DAVLATKODI', 'COUNTRYCODE', 'AMALQILISHMUDDATI']):
            return "PASSPORT"

        # 5. Check Contact Screenshot keywords
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
                    viz_father = normalize_patronymic(after)
                else:
                    for j in range(i + 1, min(i + 4, len(all_raw_lines))):
                        cand = all_raw_lines[j].strip().upper()
                        cand_clean = re.sub(r'[^A-ZА-Я0-9]', '', cand)
                        if not is_passport_header_label(cand_clean) and re.match(r'^[A-ZА-Я\s\'-]{2,}$', cand):
                            viz_father = normalize_patronymic(cand)
                            break

            # Place of Birth / Address (TUG'ILGAN JOYI / PLACE OF BIRTH)
            is_pob_label = any(k in clean_l for k in ['TUGILGANJOYI', 'PLACEOFBIRTH', 'МЕСТОРОЖДЕНИЯ', 'TUGILGANJOYL'])
            if is_pob_label and not viz_address:
                after = re.sub(r'^.*?(TUGILGANJOYI|PLACEOFBIRTH|МЕСТОРОЖДЕНИЯ|TUGILGANJOYL|TUG\'ILGAN JOYI|PLACE OF BIRTH)[/:\s]*', '', up, flags=re.IGNORECASE).strip()
                after_clean = re.sub(r'[^A-ZА-Я0-9]', '', after)
                if after and not is_passport_header_label(after_clean) and len(after) >= 3 and after not in ('M', 'F') and not re.match(r'^[\d\s\.\-\/]+$', after):
                    viz_address = normalize_address(after)
                else:
                    for j in range(i + 1, min(i + 4, len(all_raw_lines))):
                        cand = all_raw_lines[j].strip().upper()
                        cand_clean = re.sub(r'[^A-ZА-Я0-9]', '', cand)
                        if not is_passport_header_label(cand_clean) and len(cand) >= 3 and cand not in ('M', 'F') and not re.match(r'^[\d\s\.\-\/]+$', cand):
                            viz_address = normalize_address(cand)
                            break

            # Date of Birth (TUG'ILGAN SANASI / DATE OF BIRTH)
            is_pob = any(k in clean_l for k in ['TUGILGANJOYI', 'PLACEOFBIRTH', 'МЕСТОРОЖДЕНИЯ', 'TUGILGANJOYL'])
            is_dob_label = any(k in clean_l for k in ['TUGILGANSANASI', 'DATEOFBIRTH', 'DATEOFB', 'ДАТАРОЖДЕНИЯ', 'BIRTHDATE', 'TUGILGANKUNI', 'TUGILGANYILI'])
            if (is_dob_label or ('TUGILGAN' in clean_l and not is_pob)) and not viz_dob:
                for j in range(i, min(i + 4, len(all_raw_lines))):
                    dates = extract_dates_from_text(all_raw_lines[j])
                    birth_dates = [d for d in dates if int(d[:4]) <= 2018]
                    if birth_dates:
                        viz_dob = birth_dates[0]
                        break
                    elif dates and not viz_dob:
                        viz_dob = dates[0]

            # Date of Issue (BERILGAN SANASI / DATE OF ISSUE)
            if any(k in clean_l for k in ['BERILGANSANASI', 'DATEOFISSUE', 'ДАТАВЫДАЧИ', 'ISSUEDATE', 'BERILGANKUNI', 'BERILGANYILI']) and not viz_doi:
                for j in range(i, min(i + 4, len(all_raw_lines))):
                    dates = extract_dates_from_text(all_raw_lines[j])
                    if dates:
                        viz_doi = dates[0]
                        break

            # Date of Expiry (AMAL QILISH MUDDATI / DATE OF EXPIRY)
            if any(k in clean_l for k in ['AMALQILISHMUDDATI', 'AMALQILISH', 'DATEOFEXPIRY', 'DATEOFEXPIRATION', 'EXPIRYDATE', 'EXPIRATIONDATE', 'СРОКДЕЙСТВИЯ']) and not viz_doe:
                for j in range(i, min(i + 4, len(all_raw_lines))):
                    dates = extract_dates_from_text(all_raw_lines[j])
                    if dates:
                        viz_doe = dates[0]
                        break

            # Sex (JINSI / SEX - handles OCR reading JINSLSEX / JINSI/SEX)
            if any(k in clean_l for k in ['JINSI', 'JINSL', 'SEX', 'POL']) and not viz_sex:
                for j in range(i, min(i + 4, len(all_raw_lines))):
                    g = normalize_gender(all_raw_lines[j])
                    if g:
                        viz_sex = g
                        break

        # Standalone sex fallback (search for isolated 'M' or 'F' lines)
        if not viz_sex:
            for line in all_raw_lines:
                clean_single = line.strip().upper()
                if clean_single in ('M', 'F'):
                    viz_sex = 'MALE' if clean_single == 'M' else 'FEMALE'
                    break

        # Standalone address/region fallback (search for Region/City names)
        if not viz_address:
            for line in all_raw_lines:
                cand = line.strip().upper()
                cand_clean = re.sub(r'[^A-ZА-Я0-9]', '', cand)
                if any(rk in cand_clean for rk in ['REGION', 'VILOYATI', 'VILOYAT', 'TUMANI', 'TUMAN', 'SHAHAR', 'SHAHRI']) and not is_passport_header_label(cand_clean):
                    viz_address = normalize_address(cand)
                    break

        # 3. Comprehensive Global Document Date Disambiguation & Cross-Validation
        all_doc_dates: List[str] = []
        for d in extract_dates_from_text(upper_text):
            if d not in all_doc_dates:
                all_doc_dates.append(d)
        doc_dates = sorted(all_doc_dates)

        birth_candidates = [d for d in doc_dates if 1940 <= int(d[:4]) <= 2018]
        issue_candidates = [d for d in doc_dates if 2000 <= int(d[:4]) <= 2026]
        expiry_candidates = [d for d in doc_dates if 2024 <= int(d[:4]) <= 2040]

        # Reconcile Date of Birth (must NEVER be equal to Issue/Expiry date or in future)
        if not viz_dob or int(viz_dob[:4]) > 2018 or viz_dob == viz_doi or viz_dob == viz_doe:
            if birth_candidates:
                viz_dob = birth_candidates[0]
            elif len(doc_dates) >= 3 and doc_dates[0] != viz_doi and doc_dates[0] != viz_doe:
                viz_dob = doc_dates[0]
            else:
                viz_dob = None

        # Reconcile Date of Issue
        if not viz_doi or (viz_dob and viz_doi <= viz_dob):
            valid_issues = [d for d in issue_candidates if not viz_dob or d > viz_dob]
            if valid_issues:
                viz_doi = valid_issues[0]
            elif len(doc_dates) >= 2:
                remaining = [d for d in doc_dates if d != (viz_dob or '') and d != (viz_doe or '')]
                if remaining:
                    viz_doi = remaining[0]

        # Reconcile Date of Expiry
        if not viz_doe or (viz_doi and viz_doe <= viz_doi):
            valid_expiries = [d for d in expiry_candidates if not viz_doi or d > viz_doi]
            if valid_expiries:
                viz_doe = valid_expiries[-1]
            elif doc_dates and doc_dates[-1] != (viz_dob or '') and doc_dates[-1] != (viz_doi or ''):
                viz_doe = doc_dates[-1]

        # Invariant check: DOB strictly < DOI < DOE
        if viz_dob and viz_doi and viz_dob >= viz_doi:
            if birth_candidates:
                viz_dob = birth_candidates[0]
            else:
                viz_dob = None

        # Assemble Full Name (Surname + Given Names + Father's Name)
        if viz_surname or viz_given or viz_father:
            viz_name_parts = [p for p in [viz_surname, viz_given, viz_father] if p]
            full_viz_name = normalize_name(' '.join(viz_name_parts))
            if full_viz_name:
                fields['FULL_NAME'] = ExtractedField(full_viz_name, 0.98, True, 'VIZ')

        if viz_father:
            fields['FATHER_FULLNAME'] = ExtractedField(viz_father, 0.95, True, 'VIZ')
        if viz_dob:
            fields['DATE_OF_BIRTH'] = ExtractedField(viz_dob, 0.97, True, 'VIZ')
        if viz_doi:
            fields['DATE_OF_ISSUE'] = ExtractedField(viz_doi, 0.95, True, 'VIZ')
        if viz_doe:
            fields['DATE_OF_EXPIRATION'] = ExtractedField(viz_doe, 0.95, True, 'VIZ')
        if viz_sex:
            fields['SEX'] = ExtractedField(viz_sex, 0.98, True, 'VIZ')
        if viz_address:
            fields['ADDRESS'] = ExtractedField(viz_address, 0.95, True, 'VIZ')

        return fields


def translate_uzbek_school_name(raw_school_text: str, place_of_issue: str = '') -> str:
    """
    Translates Uzbek and Russian school names & locations into clean English.
    """
    s = raw_school_text.strip()
    s = re.sub(r'\bANDIIAN\b', 'ANDIJAN', s, flags=re.IGNORECASE)
    s = re.sub(r'\bSAMARQANI\b', 'SAMARQAND', s, flags=re.IGNORECASE)

    # Check English in-text pattern from secondary attestats (handle potential OCR word merges and Ne/N prefixes):
    m_eng = re.search(
        r'\b(?:Secondary\s*(?:General\s*)?School|School)\s*(?:[Nn][a-zA-Z\.]*|№)?\s*(\d+)\s+in\s+the\s+city\s+of\s+([A-Za-z]+)\s+([A-Za-z]+)\s+region',
        s,
        re.IGNORECASE
    )
    if m_eng:
        num = m_eng.group(1)
        city = m_eng.group(2).strip().upper()
        region = m_eng.group(3).strip().upper()
        return f"SECONDARY SCHOOL NO. {num} OF {region} REGION, {city} CITY"

    # Check Russian in-text pattern from secondary attestats:
    m_rus = re.search(
        r'средн(?:юю|яя)\s*общеобразовательн(?:ую|ая)?\s*школ(?:у|а)\s*(?:[Nn][a-zA-Z\.]*|№)?\s*(\d+)\s+города\s+([A-Za-zА-Яа-я]+)\s+([A-Za-zА-Яа-я]+)\s+области',
        s,
        re.IGNORECASE
    )
    if m_rus:
        num = m_rus.group(1)
        city = m_rus.group(2).strip().upper()
        region = m_rus.group(3).strip().upper()
        return f"SECONDARY SCHOOL NO. {num} OF {region} REGION, {city} CITY"

    num_match = re.search(r'\b(\d+)[\s-]*(?:sonli|son|maktab|№|no\.?)\b', s, re.IGNORECASE)
    school_num = num_match.group(1) if num_match else None

    # If it's already a full institute/university name (e.g. ANDIJAN MACHINE-BUILDING INSTITUTE)
    if any(k in s.upper() for k in ['INSTITUTE', 'UNIVERSITY', 'INSTITUT', 'UNIVERSITET', 'AKADEMIYA', 'ACADEMY']):
        clean_univ = re.sub(r'[\(\)\{\}\[\]\.,;:]', ' ', s).strip()
        clean_univ = re.sub(r'\s+', ' ', clean_univ)
        return clean_univ.upper()

    if re.search(r'(ixtisoslashtirilgan|specialized)', s, re.IGNORECASE):
        base_type = "Specialized School"
    elif re.search(r'(prezident|presidential)', s, re.IGNORECASE):
        base_type = "Presidential School"
    elif re.search(r'(ijod|creativity)', s, re.IGNORECASE):
        base_type = "Creativity School"
    elif re.search(r'(litsey|lyceum)', s, re.IGNORECASE):
        base_type = "Academic Lyceum"
    elif re.search(r'(texnikum|tehnikum|technicum)', s, re.IGNORECASE):
        base_type = "Technicum"
    elif re.search(r'(kollej|college)', s, re.IGNORECASE):
        base_type = "College"
    elif re.search(r'(gimnaziya|gymnasium)', s, re.IGNORECASE):
        base_type = "Gymnasium"
    elif re.search(r'(umumiy|orta\s*talim|o\'rta\s*ta\'lim|maktab|school)', s, re.IGNORECASE):
        base_type = "Secondary School"
    else:
        base_type = re.sub(r'\s+', ' ', s).strip().title()

    if school_num:
        school_name = f"{base_type} No. {school_num}"
    else:
        school_name = base_type

    if place_of_issue:
        p = place_of_issue.strip()
        p = re.sub(r'\b20[1-2][0-9][\s\-]*(?:-?yilda|yil|year)?\b', '', p, flags=re.IGNORECASE)
        p = re.sub(r'\bQoraqalpog[\'\`]?iston Respublikasi\b', 'Republic of Karakalpakstan', p, flags=re.IGNORECASE)
        p = re.sub(r'\bO[\'\`]?zbekiston Respublikasi\b', 'Republic of Uzbekistan', p, flags=re.IGNORECASE)
        p = re.sub(r'\b([A-Za-zА-Яа-я]+)\s+viloyati[a-z]*\b', r'\1 Region', p, flags=re.IGNORECASE)
        p = re.sub(r'\bviloyati[a-z]*\b', ' Region ', p, flags=re.IGNORECASE)
        p = re.sub(r'\b([A-Za-zА-Яа-я]+)\s+tumani[a-z]*\b', r'\1 District', p, flags=re.IGNORECASE)
        p = re.sub(r'\btumani[a-z]*\b', ' District ', p, flags=re.IGNORECASE)
        p = re.sub(r'\b([A-Za-zА-Яа-я]+)\s+shahri?\b', r'\1 City', p, flags=re.IGNORECASE)
        p = re.sub(r'\b([A-Za-zА-Яа-я]+)\s+shahar\b', r'\1 City', p, flags=re.IGNORECASE)
        p = re.sub(r'[\(\)\{\}\[\]\.,;:]', ' ', p).strip()
        p = re.sub(r'\s+', ' ', p)
        if p and not any(k in p.upper() for k in ['ORGANIZATION', 'TASHKILOT', 'BERILGAN', 'YEAR OF ISSUE', 'PLACE OF ISSUE']):
            res = f"{school_name} of {p}".upper().strip()
            return res.rstrip('.,;:')

    return school_name.upper().strip().rstrip('.,;:')


def calculate_gpa_from_text(full_text: str) -> Optional[str]:
    """
    Extracts explicit average grade or calculates the arithmetic mean of all assessed subjects.
    e.g. 5.00 or 4.91
    """
    # 1. Check for explicit average or average grade line (including OCR typos like o-year)
    avg_m = re.search(
        r'(?:average of [0-9oOa-z\-]+ grades|o[\'\`]?rtacha ko[\'\`]?rsatkichi|average grade|gpa)[\s:]*([3-5](?:\.\d{1,2})?)',
        full_text,
        re.IGNORECASE
    )
    if avg_m:
        return f"{float(avg_m.group(1)):.2f}"

    avg_block = re.search(
        r'(?:average of [0-9oOa-z\-]+ grades|o[\'\`]?rtacha ko[\'\`]?rsatkichi)[\s\S]{0,60}\b([3-5]\.\d{2})\b',
        full_text,
        re.IGNORECASE
    )
    if avg_block:
        return avg_block.group(1)

    # 2. Extract grades from the assessment table: 5 (a'lo), 4 (yaxshi), 5 (excellent), etc.
    grades_found = re.findall(
        r'(?:^|[^\d])([3-5])\s*[\(\[]\s*(?:a[\'\`]?lo|alo|ao|al|yaxshi|yaxsh|qoniqarli|qoniq|excellent|good|satisfactory|a\s*lo)',
        full_text,
        re.IGNORECASE
    )
    if not grades_found or len(grades_found) < 3:
        grades_found = re.findall(r'(?:^|[^\d])([3-5])\s*[\(\[]', full_text)

    if grades_found and len(grades_found) >= 3:
        nums = [int(g) for g in grades_found if g.isdigit()]
        if nums:
            avg = sum(nums) / len(nums)
            return f"{avg:.2f}"

    return None


# =========================================================================
# 3. DIPLOMA & SCHOOL CERTIFICATE EXTRACTOR
# =========================================================================
class DiplomaExtractor:
    @staticmethod
    def extract(ocr_lines: List[str], full_text: str, is_shahodatnoma: bool = False) -> Dict[str, ExtractedField]:
        fields: Dict[str, ExtractedField] = {}
        all_raw_lines = [l.strip() for l in ocr_lines if l.strip()]
        upper_text = full_text.upper()

        is_technicum_or_college = any(k in upper_text for k in ['TECHNICUM', 'TEXNIKUM', 'TEHNIKUM', 'KOLLEJ', 'COLLEGE'])
        is_master = 'MAGISTR' in upper_text or 'MASTER' in upper_text

        degree_duration = 3 if is_shahodatnoma else (2 if (is_technicum_or_college or is_master) else 4)

        if is_shahodatnoma:
            fields['MAJOR'] = ExtractedField("GENERAL SECONDARY EDUCATION", 0.98, True, 'CALCULATED')

        # Form Subtitle / Placeholder filter
        FORM_SUBTITLE_PATTERNS = [
            'THE NAME OF', 'EDUCATIONAL INSTITUTION', 'TA\'LIM MUASSASASI NOMI',
            'TALIM MUASSASASI NOMI', 'O\'QUV YURTI NOMI', 'OQUV YURTI NOMI',
            'MUASSASA NOMI', 'GRADUATE\'S', 'GRADUATES', 'FULL NAME',
            'FAMILYASI, ISMI', 'SPECIALIZATION OF', 'QUALIFICATION(S)', 'QUALIFICATIONS',
            'TA\'LIM TASHKILOTI', 'EDUCATIONAL ORGANIZATION', 'YEAR OF ISSUE', 'PLACE OF ISSUE',
            'BERILGAN YILI', 'BERILGAN JOYI', 'BERIGAN JOUI', 'BERIGAN YILI',
            'THE EDUCATIONAL INSTITUTION', 'GRADUATE\'S SURNAME', 'GRADUATES SURNAME'
        ]

        def is_form_subtitle(line_str: str) -> bool:
            t = line_str.upper().strip()
            if (t.startswith('(') and t.endswith(')')) or (t.startswith('(') and any(sp in t for sp in FORM_SUBTITLE_PATTERNS)):
                return True
            clean_str = re.sub(r'[^A-ZА-Я0-9]', '', t)
            return any(re.sub(r'[^A-ZА-Я0-9]', '', sp) in clean_str for sp in FORM_SUBTITLE_PATTERNS)

        # 1. Degree / Certificate / Registration Serial Number
        serial_match = re.search(
            r'\b(UM|B|M|K)\s*(?:[Nn][A-Za-z:\s]{0,2}|№|[Nn][Oo]\.?|[Gg])?\s*(\d{6,8})\b',
            upper_text
        )
        if serial_match:
            prefix = serial_match.group(1).upper()
            digits = serial_match.group(2)
            fields['DEGREE_NO'] = ExtractedField(f"{prefix} {digits}", 0.96, True, 'OCR_REGEX')
        else:
            reg_match = re.search(
                r'(?:REGISTRATION NUMBER|RO\'YXATGA OLISH RAQAMI|REGISTRATION NO\.?|RO\'YXAT RAQAMI)[:\s\-]*([A-Z0-9\-]+)',
                upper_text
            )
            if reg_match:
                fields['DEGREE_NO'] = ExtractedField(reg_match.group(1).strip(), 0.95, True, 'OCR_REGEX')
            else:
                other_serial = re.search(r'(?:SERIYA|SERIES|№)[:\s\-]*([A-ZА-Я]{1,3}\s*\d{6,8})|\b([A-ZА-Я]{1,3}\s*\d{6,8})\b|\b(\d{6,8})\b', upper_text)
                if other_serial:
                    s_val = other_serial.group(1) or other_serial.group(2) or other_serial.group(3)
                    if s_val and len(s_val.strip()) >= 4 and not any(k in s_val for k in ['DIPLOMA', 'SHAHODATNOMA']):
                        fields['DEGREE_NO'] = ExtractedField(s_val.strip(), 0.92, True, 'OCR_REGEX')

        # 2. Extract Place of Issue / Location (for Shahodatnoma)
        place_of_issue = ''
        for i, line in enumerate(all_raw_lines):
            if i < 4:
                continue
            l_up = line.upper()
            if is_form_subtitle(line) or any(k in l_up for k in ['TA\'LIM TASHKILOTI', 'YEAR OF ISSUE', 'PLACE OF ISSUE', 'BERILGAN', 'BERIGAN']):
                continue
            if any(pk in l_up for pk in ['VILOYATI', 'TUMANI', 'SHAHAR', 'SHAHRI', 'QORAQALPOG', 'KARAKALPAK', 'NUKUS', 'ANDIJON', 'TOSHKENT', 'SAMARQAND', 'FERGANA', 'FARG\'ONA', 'MARGILAN']):
                if not any(sk in l_up for sk in ['MAKTAB', 'SCHOOL', 'DIPLOM', 'SHAHODATNOMA', 'TASHKILOTI', 'ORGANIZATION']):
                    place_of_issue = line.strip()
                    break

        # 3. School Name (Translate into English)
        school_keywords = [
            'TECHNICUM', 'TEXNIKUM', 'TEHNIKUM', 'KOLLEJ', 'COLLEGE', 'LITSEY', 'LYCEUM',
            'UNIVERSITET', 'UNIVERSITY', 'INSTITUT', 'INSTITUTE', 'AKADEMIYA', 'ACADEMY',
            'MAKTAB', 'MAKTABI', 'MAKTABINI', 'SCHOOL', 'GIMNAZIYA', 'GYMNASIUM', 'IXTISOSLASHTIRILGAN'
        ]

        extracted_school = None
        attestat_m = re.search(
            r'\b(?:Secondary\s*(?:General\s*)?School|School)\s*(?:[Nn][a-zA-Z\.]*|№)?\s*(\d+)\s+in\s+the\s+city\s+of\s+([A-Za-z]+)\s+([A-Za-z]+)\s+region',
            full_text,
            re.IGNORECASE
        )
        if attestat_m:
            num = attestat_m.group(1)
            city = attestat_m.group(2).strip().upper()
            region = attestat_m.group(3).strip().upper()
            fields['FINAL_SCHOOL_NAME'] = ExtractedField(f"SECONDARY SCHOOL NO. {num} OF {region} REGION, {city} CITY", 0.96, True, 'LAYOUT')
        else:
            # Helper: connective endings that signal a multi-line school name
            _SCHOOL_NAME_CONTINUATIONS = ['NAMED AFTER', 'NAMED', 'AFTER', 'OF', 'AND', 'IM.', 'IM']
            _SCHOOL_BREAK_KW = ['DIPLOM', 'DIPLOMA', 'SHAHODATNOMA', 'CERTIFICATE', 'BERILGAN', 'YILDA', 'YEAR',
                                'IN ACCORDANCE', 'COMMISSION', 'DECISION', 'AWARDED', 'BACHELOR', 'MASTER']

            def _needs_continuation(text: str) -> bool:
                """True when the accumulated school name ends with a connective word."""
                t = text.upper().strip().rstrip('.,;:')
                return any(t.endswith(ce) for ce in _SCHOOL_NAME_CONTINUATIONS)

            def _collect_continuation(start_idx: int, initial_text: str) -> str:
                """Append subsequent lines to *initial_text* while the name looks incomplete."""
                result = initial_text
                for j in range(start_idx, min(start_idx + 3, len(all_raw_lines))):
                    nxt = all_raw_lines[j].strip()
                    if not nxt or is_form_subtitle(nxt):
                        break
                    nxt_up = nxt.upper()
                    if any(k in nxt_up for k in _SCHOOL_BREAK_KW):
                        break
                    result = result + ' ' + nxt
                    if not _needs_continuation(result):
                        break
                return re.sub(r'\s+', ' ', result).strip()

            for i, line in enumerate(all_raw_lines):
                l_up = line.upper()

                # Check if line is a school organization subtitle
                if any(sk in l_up for sk in ['EDUCATIONAL ORGANIZATION', 'TA\'LIM TASHKILOTI', 'TA LIM TASHKLON', 'TALIM TASHKILOTI', 'EDUCATIONAL INSTITUTION', 'TA\'LIM MUASSASASI', 'THE EDUCATIONAL INSTITUTION']):
                    if i > 0:
                        cand = all_raw_lines[i-1].strip()
                        if len(cand) >= 4 and not is_form_subtitle(cand) and not any(k in cand.upper() for k in _SCHOOL_BREAK_KW):
                            # Walk upward to collect multi-line names (e.g. "NAMED AFTER" on the line above)
                            if i >= 2 and _needs_continuation(all_raw_lines[i-2].strip()):
                                upper_cand = all_raw_lines[i-2].strip()
                                if not is_form_subtitle(upper_cand) and not any(k in upper_cand.upper() for k in _SCHOOL_BREAK_KW):
                                    cand = upper_cand + ' ' + cand
                            extracted_school = re.sub(r'\s+', ' ', cand).strip()
                            break

                # Direct keyword match
                if any(sk in l_up for sk in school_keywords) and not is_form_subtitle(line):
                    cand = re.sub(r'\s+', ' ', line).strip()
                    if len(cand) >= 5 and not any(k in cand.upper() for k in _SCHOOL_BREAK_KW):
                        # Collect continuation lines for multi-line names
                        if _needs_continuation(cand):
                            cand = _collect_continuation(i + 1, cand)
                        extracted_school = cand
                        break

            if extracted_school:
                eng_school = translate_uzbek_school_name(extracted_school, place_of_issue)
                fields['FINAL_SCHOOL_NAME'] = ExtractedField(eng_school, 0.95, True, 'LAYOUT')

        # 4. Major / Specialization (Single or Multi-line)
        if not is_shahodatnoma:
            major_lines = []
            in_major = False
            for line in all_raw_lines:
                l_up = line.upper()
                clean_l_up = re.sub(r'[^A-ZА-Я0-9]', '', l_up)

                if any(mk in clean_l_up for mk in ['ISAWARDEDWITH', 'AWARDEDWITH', 'COMPLETED', 'TAMOMLADI', 'MUTAXASSISLIGI', 'YONALISHI', 'MAJOR', 'SPECIALIZATION', 'SPECIALTY', 'QUALIFICATION']):
                    in_major = True
                    clean_major = re.sub(r'^(?:IS\s*AWARDED\s*WITH|COMPLETED|TAMOMLADI|MUTAXASSISLIGI|YO[\'\`]?NALISHI|YONALISHI|MAJOR|SPECIALIZATION\s*OF|SPECIALTY|QUALIFICATION\(S\))[:\s\-]*', '', line, flags=re.IGNORECASE).strip()
                    clean_major = re.sub(r'^\s*[\(\[]\s*(?:IN[-\s]*THE\s+SPECIALITY|SPECIALITY|SPECIALTY|MUTAXASSISLIK|FIELD|DIRECTION)\s*[\)\]]', '', clean_major, flags=re.IGNORECASE).strip()
                    if clean_major and len(clean_major) >= 4 and not is_form_subtitle(clean_major):
                        major_lines.append(clean_major)
                    continue

                if in_major:
                    if any(k in clean_l_up for k in ['BACHELOR', 'MAGISTR', 'MASTER', 'QUALIFIEDAS', 'QUALIFICATION', 'RECTOR', 'REGISTRATION', 'JULY', 'AUGUST', 'JUNE', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER', 'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY']):
                        break
                    if re.search(r'\b(20[1-2][0-9])\b', line):
                        break
                    if any(k == clean_l_up for k in ['INTHESPECIALITY', 'INTHESPECIALTY', 'SPECIALITY', 'SPECIALTY', 'MUTAXASSISLIGI', 'MUTAXASSISLIK', 'FIELD', 'DIRECTION']):
                        continue
                    clean_line = re.sub(r'[\(\[]\s*(?:IN[-\s]*THE\s+SPECIALITY|SPECIALITY|SPECIALTY|MUTAXASSISLIK|FIELD|DIRECTION)\s*[\)\]]?', '', line, flags=re.IGNORECASE).strip()
                    if clean_line and not is_form_subtitle(clean_line) and not clean_line.startswith('('):
                        major_lines.append(clean_line)

            if major_lines:
                full_major = " ".join(major_lines).strip().upper()
                full_major = re.sub(r'[\.\,]', ' ', full_major)
                full_major = re.sub(r'\s+', ' ', full_major).strip()
                fields['MAJOR'] = ExtractedField(full_major, 0.90, True, 'LAYOUT')

        # NOTE: FULL_NAME is intentionally NOT extracted from diplomas/certificates.
        # The student's name is already captured from their passport scan.

        # NOTE: DATE_OF_BIRTH is intentionally NOT extracted from diplomas/certificates.
        # The student's DOB is already captured from their passport scan.

        # 7. Graduation Date & Computed Entry Date
        grad_match = re.search(r'\b(20[1-2][0-9])[\s\-yY]*(?:-?yilda|yil|year|г|y)?\b', upper_text)
        if grad_match:
            grad_year = int(grad_match.group(1))
            fields['DATE_OF_GRADUATION'] = ExtractedField(f"{grad_year}-07-20", 0.95, True, 'CALCULATED')
            entry_year = grad_year - degree_duration
            fields['DATE_OF_ENTRY'] = ExtractedField(f"{entry_year}-09-02", 0.95, True, 'CALCULATED')

        # 8. GPA (Explicit or calculated from grade table)
        gpa_val = calculate_gpa_from_text(full_text)
        if gpa_val:
            fields['GPA'] = ExtractedField(gpa_val, 0.92, True, 'CALCULATED')

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

        # 2. Check for Father / Mother Contact names
        is_father_contact = any(re.search(r'\b(?:DADA|DADAM|OTA|OTAM|FATHER)\b', l, re.IGNORECASE) for l in all_raw_lines)
        is_mother_contact = any(re.search(r'\b(?:ONA|ONAM|OYI|OYIM|MOTHER)\b', l, re.IGNORECASE) for l in all_raw_lines)

        # 3. Phone numbers
        phones = re.findall(r'(?:\+?998[\s-]*)?(?:9[0-9]|88|33|77|99|95|94|93|91|90)[\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}', full_text)
        if phones:
            if is_father_contact and not is_mother_contact:
                fields['FATHER_PHONE'] = ExtractedField(normalize_phone_number(phones[0]), 0.96, True, 'OCR_REGEX')
                if len(phones) >= 2:
                    fields['FATHER_PHONE_2'] = ExtractedField(normalize_phone_number(phones[1]), 0.95, True, 'OCR_REGEX')
            elif is_mother_contact and not is_father_contact:
                fields['MOTHER_PHONE'] = ExtractedField(normalize_phone_number(phones[0]), 0.96, True, 'OCR_REGEX')
                if len(phones) >= 2:
                    fields['MOTHER_PHONE_2'] = ExtractedField(normalize_phone_number(phones[1]), 0.95, True, 'OCR_REGEX')
            else:
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
