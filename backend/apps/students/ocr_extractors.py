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

        # 1. Check School Certificate keywords
        if any(k in up_clean for k in ['SHAHODATNOMA', 'ATTESTAT', 'GENERALSECONDARYEDUCATION', 'ORTATALIM', 'TALIMTOGRISIDA', 'USHBUSHAHODATNOMA', 'AVERAGEOF6YEARGRADES', 'BAHOLARIORTACHA']):
            return "SCHOOL_CERTIFICATE"

        # 2. Check Diploma & Technicum keywords
        if any(k in up_clean for k in ['DIPLOM', 'DIPLOMA', 'BAKALAVR', 'MAGISTR', 'BACHELOR', 'MASTER', 'TECHNICUM', 'TEXNIKUM', 'TEHNIKUM', 'ATTESTATIONCOMMISSION']):
            return "DIPLOMA"

        # 3. Check ID Card keywords
        if any(k in up_clean for k in ['IDCARD', 'IDENTIFICATIONCARD', 'IDKARTA']):
            return "ID_CARD"

        # 4. Check Passport keywords (specific to passport, not generic republic header)
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
                    viz_father = normalize_patronymic(after)
                else:
                    for j in range(i + 1, min(i + 4, len(all_raw_lines))):
                        cand = all_raw_lines[j].strip().upper()
                        cand_clean = re.sub(r'[^A-ZА-Я0-9]', '', cand)
                        if not is_passport_header_label(cand_clean) and re.match(r'^[A-ZА-Я\s\'-]{2,}$', cand):
                            viz_father = normalize_patronymic(cand)
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

        return fields


def translate_uzbek_school_name(raw_school_text: str, place_of_issue: str = '') -> str:
    """
    Translates Uzbek and Russian school names & locations into clean English.
    e.g.:
    - '46-sonli ayrim fanlar chuqur o'qitiladigan sinflari mavjud umumiy o'rta ta'lim maktabini'
      + 'Qoraqalpog'iston Respublikasi, Nukus shahar'
      -> 'SECONDARY SCHOOL NO. 46 OF REPUBLIC OF KARAKALPAKSTAN, NUKUS CITY'
    - 'Ixtisoslashtirilgan maktabini' + 'Andijon viloyati, Shahrixon tumani'
      -> 'SPECIALIZED SCHOOL OF ANDIJON REGION, SHAHRIXON DISTRICT'
    """
    s = raw_school_text.strip()
    
    num_match = re.search(r'\b(\d+)[\s-]*(?:sonli|son|maktab|№|no\.?)\b', s, re.IGNORECASE)
    school_num = num_match.group(1) if num_match else None

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
    # 1. Check for explicit 6-year average or average grade line
    avg_m = re.search(
        r'(?:average of 6-year grades|o[\'\`]?rtacha ko[\'\`]?rsatkichi|average grade|gpa)[\s:]*([3-5](?:\.\d{1,2})?)',
        full_text,
        re.IGNORECASE
    )
    if avg_m:
        return f"{float(avg_m.group(1)):.2f}"

    # Check for isolated decimal number following 'average of 6-year grades'
    avg_block = re.search(
        r'average of 6-year grades[\s\S]{0,60}\b([3-5]\.\d{2})\b',
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
            'BERILGAN YILI', 'BERILGAN JOYI', 'BERIGAN JOUI', 'BERIGAN YILI'
        ]

        def is_form_subtitle(line_str: str) -> bool:
            t = line_str.upper().strip()
            if (t.startswith('(') and t.endswith(')')) or (t.startswith('(') and any(sp in t for sp in FORM_SUBTITLE_PATTERNS)):
                return True
            clean_str = re.sub(r'[^A-ZА-Я0-9]', '', t)
            return any(re.sub(r'[^A-ZА-Я0-9]', '', sp) in clean_str for sp in FORM_SUBTITLE_PATTERNS)

        # 1. Degree / Certificate / Registration Serial Number
        reg_match = re.search(r'(?:REGISTRATION NUMBER|RO\'YXATGA OLISH RAQAMI|REGISTRATION NO\.?|RO\'YXAT RAQAMI)[:\s\-]*([A-Z0-9\-]+)', upper_text)
        serial_match = re.search(r'(?:UM\s*(?:N[:\s]|№|NO\.?)?\s*\d{6,8}|(?:SERIYA|SERIES|№)[:\s\-]*[A-ZА-Я]{1,3}\s*(?:№|N|NO\.?)?\s*\d{6,8}|\b[A-ZА-Я]{1,3}\s*\d{6,8}\b|\b\d{6,8}\b)', upper_text)

        if reg_match:
            fields['DEGREE_NO'] = ExtractedField(reg_match.group(1).strip(), 0.95, True, 'OCR_REGEX')
        elif serial_match:
            s_val = serial_match.group(0).strip()
            if s_val and len(s_val) >= 4 and not any(k in s_val for k in ['DIPLOMA', 'SHAHODATNOMA']):
                clean_ser = re.sub(r'^UM\s*(?:N[:\s]|№|NO\.?)\s*', 'UM ', s_val, flags=re.IGNORECASE)
                fields['DEGREE_NO'] = ExtractedField(clean_ser, 0.95, True, 'OCR_REGEX')

        # 2. Extract Place of Issue / Location (for Shahodatnoma)
        place_of_issue = ''
        for i, line in enumerate(all_raw_lines):
            if i < 4:
                continue
            l_up = line.upper()
            if is_form_subtitle(line) or any(k in l_up for k in ['TA\'LIM TASHKILOTI', 'YEAR OF ISSUE', 'PLACE OF ISSUE', 'BERILGAN', 'BERIGAN']):
                continue
            if any(pk in l_up for pk in ['VILOYATI', 'TUMANI', 'SHAHAR', 'SHAHRI', 'QORAQALPOG', 'KARAKALPAK', 'NUKUS', 'ANDIJON', 'TOSHKENT', 'SAMARQAND']):
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
        for i, line in enumerate(all_raw_lines):
            l_up = line.upper()

            # Check if line is a school organization subtitle
            if any(sk in l_up for sk in ['EDUCATIONAL ORGANIZATION', 'TA\'LIM TASHKILOTI', 'TA LIM TASHKLON', 'TALIM TASHKILOTI', 'EDUCATIONAL INSTITUTION', 'TA\'LIM MUASSASASI']):
                if i > 0:
                    cand = all_raw_lines[i-1].strip()
                    if len(cand) >= 4 and not is_form_subtitle(cand) and not any(k in cand.upper() for k in ['DIPLOM', 'DIPLOMA', 'SHAHODATNOMA', 'CERTIFICATE', 'BERILGAN', 'YILDA', 'YEAR']):
                        extracted_school = cand
                        break

            # Direct keyword match
            if any(sk in l_up for sk in school_keywords) and not is_form_subtitle(line):
                cand = re.sub(r'\s+', ' ', line).strip()
                if len(cand) >= 5 and not any(k in cand.upper() for k in ['DIPLOM', 'DIPLOMA', 'SHAHODATNOMA', 'CERTIFICATE', 'BERILGAN']):
                    extracted_school = cand
                    break

        if extracted_school:
            eng_school = translate_uzbek_school_name(extracted_school, place_of_issue)
            fields['FINAL_SCHOOL_NAME'] = ExtractedField(eng_school, 0.95, True, 'LAYOUT')

        # 4. Major / Specialization
        if not is_shahodatnoma:
            for line in all_raw_lines:
                l_up = line.upper()
                if any(mk in l_up for mk in ['COMPLETED', 'TAMOMLADI', 'MUTAXASSISLIGI', 'YO\'NALISHI', 'YONALISHI', 'MAJOR', 'SPECIALIZATION', 'SPECIALTY', 'QUALIFICATION']):
                    clean_major = re.sub(r'^(COMPLETED|TAMOMLADI|MUTAXASSISLIGI|YO\'NALISHI|YONALISHI|MAJOR|SPECIALIZATION OF|SPECIALTY|QUALIFICATION\(S\))[:\s\-]+', '', l_up).strip()
                    clean_major = re.sub(r'\(.*?\)', '', clean_major).strip()
                    if clean_major and len(clean_major) >= 4 and not is_form_subtitle(clean_major):
                        fields['MAJOR'] = ExtractedField(clean_major, 0.88, False, 'LAYOUT')
                        break

        # 5. Student Full Name on Certificate / Diploma
        for i, line in enumerate(all_raw_lines):
            l_up = line.upper()
            if any(nk in l_up for nk in ['SURNAME, GIVEN', 'SWNAME, GNEN', 'FAMILYASI, ISMI', 'FAMLYASI, ISMI', 'FATHERSNAME', 'PATRONYMIC', 'PARORYMIC', 'GRADUATE\'S FULL NAME', 'BITIRUVCHINING FAMILIYASI', 'COMMISSION', 'DECISION']):
                if i > 0:
                    cand = all_raw_lines[i-1].strip().upper()
                    if re.match(r'^[A-ZА-Я\s\'-]{6,}$', cand) and not is_form_subtitle(cand):
                        if not any(k in cand for k in ['COMMISSION', 'DECISION', 'STATE', 'DIPLOMA', 'SHAHODATNOMA', 'CERTIFICATE', 'RESPUBLIKASI', 'REPUBLIC', 'YILDA', 'YEAR']):
                            fields['FULL_NAME'] = ExtractedField(normalize_name(cand), 0.95, True, 'LAYOUT')
                            break

        # 6. Student Date of Birth on Certificate
        for i, line in enumerate(all_raw_lines):
            l_up = line.upper()
            if any(dk in l_up for dk in ['DATE OF BIRTH', 'TUG\'ILGAN SANASI', 'TUGILGAN SANASI', 'TUGLLGAN SANASI', 'TUG LLGAN', 'CARE OF BURTH']):
                for j in range(max(0, i-2), min(i+2, len(all_raw_lines))):
                    d = normalize_date(all_raw_lines[j])
                    if d:
                        fields['DATE_OF_BIRTH'] = ExtractedField(d, 0.95, True, 'LAYOUT')
                        break
                if 'DATE_OF_BIRTH' in fields:
                    break

        # 7. Graduation Date & Computed Entry Date (Graduation Year - 3 for Shahodatnoma)
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
