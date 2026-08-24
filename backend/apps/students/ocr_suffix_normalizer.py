"""
OCR Name and Surname Suffix Normalization Layer for SalomCRM.

Provides context-aware fuzzy matching and normalization for Uzbek/Central Asian
patronymic and surname endings (e.g., UGLI, QIZI, OVICH, OVNA, ZODA, OV, EVA).
Corrects common OCR character confusions (0<->O, 1/L/l/T<->I, etc.) specifically
within person name contexts without modifying unrelated text.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

# =========================================================================
# 1. CENTRALIZED SUFFIX DICTIONARY & CANONICAL TARGETS
# =========================================================================

# Standalone Patronymic & Name Ending Targets
CANONICAL_STANDALONE_SUFFIXES = {
    'UGLI': [
        'UGLI', 'OGLI', 'UGIL', 'OGIL', 'AUGLI', 'AUGL', 'AUGN',
        'UGLT', 'UGL1', 'UGLl', 'UGL', 'O\'GLI', 'O‘GLI', 'O\'G\'LI', 'O‘G‘LI',
        'UGLJ', 'UGLI', 'OGLY', 'UGLY'
    ],
    'QIZI': [
        'QIZI', 'QIZ', 'QIZl', 'QIZ1', 'QIZT', 'QIZL'
    ],
    # KIZI is a valid passport spelling in its own right and must never be
    # rewritten to QIZI (they are distinct transliterations, not OCR errors).
    'KIZI': [
        'KIZI', 'KYZY', 'KIZ', 'KIZL', 'K1ZI', 'KIZl'
    ],
    'OVICH': [
        'OVICH', '0VICH', 'OVlCH', '0VlCH', 'OV1CH', '0V1CH', 'OVTC H', 'OVICН'
    ],
    'EVICH': [
        'EVICH', 'EVlCH', 'EV1CH', 'EVICН'
    ],
    'OVNA': [
        'OVNA', '0VNA', 'OVN4'
    ],
    'EVNA': [
        'EVNA', 'EVN4'
    ],
    'ZODA': [
        'ZODA', 'Z0DA', 'ZADA', 'ZOD4', 'Z0D4'
    ],
}

# Attached Suffix Targets (at the end of surnames or patronymics)
CANONICAL_ATTACHED_SUFFIXES = [
    'OVICH', 'EVICH', 'OVNA', 'EVNA',
    'YEVA', 'YEVA', 'OVA', 'EVA', 'YEV', 'EV', 'OV',
    'ZODA', 'ZADA'
]

# Common OCR Visual Digit & Homoglyph Substitution Table
OCR_CONFUSIONS = {
    '0': 'O',
    '1': 'I',
    '|': 'I',
    '!': 'I',
    ']': 'I',
    '[': 'I',
    'С': 'C',    # Cyrillic C -> Latin C
    'Н': 'H',    # Cyrillic H -> Latin H
    'В': 'B',    # Cyrillic B -> Latin B
    'Р': 'P',    # Cyrillic P -> Latin P
    '8': 'B',
    '5': 'S',
}

# Name Fields in CRM & Document Extractor where Suffix Normalization applies
NAME_FIELDS = {
    'FULL_NAME', 'FULL NAME', 'full_name',
    'SURNAME', 'surname', 'last_name',
    'GIVEN_NAMES', 'GIVEN NAMES', 'GIVEN_NAME', 'first_name',
    'FATHERS_NAME', 'FATHER_NAME', 'OTASINING_ISMI', 'middle_name', 'patronymic',
    'FATHER_FULLNAME', 'MOTHER_FULLNAME', 'father_name', 'mother_name',
    'STUDENT_NAME', 'student_name'
}

# Default Fuzzy Matching Similarity Threshold (0.0 to 1.0)
DEFAULT_SIMILARITY_THRESHOLD = 0.70


# =========================================================================
# 2. OCR-WEIGHTED FUZZY DISTANCE & NORMALIZATION ALGORITHM
# =========================================================================

def ocr_soft_normalize(s: str) -> str:
    """
    Normalizes a token by replacing common OCR digits / Cyrillic homoglyphs with canonical Latin letters.
    """
    if not s:
        return ""
    # Strip non-alphanumeric chars except apostrophes
    clean = re.sub(r'[^\w\'-]', '', s.upper())
    res = []
    for ch in clean:
        res.append(OCR_CONFUSIONS.get(ch, ch))
    return "".join(res)


def calculate_ocr_similarity(token: str, target: str) -> float:
    """
    Calculates weighted similarity between token and target.
    Known OCR substitutions have lower penalty (0.2) than random character edits (1.0).
    """
    t_clean = token.upper().replace("'", "").replace("‘", "").replace("’", "").replace("`", "")
    target_clean = target.upper().replace("'", "").replace("‘", "").replace("’", "").replace("`", "")

    if t_clean == target_clean:
        return 1.0

    # Test soft-normalized match
    t_soft = ocr_soft_normalize(t_clean)
    target_soft = ocr_soft_normalize(target_clean)
    if t_soft == target_soft:
        return 0.95

    # Levenshtein distance with OCR weight
    n, m = len(t_clean), len(target_clean)
    if n == 0 or m == 0:
        return 0.0

    dp = [[0.0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = float(i)
    for j in range(m + 1):
        dp[0][j] = float(j)

    for i in range(1, n + 1):
        c1 = t_clean[i - 1]
        for j in range(1, m + 1):
            c2 = target_clean[j - 1]
            if c1 == c2:
                cost = 0.0
            elif OCR_CONFUSIONS.get(c1) == c2 or OCR_CONFUSIONS.get(c2) == c1:
                cost = 0.25  # Very low penalty for known OCR character swap
            else:
                cost = 1.0

            dp[i][j] = min(
                dp[i - 1][j] + 1.0,        # Deletion
                dp[i][j - 1] + 1.0,        # Insertion
                dp[i - 1][j - 1] + cost     # Substitution
            )

    dist = dp[n][m]
    max_len = max(n, m)
    sim = max(0.0, 1.0 - (dist / max_len))
    return sim


# Real given names / words that are close enough to a suffix to be caught by
# fuzzy matching but must NEVER be rewritten (e.g. ODIL is not a garbled UGLI,
# OZODA is not a garbled ZODA, EVA/OVA are given names, not clipped OVNA/EVNA).
PROTECTED_NAME_TOKENS = {
    'ODIL', 'ODILA', 'OZODA', 'OZOD', 'OBID', 'OSIM', 'ORIF', 'OLIM', 'OLIMA',
    'ONA', 'OTA', 'OYIM', 'OGILOY', 'UGILOY', 'OYBEK', 'OGABEK',
    'EVA', 'OVA', 'NOVA', 'SEVA', 'IVA', 'ODINA',
    'KIZIL', 'QIZIL', 'ZUHRA', 'ZEBO', 'ZOKIR', 'ZAFAR',
}


def _is_ocr_plausible(token: str, target: str) -> bool:
    """
    True only if `token` can be explained as `target` plus known OCR confusions
    (digit/homoglyph swaps) rather than arbitrary letter edits.

    This is what separates a genuine misread ('QIZ1' -> 'QIZI') from a different
    real word that merely looks similar ('ODIL' vs 'OGIL' -> 'UGLI').
    """
    t = ocr_soft_normalize(token)
    g = ocr_soft_normalize(target)
    if t == g:
        return True
    # Same length: every differing position must be a known OCR confusion pair.
    if len(t) == len(g):
        for c1, c2 in zip(t, g):
            if c1 == c2:
                continue
            if OCR_CONFUSIONS.get(c1) == c2 or OCR_CONFUSIONS.get(c2) == c1:
                continue
            return False
        return True
    return False


def normalize_standalone_suffix(token: str, threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> Tuple[str, bool]:
    """
    Attempts to match and normalize a standalone token into a canonical patronymic suffix.
    Returns (normalized_token, was_changed).

    Correction is deliberately conservative: a token is only rewritten when it is
    an exact known variant, or when the difference is fully explained by OCR
    character confusions. Real names that merely resemble a suffix are preserved.
    """
    clean = token.strip().upper()
    if not clean or len(clean) < 2:
        return token, False

    # Never touch known real-word tokens, even if they resemble a suffix.
    if clean in PROTECTED_NAME_TOKENS:
        return token, False

    # Check direct dictionary lookup first
    for canonical, variants in CANONICAL_STANDALONE_SUFFIXES.items():
        if clean in variants or ocr_soft_normalize(clean) == canonical:
            if clean != canonical:
                logger.debug(f"[OCR Suffix] Direct match: '{token}' -> '{canonical}'")
                return canonical, True
            return canonical, False

    # Fuzzy match across all canonical candidates. Only OCR-plausible rewrites
    # are considered, so unrelated real words are left alone.
    best_candidate = None
    best_score = 0.0

    for canonical, variants in CANONICAL_STANDALONE_SUFFIXES.items():
        for cand in [canonical] + variants:
            score = calculate_ocr_similarity(clean, cand)
            if score > best_score and _is_ocr_plausible(clean, cand):
                best_score = score
                best_candidate = canonical

    if best_candidate and best_score >= threshold:
        logger.debug(f"[OCR Suffix] Fuzzy match: '{token}' -> '{best_candidate}' (sim: {best_score:.2f})")
        return best_candidate, True

    return token, False


VALID_ATTACHED_SUFFIXES = [
    'OVICH', 'EVICH', 'OVNA', 'EVNA',
    'ZODA', 'ZADA',
    'YEVA', 'IEVA', 'OVA', 'EVA',
    'YEV', 'IEV', 'OV', 'EV'
]


def normalize_attached_suffix(word: str, threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> Tuple[str, bool]:
    """
    Normalizes attached surname / patronymic endings within a word.
    e.g. 'VALIYEV0VICH' -> 'VALIYEVOVICH', 'ISMOILOVZ0DA' -> 'ISMOILOVZODA', 'ZOKIR0V' -> 'ZOKIROV', 'AL1YEV' -> 'ALIYEV'.
    Preserves valid existing suffix spellings (such as ALIEVA, VALIYEVA, KARIMOV).
    """
    clean = word.strip().upper()
    if len(clean) <= 3:
        return word, False

    # 1. If word already ends with a known valid suffix, just check root digits
    for valid_suf in sorted(VALID_ATTACHED_SUFFIXES, key=lambda s: len(s), reverse=True):
        if clean.endswith(valid_suf) and len(clean) >= len(valid_suf) + 2:
            base = clean[:-len(valid_suf)]
            clean_base = ocr_soft_normalize(base)
            corrected_word = clean_base + valid_suf
            if corrected_word != word:
                return corrected_word, True
            return word, False

    # 2. Suffix has OCR errors (e.g. ending in 0V, 0VA, Z0DA, 0VICH, 0VNA)
    for suffix in sorted(VALID_ATTACHED_SUFFIXES, key=lambda s: len(s), reverse=True):
        s_len = len(suffix)
        if len(clean) < s_len + 2:
            continue

        tail = clean[-s_len:]
        base = clean[:-s_len]

        # Check OCR-weighted similarity on tail suffix
        sim = calculate_ocr_similarity(tail, suffix)
        if sim >= threshold:
            clean_base = ocr_soft_normalize(base)
            corrected_word = clean_base + suffix
            if corrected_word != word:
                logger.debug(f"[OCR Suffix] Attached suffix fix: '{word}' -> '{corrected_word}' (tail: {tail} -> {suffix}, sim: {sim:.2f})")
                return corrected_word, True

    return word, False


# =========================================================================
# 3. HIGH-LEVEL NAME NORMALIZATION API
# =========================================================================

def normalize_full_name(raw_name: str) -> str:
    """
    Normalizes full name string by correcting OCR patronymic and surname suffixes.
    Preserves word order, clean spacing, and standard capitalization.
    
    Examples:
    - 'ABDULLOH UGLT' -> 'ABDULLOH UGLI'
    - 'BOTIR UGL1' -> 'BOTIR UGLI'
    - 'ANVAR QIZl' -> 'ANVAR QIZI'
    - 'TURSUNOVZ0DA' -> 'TURSUNOVZODA'
    - 'ALIEV0VICH' -> 'ALIEVOVICH'
    """
    if not raw_name or not isinstance(raw_name, str):
        return ""

    # Clean whitespace and strip stray symbols
    clean = re.sub(r'[^A-ZА-Яa-zа-я0-9\s\'\‘\’\`-]', ' ', raw_name)
    tokens = [t.strip() for t in clean.split() if t.strip()]

    if not tokens:
        return ""

    normalized_tokens = []
    n = len(tokens)

    for i, token in enumerate(tokens):
        is_last = (i == n - 1)
        is_first = (i == 0)
        up_token = token.upper()

        # Case 1: Standalone patronymic token at the end of the full name (e.g. '... UGLT', '... QIZl')
        if is_last and n >= 2:
            fixed_token, changed = normalize_standalone_suffix(up_token)
            if changed:
                normalized_tokens.append(fixed_token)
                continue

        # Case 2: Attached surname/patronymic ending (e.g. 'ZOKIR0V', 'ALIYEV0VICH', 'RAHMATZ0DA')
        fixed_word, changed_attached = normalize_attached_suffix(up_token)
        if changed_attached:
            normalized_tokens.append(fixed_word)
            continue

        # Case 3: Joined patronymic at the end of word (e.g. 'BOTIRUGLI' or 'RUSTAMQIZI')
        joined_m = re.search(r'^(.*?)[\s_-]*(AUGN|AUGL|AUGLI|UGLI|OGLI|UGIL|OGIL|UGL|UGLT|UGL1|UGLl|QIZI|KIZI|KYZY|QIZ|KIZ|QIZl|QIZ1)$', up_token, re.IGNORECASE)
        if joined_m and len(joined_m.group(1)) >= 3:
            base_part = joined_m.group(1).strip()
            suffix_part = joined_m.group(2).strip()
            norm_suffix, _ = normalize_standalone_suffix(suffix_part)
            normalized_tokens.append(f"{base_part} {norm_suffix}")
            continue

        normalized_tokens.append(up_token)

    return " ".join(normalized_tokens)


def normalize_extracted_fields(fields_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies OCR name/surname normalization to all name fields in an extracted document payload.
    """
    if not fields_dict or not isinstance(fields_dict, dict):
        return fields_dict

    updated = dict(fields_dict)

    for field_key, field_val in fields_dict.items():
        if not field_val or not isinstance(field_val, str):
            continue

        norm_key = field_key.upper().replace(' ', '_')
        if norm_key in NAME_FIELDS or field_key in NAME_FIELDS:
            corrected = normalize_full_name(field_val)
            if corrected and corrected != field_val:
                logger.info(f"[OCR Suffix Normalizer] Field '{field_key}' corrected: '{field_val}' -> '{corrected}'")
                updated[field_key] = corrected

    return updated
