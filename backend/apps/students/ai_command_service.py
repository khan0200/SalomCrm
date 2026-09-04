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
