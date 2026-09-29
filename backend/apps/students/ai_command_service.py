import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

# Common acronym mappings for South Korean Universities
KNOWN_ACRONYMS: Dict[str, str] = {
    "BUFS": "BUSAN UNIVERSITY OF FOREIGN STUDIES",
    "SNU": "SEOUL NATIONAL UNIVERSITY",
    "KU": "KOREA UNIVERSITY",
    "YU": "YONSEI UNIVERSITY",
    "CAU": "CHUNG-ANG UNIVERSITY",
    "SKKU": "SUNGKYUNKWAN UNIVERSITY",
    "HYU": "HANYANG UNIVERSITY",
    "PNU": "PUSAN NATIONAL UNIVERSITY",
    "KNU": "KYUNGPOOK NATIONAL UNIVERSITY",
    "CNU": "CHONNAM NATIONAL UNIVERSITY",
    "KAIST": "KAIST",
    "POSTECH": "POHANG UNIVERSITY OF SCIENCE AND TECHNOLOGY",
    "UNIST": "ULSAN NATIONAL INSTITUTE OF SCIENCE AND TECHNOLOGY",
    "JNU": "JEONBUK NATIONAL UNIVERSITY",
    "KMU": "KOOKMIN UNIVERSITY",
    "SMIT": "SEOUL MEDIA INSTITUTE OF TECHNOLOGY",
    "JBU": "JOONGBU UNIVERSITY",
}

# Supported row colors (user-facing name -> stored value)
COLOR_NAME_MAP: Dict[str, Optional[str]] = {
    "red": "red",
    "orange": "orange",
    "yellow": "yellow",
    "green": "green",
    "blue": "blue",
    "purple": "purple",
    "pink": "pink",
    "gray": "gray",
    "grey": "gray",
    "none": None,
    "clear": None,
    "remove": None,
    "reset": None,
    "white": None,
}


def find_best_matching_university(raw_name: str, official_universities: List[str]) -> Optional[str]:
    """
    Smart matcher that resolves acronyms (e.g. BUFS), short names (e.g. Inha, Joongbu),
    or exact substrings against official database university names.
    """
    if not raw_name or not official_universities:
        return None

    query = raw_name.strip().upper()

    # 1. Check direct acronym map
    if query in KNOWN_ACRONYMS:
        expanded = KNOWN_ACRONYMS[query].upper()
        for u in official_universities:
            if expanded in u.upper():
                return u

    # 2. Check exact match
    for u in official_universities:
        if u.upper() == query:
            return u

    # 3. Check if university name begins with query word (e.g. "JOONGBU" in "JOONGBU UNIVERSITY ...")
    for u in official_universities:
        u_upper = u.upper()
        if u_upper.startswith(query + " ") or u_upper.startswith(query + "("):
            return u

    # 4. Check word boundary substring
    for u in official_universities:
        u_upper = u.upper()
        if query in u_upper:
            return u

    # 5. Check acronym generation from official names (e.g. "BUFS" from "Busan University of Foreign Studies")
    for u in official_universities:
        words = [w for w in u.split() if w.isalpha() and w.lower() not in ['of', 'and', 'the', '&']]
        acronym = "".join(w[0].upper() for w in words)
        if query == acronym:
            return u

    return None


def find_best_matching_folder(raw_name: str, available_folders: List[Dict]) -> Optional[Dict]:
    """
    Smart matcher that resolves a partial/case-insensitive folder name against
    the available folders list. Returns the folder dict {id, name} or None.
    """
    if not raw_name or not available_folders:
        return None

    query = raw_name.strip().upper()

    # 1. Exact match (case-insensitive)
    for f in available_folders:
        if f.get("name", "").upper() == query:
            return f

    # 2. Folder name starts with query
    for f in available_folders:
        if f.get("name", "").upper().startswith(query):
            return f

    # 3. Folder name contains query
    for f in available_folders:
        if query in f.get("name", "").upper():
            return f

    return None


def normalize_color(raw_color: str) -> Optional[str]:
    """Normalize a user-typed color name to the stored value (or None to clear)."""
    return COLOR_NAME_MAP.get(raw_color.strip().lower(), raw_color.strip().lower())


def interpret_ai_command(
    prompt: str,
    official_universities: Optional[List[str]] = None,
    all_student_ids: Optional[List[str]] = None,
    available_folders: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Uses OpenAI GPT-4o with structured JSON output to understand
    natural language bulk operations on CRM students.
    """
    api_key = os.environ.get("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "")
    official_unis = official_universities or []
    folders = available_folders or []

    # Fast heuristic check for "set university for f1,f2" (strictly "set university for <ids>" with NO university name specified)
    import re
    empty_uni_match = re.match(r'^(?:set|add)\s+universit(?:y)?\s+for\s+([a-zA-Z0-9\s,;]+)$', prompt.strip(), re.IGNORECASE)
    if empty_uni_match:
        rem = empty_uni_match.group(1).strip()
        tokens = [t.strip().upper() for t in re.split(r'[\s,;]+', rem) if t.strip()]
        # Check if all tokens match alphanumeric student ID pattern
        if tokens and all(re.match(r'^[A-Z0-9]+$', t) for t in tokens):
            return {
                "action": "set_university",
                "student_ids": tokens,
                "university_name": None,
                "needs_clarification": True,
                "clarification_field": "university",
                "clarification_question": f"Which university would you like to set for {', '.join(tokens)}?",
                "message": f"Please select or enter the university to assign to {', '.join(tokens)}."
            }

    if not api_key:
        logger.warning("OPENAI_API_KEY not found; using rule-based fallback.")
        return fallback_rule_based_parser(prompt, official_unis, folders)

    # Sample top universities and folder names for prompt context
    uni_sample = official_unis[:120]
    folder_sample = [f.get("name", "") for f in folders[:50]]

    system_instruction = (
        "You are the intelligent bulk operations assistant for Salom Korea CRM.\n"
        "Your job is to parse the user's natural language command and map it to an action.\n\n"
        "Supported actions:\n"
        "1. 'set_university': assign a university to one or more students.\n"
        "   - extract 'student_ids': list of alphanumeric IDs (uppercase, e.g. ['F4', 'F5', 'F6']).\n"
        "   - extract 'university_name': MUST be matched against the official university list when possible.\n"
        "     Resolve acronyms like BUFS -> BUSAN UNIVERSITY OF FOREIGN STUDIES, SNU -> SEOUL NATIONAL UNIVERSITY, etc.\n"
        "   - if user did NOT specify any university name (e.g. 'set university for f4,f5,f6'), set:\n"
        "     'needs_clarification': true, 'clarification_field': 'university', 'clarification_question': 'Which university would you like to set for [IDs]?'.\n"
        "2. 'show_university': view university choices for students.\n"
        "3. 'delete_students': archive or delete students.\n"
        "4. 'excel_export': preselect students and open Excel export.\n"
        "5. 'create_folder': create a new folder by name.\n"
        "   - CRITICAL: In this CRM, users say 'open folder <name>' or 'create folder <name>' or 'new folder <name>' to CREATE a new folder (e.g. 'open folder busan' means create a new folder named BUSAN, NOT navigating).\n"
        "   - extract 'folder_name': the uppercase folder name to create (e.g. 'BUSAN').\n"
        "   - e.g. 'open folder busan', 'create folder seoul', 'new folder busan'\n"
        "6. 'add_to_folder': add specific students to a named folder.\n"
        "   - extract 'folder_name': the destination folder name.\n"
        "   - extract 'student_ids': list of student IDs to add.\n"
        "   - e.g. 'folder busan add f1,f5,f6', 'add f1,f5 to folder busan'\n"
        "7. 'set_row_color': set personal (only me) row color for specific students.\n"
        "   - extract 'student_ids': list of student IDs.\n"
        "   - extract 'color': one of: red, orange, yellow, green, blue, purple, pink, gray, none (to clear).\n"
        "   - e.g. 'set row color red f1,f8,f2', 'color green for f3,f4', 'clear color f1'\n"
        "8. 'filter_students': filter or query students by language certificate (IELTS, TOPIK, SAT, TOEFL, CEFR, SKA, NO CERTIFICATE) and/or score.\n"
        "   - extract 'cert': uppercase certificate name ('IELTS', 'TOPIK', 'SAT', 'TOEFL', 'CEFR', 'SKA', 'NO CERTIFICATE') or null.\n"
        "   - extract 'score': score string if specified (e.g. '6.0', '6.5', '2', '3', 'EXPECTED') or null.\n"
        "     Note: For IELTS, format integer scores as decimal e.g. 6 -> '6.0', 7 -> '7.0'.\n"
        "   - e.g. 'filter ielts 6', 'filter topik 2', 'who has sat', 'who has ielts', 'show students with ielts 6.5', 'filter no certificate'\n"
        "9. 'other': general inquiry or custom prompt.\n\n"
        f"Available official universities in database (sample):\n{json.dumps(uni_sample)}\n\n"
        f"Available folders:\n{json.dumps(folder_sample)}\n\n"
        "You MUST respond ONLY with valid JSON matching this schema:\n"
        "{\n"
        '  "action": "set_university" | "show_university" | "delete_students" | "excel_export" | "create_folder" | "open_folder" | "add_to_folder" | "set_row_color" | "filter_students" | "clarification" | "other",\n'
        '  "student_ids": ["F4", "F5"],\n'
        '  "university_name": "EXACT_OFFICIAL_NAME" or null,\n'
        '  "folder_name": "folder name" or null,\n'
        '  "color": "red" | "orange" | "yellow" | "green" | "blue" | "purple" | "pink" | "gray" | "none" | null,\n'
        '  "cert": "IELTS" | "TOPIK" | "SAT" | "TOEFL" | "CEFR" | "SKA" | "NO CERTIFICATE" | null,\n'
        '  "score": "6.0" | "2" | null,\n'
        '  "needs_clarification": boolean,\n'
        '  "clarification_field": "university" or null,\n'
        '  "clarification_question": "..." or null,\n'
        '  "message": "Brief friendly summary"\n'
        "}"
    )

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
                "max_tokens": 500
            },
            timeout=15
        )

        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)

            # Post-process university matching if present
            raw_uni = parsed.get("university_name")
            if raw_uni:
                best_match = find_best_matching_university(raw_uni, official_unis)
                if best_match:
                    parsed["university_name"] = best_match

            # Post-process folder matching if present
            raw_folder = parsed.get("folder_name")
            if raw_folder:
                best_folder = find_best_matching_folder(raw_folder, folders)
                if best_folder:
                    parsed["folder_name"] = best_folder["name"]
                    parsed["folder_id"] = best_folder["id"]

            # Post-process color normalization
            raw_color = parsed.get("color")
            if raw_color is not None:
                parsed["color"] = normalize_color(raw_color)

            # Normalize student IDs
            if parsed.get("student_ids"):
                parsed["student_ids"] = [str(s).strip().upper() for s in parsed["student_ids"]]

            return parsed
        else:
            logger.error(f"OpenAI error {resp.status_code}: {resp.text}")
            return fallback_rule_based_parser(prompt, official_unis, folders)

    except Exception as e:
        logger.error(f"OpenAI call failed in ai_command_service: {e}")
        return fallback_rule_based_parser(prompt, official_unis, folders)


def fallback_rule_based_parser(
    prompt: str,
    official_universities: List[str],
    available_folders: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """High-accuracy fallback parser when OpenAI is unreachable or offline."""
    import re

    folders = available_folders or []
    text = prompt.strip()

    STOP_WORDS = {
        'ONLY', 'ME', 'FOR', 'STUDENT', 'STUDENTS', 'TO', 'IN', 'AND', 'THE', 'THESE',
        'ROW', 'COLOR', 'CHANGES', 'MY', 'MINE'
    }

    def extract_clean_ids(raw_text: str) -> List[str]:
        tokens = [t.strip().upper() for t in re.split(r'[\s,;]+', raw_text) if t.strip()]
        return [t for t in tokens if t not in STOP_WORDS]

    # 1. /delete
    del_m = re.match(r'^\/delete\s+(.+)$', text, re.I)
    if del_m:
        ids = extract_clean_ids(del_m.group(1))
        return {
            "action": "delete_students",
            "student_ids": ids,
            "message": f"Archiving students: {', '.join(ids)}"
        }

    # 2. /excel
    excel_m = re.match(r'^\/excel\s+(.+)$', text, re.I)
    if excel_m:
        ids = extract_clean_ids(excel_m.group(1))
        return {
            "action": "excel_export",
            "student_ids": ids,
            "message": f"Exporting {len(ids)} students to Excel"
        }

    # 3. open/create/new folder <name> -> create_folder
    folder_create_m = re.match(r'^(?:open|create|new|make)\s+(?:folder\s+)?(.+?)(?:\s+folder)?$', text, re.I)
    if folder_create_m:
        raw_name = folder_create_m.group(1).strip().upper()
        return {
            "action": "create_folder",
            "folder_name": raw_name,
            "message": f"Creating new folder: {raw_name}"
        }

    # 4. folder <name> add <ids>  OR  add <ids> to folder <name>
    folder_add_m = re.match(r'^(?:folder\s+(.+?)\s+add\s+(.+)|add\s+(.+?)\s+to\s+(?:folder\s+)?(.+))$', text, re.I)
    if folder_add_m:
        if folder_add_m.group(1):
            raw_name = folder_add_m.group(1).strip()
            raw_ids = folder_add_m.group(2).strip()
        else:
            raw_ids = folder_add_m.group(3).strip()
            raw_name = folder_add_m.group(4).strip()

        ids = extract_clean_ids(raw_ids)
        matched = find_best_matching_folder(raw_name, folders)
        folder_name = matched["name"] if matched else raw_name
        folder_id = matched["id"] if matched else None

        result: Dict[str, Any] = {
            "action": "add_to_folder",
            "student_ids": ids,
            "folder_name": folder_name,
            "message": f"Adding {', '.join(ids)} to folder '{folder_name}'"
        }
        if folder_id:
            result["folder_id"] = folder_id
        return result

    # 5. set/color row color <color> <ids>
    color_m = re.match(
        r'^(?:set\s+(?:row\s+)?color|color)\s+(\w+)\s+(?:for\s+)?(.+)$',
        text, re.I
    )
    if color_m:
        raw_color = color_m.group(1).strip()
        ids = extract_clean_ids(color_m.group(2))
        normalized_color = normalize_color(raw_color)
        return {
            "action": "set_row_color",
            "student_ids": ids,
            "color": normalized_color,
            "message": f"Setting row color '{raw_color}' for {', '.join(ids)}"
        }

    # 6. clear/remove color <ids>
    clear_color_m = re.match(r'^(?:clear|remove|reset)\s+(?:row\s+)?color\s+(?:for\s+)?(.+)$', text, re.I)
    if clear_color_m:
        ids = extract_clean_ids(clear_color_m.group(1))
        return {
            "action": "set_row_color",
            "student_ids": ids,
            "color": None,
            "message": f"Clearing row color for {', '.join(ids)}"
        }

    # 7. show university
    show_m = re.match(r'^(?:show|get|view)\s+universit(?:y|ies)(?:\s+for)?\s+(.+)$', text, re.I)
    if show_m:
        ids = extract_clean_ids(show_m.group(1))
        return {
            "action": "show_university",
            "student_ids": ids,
            "message": f"Viewing university choices for: {', '.join(ids)}"
        }

    # 8. set university <name> for <ids...>
    set_m = re.match(r'^set\s+universit(?:y)?\s+(.+?)\s+for\s+(.+)$', text, re.I)
    if set_m:
        raw_uni = set_m.group(1).strip()
        ids = extract_clean_ids(set_m.group(2))
        matched_uni = find_best_matching_university(raw_uni, official_universities) or raw_uni
        return {
            "action": "set_university",
            "student_ids": ids,
            "university_name": matched_uni,
            "message": f"Setting {matched_uni} for {', '.join(ids)}"
        }

    # 9. set university for <ids...> (no university specified)
    set_no_uni_m = re.match(r'^(?:set|add)\s+universit(?:y)?\s+(?:for\s+)?(.+)$', text, re.I)
    if set_no_uni_m:
        rem_clean = re.sub(r'^for\s+', '', set_no_uni_m.group(1), flags=re.I).strip()
        ids = extract_clean_ids(rem_clean)
        return {
            "action": "set_university",
            "student_ids": ids,
            "university_name": None,
            "needs_clarification": True,
            "clarification_field": "university",
            "clarification_question": f"Which university would you like to set for {', '.join(ids)}?",
            "message": f"Please choose which university to set for {', '.join(ids)}."
        }

    # 10. Filter by Certificate & Score (e.g. "filter ielts 6", "filter topik 2", "who has sat")
    cert_filter_m = re.match(
        r'^(?:filter|show|find|search|who\s+has|who\s+got)\s+(?:students?\s+with\s+|cert(?:ificate)?\s+)?(ielts|topik|sat|toefl|cefr|ska|no\s+certificate)\s*([0-9]+(?:\.[0-9]+)?)?$',
        text, re.I
    )
    if cert_filter_m:
        raw_cert = cert_filter_m.group(1).strip().upper()
        raw_score = cert_filter_m.group(2).strip() if cert_filter_m.group(2) else None
        if raw_cert in ('NO CERTIFICATE', 'NO CERT'):
            raw_cert = 'NO CERTIFICATE'

        if raw_cert == 'IELTS' and raw_score and '.' not in raw_score:
            raw_score = f"{raw_score}.0"

        msg = f"Filtering students with {raw_cert}" + (f" (Score: {raw_score})" if raw_score else "")
        return {
            "action": "filter_students",
            "cert": raw_cert,
            "score": raw_score,
            "message": msg
        }

    quick_cert_m = re.match(r'^(ielts|topik|sat|toefl|cefr|ska)\s*([0-9]+(?:\.[0-9]+)?)?$', text, re.I)
    if quick_cert_m:
        raw_cert = quick_cert_m.group(1).strip().upper()
        raw_score = quick_cert_m.group(2).strip() if quick_cert_m.group(2) else None
        if raw_cert == 'IELTS' and raw_score and '.' not in raw_score:
            raw_score = f"{raw_score}.0"
        return {
            "action": "filter_students",
            "cert": raw_cert,
            "score": raw_score,
            "message": f"Filtering students with {raw_cert}" + (f" (Score: {raw_score})" if raw_score else "")
        }

    return {
        "action": "other",
        "message": f"Received instruction: {text}"
    }


# --- School name normalization (Educational Background modal) ---

# Uzbek/Russian words that indicate a numbered general-education school and
# should collapse to the "GENERAL SECONDARY SCHOOL №N" family.
_SCHOOL_WORD_HINTS = ('MAKTAB', 'MAKTABI', 'SCHOOL', 'ШКОЛА', 'МАКТАБ')

# Words that indicate the input names an actual institution type. If NONE of
# these (or their Cyrillic equivalents) appear anywhere in the input, the AI
# has no basis to invent an institution — this guards against hallucination
# on bare place names / stray words (e.g. "asaka", "12", "bilmadim").
_INSTITUTION_TYPE_HINTS = (
    'MAKTAB', 'ШКОЛА', 'SCHOOL', 'SKUL', 'SCOOL', 'SKOOL',
    'LITSEY', 'LITSEI', 'LYCEUM', 'ЛИЦЕЙ',
    'KOLLEJ', 'COLLEGE', 'КОЛЛЕДЖ', 'КОЛЛЕЖ',
    'TEXNIKUM', 'TECHNICUM', 'ТЕХНИКУМ',
    'POLITEXNIKUM', 'POLYTECHNICUM', 'ПОЛИТЕХНИКУМ',
    'UNIVERSITET', 'UNIVERSITY', 'УНИВЕРСИТЕТ',
    'INSTITUT', 'INSTITUTE', 'ИНСТИТУТ',
    'AKADEMI', 'ACADEMY', 'АКАДЕМИ',
    'GIMNAZIYA', 'GYMNASIUM', 'ГИМНАЗИЯ',
)


def _has_institution_type_hint(text: str) -> bool:
    upper = text.upper()
    return any(hint in upper for hint in _INSTITUTION_TYPE_HINTS)


def _pretokenize_school_name(name: str) -> str:
    """
    Cleans up punctuation noise BEFORE the name reaches the AI, so the model
    always sees clean word boundaries instead of guessing across stray
    separators like '/', ',', '_', or doubled dashes.
    """
    import re as _re

    n = name.strip()
    # Collapse doubled/tripled dashes to a single dash: "3--maktab" -> "3-maktab"
    n = _re.sub(r'-{2,}', '-', n)
    # Treat '/', '_', and ',' between a number and a word as the same
    # separator as a dash or space, e.g. "3/maktab" / "3,maktab" / "3_maktab" -> "3-maktab"
    n = _re.sub(r'(\d)\s*[/_,]\s*', r'\1-', n)
    n = _re.sub(r'[/_,]\s*(\d)', r'-\1', n)
    # Collapse any remaining run of whitespace
    n = _re.sub(r'\s+', ' ', n).strip()
    return n


def normalize_school_name(raw_name: str, official_schools: Optional[List[str]] = None) -> str:
    """
    Normalizes a manually-typed school name (English, Uzbek, or mixed) into the
    CRM's house style, e.g.:
      "3RD vocational school"        -> "VOCATIONAL SCHOOL №3"
      "N3 General secondary school"  -> "GENERAL SECONDARY SCHOOL №3"
      "qorgontepa tumani 3-maktab"   -> "QORGONTEPA DISTRICT GENERAL SECONDARY SCHOOL №3"

    Falls back to a simple uppercase/whitespace cleanup (no translation) if no
    OpenAI key is configured or the API call fails, so the field is never
    blocked on AI availability.

    Guards against hallucination: if the input contains no recognizable
    institution-type word at all (e.g. a bare place name like "asaka", a bare
    number like "12", or filler text like "bilmadim"), the AI is never asked
    to invent one — the input is returned unchanged (just uppercased) for a
    human to fill in properly.
    """
    name = _pretokenize_school_name(raw_name or '')
    if not name:
        return name

    # Hallucination guard: no institution-type word present anywhere in the
    # input and it isn't just a pass-through directory match -> don't let the
    # AI fabricate an institution out of a bare word/number.
    if not _has_institution_type_hint(name):
        return name.upper()

    schools = official_schools or []
    api_key = os.environ.get("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "")

    if not api_key:
        return _fallback_normalize_school_name(name)

    schools_sample = schools[:150]

    system_instruction = (
        "You clean up school/university/college names typed by CRM staff in Uzbekistan into one "
        "consistent house style used by this CRM's school directory.\n\n"
        "Rules:\n"
        "1. Translate any Uzbek or Russian words into English using this exact dictionary — apply it "
        "regardless of spacing, hyphenation, or case in the input (e.g. 'kasb hunar kolleji', "
        "'kasb-hunar kolleji', and 'kasb-hunar kolleji' all mean the same thing):\n"
        "   - 'tumani'/'tuman' -> 'DISTRICT'\n"
        "   - 'shahar'/'shahri'/'shahridagi' -> 'CITY'\n"
        "   - 'viloyati' -> 'REGION'\n"
        "   - 'maktab'/'maktabi' / Russian 'школа' -> 'SCHOOL'\n"
        "   - 'umumiy o'rta ta'lim maktabi' / \"o'rta maktab\" -> 'GENERAL SECONDARY SCHOOL'\n"
        "   - 'kasb-hunar kolleji', 'kasb hunar kolleji' (with or without a hyphen/space), bare 'kollej', "
        "'texnika kolleji', 'professional kollej' -> 'VOCATIONAL COLLEGE'. A medical college "
        "('tibbiyot kolleji') -> 'MEDICAL COLLEGE', not 'VOCATIONAL COLLEGE'.\n"
        "   - 'litsey'/'litseyi' (with or without a hyphen/space), Russian 'лицей' -> 'LYCEUM'. "
        "'akademik litsey'/'akademik litseyi' -> 'ACADEMIC LYCEUM'.\n"
        "   - 'texnikum' -> 'TECHNICUM'\n"
        "   - 'politexnikum' -> 'POLYTECHNICUM'\n"
        "   - 'universitet' -> 'UNIVERSITY', 'institut' -> 'INSTITUTE', 'akademiya' -> 'ACADEMY'\n"
        "CRITICAL: 'TECHNICUM' and 'POLYTECHNICUM' are DIFFERENT institution types in Uzbekistan — never "
        "substitute one for the other. Uzbek 'texnikum' always maps to 'TECHNICUM', NOT 'POLYTECHNICUM'; "
        "only translate to 'POLYTECHNICUM' if the input literally says 'politexnikum' or 'polytechnicum'. "
        "Likewise 'LYCEUM' and 'VOCATIONAL COLLEGE' are different institution types from 'SCHOOL' and from "
        "each other — never substitute between them; only translate the Uzbek/Russian word that was actually "
        "typed.\n"
        "2. Output ALL UPPERCASE.\n"
        "3. Any school number (ordinal like '3rd', 'N3', a leading/trailing digit, or a Cyrillic/Latin "
        "numeral) MUST be rewritten as '№N' placed at the END of the institution-type phrase, never as a "
        "prefix and never spelled out as an ordinal. Example: '3RD VOCATIONAL SCHOOL' -> 'VOCATIONAL SCHOOL №3'. "
        "'N3 GENERAL SECONDARY SCHOOL' -> 'GENERAL SECONDARY SCHOOL №3'. '12-GENERAL SECONDARY SCHOOL' -> "
        "'GENERAL SECONDARY SCHOOL №12'.\n"
        "4. If a district/region name is present, keep it, formatted as '<DISTRICT NAME> DISTRICT' before the "
        "institution type, e.g. 'qorgontepa tumani 3-maktab' -> 'QORGONTEPA DISTRICT GENERAL SECONDARY SCHOOL №3'.\n"
        "5. Do not invent a school number if none was given.\n"
        "5b. If the input just says 'general school' / 'umumiy maktab' without specifying 'secondary' or "
        "'education', default it to 'GENERAL SECONDARY SCHOOL' (the more common of the two house-style "
        "variants). Only use 'GENERAL EDUCATION SCHOOL' when the input explicitly says 'education' (not "
        "'secondary').\n"
        "6. If the typed name already closely matches one of the official schools listed below (allowing for "
        "typos, punctuation, or spacing differences), return that OFFICIAL name exactly instead of your own "
        "reformatting. IMPORTANT: this only applies to spelling/spacing/punctuation variants of the SAME "
        "institution type and number — e.g. 'general sekondari school-14' matches 'GENERAL SECONDARY SCHOOL №14'. "
        "NEVER match across different institution types (TECHNICUM, POLYTECHNICUM, COLLEGE, LYCEUM, SCHOOL are all "
        "distinct) or different numbers — a district commonly has several separate technicums/polytechnicums/"
        "colleges numbered №1, №2, №3 etc, and each is a different real institution. If the exact type+number "
        "combination is not in the list, output your own reformatting instead of borrowing a similar-looking name "
        "from the list.\n"
        "7. If the input is a university/institute/academy name (not a numbered school), just clean up spelling, "
        "spacing and casing — do not force a '№' number onto it.\n"
        "8. CRITICAL — NEVER INVENT AN INSTITUTION: only translate/reformat words that are actually present in "
        "the input. Never add a district, region, or institution-type word that the input did not mention or "
        "clearly imply (e.g. a bare city/district name like 'Asaka' with nothing else is NOT enough basis to "
        "invent a full institution name — do not guess which school, college, or technicum the user meant). If "
        "the input is too incomplete or ambiguous to normalize confidently, return it unchanged (just cleaned "
        "up for spacing/casing) rather than fabricating details.\n\n"
        f"Official school directory (sample):\n{json.dumps(schools_sample)}\n\n"
        "Respond ONLY with valid JSON: {\"normalized_name\": \"...\"}"
    )

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": name}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0,
                "max_tokens": 200
            },
            timeout=10
        )

        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            normalized = str(parsed.get("normalized_name", "")).strip()
            return normalized if normalized else _fallback_normalize_school_name(name)

        logger.error(f"OpenAI error {resp.status_code} in normalize_school_name: {resp.text}")
        return _fallback_normalize_school_name(name)

    except Exception as e:
        logger.error(f"OpenAI call failed in normalize_school_name: {e}")
        return _fallback_normalize_school_name(name)


def _fallback_normalize_school_name(name: str) -> str:
    """Rule-based cleanup used when AI normalization is unavailable (no translation)."""
    import re as _re

    n = _re.sub(r'\s+', ' ', name).strip()

    # "NO"/"NO."/"NO1" + number -> "№N"
    n2 = _re.sub(r'\bNO\.?\s*(\d+)\b', lambda m: '№' + m.group(1), n, flags=_re.IGNORECASE)
    if n2 != n:
        return n2.upper()

    # Ordinal prefix, e.g. "3RD VOCATIONAL SCHOOL", "1-ST GENERAL SECONDARY SCHOOL"
    m = _re.match(r'^(\d+)-?(?:ST|ND|RD|TH)\s+(.+)$', n, _re.IGNORECASE)
    if m:
        return ('%s №%s' % (m.group(2).strip(), m.group(1))).upper()

    # Bare leading number + type, e.g. "12-GENERAL SECONDARY SCHOOL", "N3 GENERAL SECONDARY SCHOOL"
    m = _re.match(r'^N?(\d+)[\s-]+(.+)$', n, _re.IGNORECASE)
    if m:
        return ('%s №%s' % (m.group(2).strip(), m.group(1))).upper()

    return n.upper()
