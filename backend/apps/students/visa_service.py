import re
import time
import urllib.parse
import requests
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, parse_qs

HOST = "https://www.visa.go.kr"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# In-memory session cookie cache (10 min TTL)
_cached_session_cookies: Optional[requests.cookies.RequestsCookieJar] = None
_session_fetched_at: float = 0
SESSION_TTL_SECONDS = 600

KOREAN_STATUS_MAP = [
    ({"사용완료"}, "VISA USED"),
    ({"불허"}, "REJECTED"),
    ({"허가", "발급"}, "APPROVED"),
    ({"접수", "신청"}, "RECEIVED"),
    ({"심사중", "처리중", "심사 중", "처리 중"}, "UNDER REVIEW"),
    ({"취소"}, "CANCELLED"),
    ({"반려"}, "RETURNED"),
    ({"보완완료", "보완제출", "보완접수"}, "SUPPLEMENT SUBMITTED"),
    ({"보완대기", "보완요청", "보완요구", "보완"}, "SUPPLEMENT NEEDED"),
    ({"기한만료"}, "EXPIRED"),
]


def parse_korean_status(korean: str) -> str:
    if not korean:
        return "UNKNOWN"
    for keywords, status in KOREAN_STATUS_MAP:
        if any(kw in korean for kw in keywords):
            return status
    return korean.strip()


def strip_html_tags(text: str) -> str:
    if not text:
        return ""
    # Remove HTML comments
    clean = re.sub(r"<!--[\s\S]*?-->", " ", text)
    # Remove HTML tags
    clean = re.sub(r"<[^>]*>", " ", clean)
    # Collapse whitespace
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def extract_rejection_reasons(html: str) -> List[Dict[str, Any]]:
    matches = []

    # Pattern 1: <th class="no_reason">...</th> <td>...</td>
    pattern1 = re.compile(
        r'<th[^>]*class=["\']no_reason["\'][^>]*>[\s\S]*?</th>\s*<td[^>]*>([\s\S]*?)</td>',
        re.IGNORECASE,
    )
    for m in pattern1.finditer(html):
        txt = strip_html_tags(m.group(1))
        txt = re.sub(
            r"^귀하의\s*비자신청에\s*대한\s*불허사유는\s*다음과\s*같습니다\s*:\s*",
            "",
            txt,
            flags=re.IGNORECASE,
        ).strip()
        if txt:
            matches.append({"text": txt, "index": m.start()})

    # Pattern 2: <th>...불허사유...</th> <td>...</td>
    if not matches:
        pattern2 = re.compile(
            r"<th[^>]*>[^<]*불허사유[^<]*</th>\s*<td[^>]*>([\s\S]*?)</td>",
            re.IGNORECASE,
        )
        for m in pattern2.finditer(html):
            txt = strip_html_tags(m.group(1))
            txt = re.sub(
                r"^귀하의\s*비자신청에\s*대한\s*불허사유는\s*다음과\s*같습니다\s*:\s*",
                "",
                txt,
                flags=re.IGNORECASE,
            ).strip()
            if txt:
                matches.append({"text": txt, "index": m.start()})

    # Pattern 3: Fallback text search
    if not matches:
        pattern3 = re.compile(
            r"귀하의\s*비자신청에\s*대한\s*불허사유는\s*다음과\s*같습니다[\s\S]*?:\s*([\s\S]*?)(?:</td>|</div>)",
            re.IGNORECASE,
        )
        for m in pattern3.finditer(html):
            txt = strip_html_tags(m.group(1))
            txt = re.sub(
                r"^귀하의\s*비자신청에\s*대한\s*불허사유는\s*다음과\s*같습니다\s*:\s*",
                "",
                txt,
                flags=re.IGNORECASE,
            ).strip()
            if txt:
                matches.append({"text": txt, "index": m.start()})

    return matches


def get_session(force_refresh: bool = False) -> requests.Session:
    """Creates a configured requests Session with cookies warmed up."""
    global _cached_session_cookies, _session_fetched_at
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )

    now = time.time()
    if (
        not force_refresh
        and _cached_session_cookies
        and (now - _session_fetched_at) < SESSION_TTL_SECONDS
    ):
        session.cookies.update(_cached_session_cookies)
        return session

    try:
        resp = session.get(
            f"{HOST}/openPage.do?MENU_ID=10301",
            timeout=10,
        )
        if resp.cookies:
            _cached_session_cookies = session.cookies.copy()
            _session_fetched_at = now
    except Exception as e:
        # Proceed with empty session if handshake fails
        pass

    return session


def format_date_str(raw: str) -> str:
    raw = raw.strip()
    if re.match(r"^\d{8}$", raw):
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw.replace(".", "-").rstrip("-")


def parse_result_embassy_gb03(html: str) -> List[Dict[str, Any]]:
    """Parses gb03 (Diplomatic Mission / Embassy) results from result3_2 section."""
    results = []

    # 1. Extract dates
    def extract_field_values(field_id: str) -> List[str]:
        pattern = re.compile(rf'id="{field_id}"[^>]*>([\s\S]*?)<', re.IGNORECASE)
        vals = []
        for m in pattern.finditer(html):
            v = re.sub(r"\s+", " ", m.group(1)).strip()
            if v:
                vals.append(v)
        return vals

    appl_dates = [
        format_date_str(d) for d in extract_field_values("RECPT_YMD")
    ]
    if not appl_dates:
        appl_dates = [
            format_date_str(d) for d in extract_field_values("APPL_YMD")
        ]
    if not appl_dates:
        appl_dates = [
            format_date_str(d) for d in extract_field_values("APPL_DTM")
        ]

    # 2. Extract statuses with positions
    status_matches = list(
        re.finditer(
            r'id="PROC_STS_CDNM_1"[^>]*>([\s\S]*?)</div>', html, re.IGNORECASE
        )
    )
    statuses = [
        {"text": strip_html_tags(m.group(1)), "index": m.start()}
        for m in status_matches
    ]

    # 3. Extract rejection reasons
    rej_reasons = extract_rejection_reasons(html)
    status_count = len(statuses)
    mapped_rejections = [""] * status_count

    for rej in rej_reasons:
        best_idx = -1
        for i in range(status_count):
            if statuses[i]["index"] < rej["index"]:
                best_idx = i
        if best_idx != -1:
            mapped_rejections[best_idx] = rej["text"]

    # 4. Entry purpose
    purpose_matches = list(
        re.finditer(r'id="ENTRY_PURPOSE"[^>]*>([^<]+)<', html, re.IGNORECASE)
    )
    purposes = [m.group(1).strip() for m in purpose_matches]

    # 5. Judgment dates (심사일자)
    judg_matches = list(
        re.finditer(
            r'id="JUDG_(?:DTM|YMD)"[^>]*>([\s\S]*?)</(?:div|td)>',
            html,
            re.IGNORECASE,
        )
    )
    judg_dates = [
        format_date_str(strip_html_tags(m.group(1))) for m in judg_matches
    ]

    total_records = max(len(appl_dates), status_count)
    for i in range(total_records):
        status_kor = statuses[i]["text"] if i < status_count else ""
        parsed_status = parse_korean_status(status_kor)

        entry_date = ""
        if i < len(judg_dates) and re.match(r"\d{4}-\d{2}-\d{2}", judg_dates[i]):
            entry_date = judg_dates[i]
        else:
            date_m = re.search(r"(\d{4}[.-]\d{2}[.-]\d{2})", status_kor)
            if date_m:
                entry_date = date_m.group(1).replace(".", "-").rstrip("-")
            elif parsed_status == "APPROVED":
                html_dm = re.search(
                    r'id="JUDG_(?:DTM|YMD)"[\s\S]{0,200}?(\d{4}[.-]\d{2}[.-]\d{2})',
                    html,
                    re.IGNORECASE,
                )
                if html_dm:
                    entry_date = html_dm.group(1).replace(".", "-")

        app_date_val = appl_dates[i] if i < len(appl_dates) else ""
        if entry_date == app_date_val:
            entry_date = ""

        is_reject = parsed_status in [
            "REJECTED",
            "CANCELLED",
            "RETURNED",
        ] or "SUPPLEMENT" in parsed_status

        results.append(
            {
                "application_date": app_date_val,
                "status": parsed_status,
                "status_korean": status_kor,
                "entry_date": entry_date,
                "entry_purpose": purposes[i] if i < len(purposes) else "",
                "rejection_reason": (
                    mapped_rejections[i] if (is_reject and i < len(mapped_rejections)) else ""
                ),
            }
        )

    return results


def parse_result_evisa_gb01(html: str) -> List[Dict[str, Any]]:
    """Parses gb01/gb02 (E-Visa / Regional) results from result1_1 section."""
    results = []

    appl_date_matches = list(
        re.finditer(r'id="APPL_YMD"[^>]*>([^<]+)<', html, re.IGNORECASE)
    )
    appl_dates = [format_date_str(m.group(1)) for m in appl_date_matches]

    status_matches = list(
        re.finditer(r'id="PROC_STS_CDNM"[^>]*>([\s\S]*?)</div>', html, re.IGNORECASE)
    )
    statuses = [
        {"text": strip_html_tags(m.group(1)), "index": m.start()}
        for m in status_matches
    ]

    rej_reasons = extract_rejection_reasons(html)
    status_count = len(statuses)
    mapped_rejections = [""] * status_count

    for rej in rej_reasons:
        best_idx = -1
        for i in range(status_count):
            if statuses[i]["index"] < rej["index"]:
                best_idx = i
        if best_idx != -1:
            mapped_rejections[best_idx] = rej["text"]

    purpose_matches = list(
        re.finditer(r'id="SOJ_QUAL_NM"[^>]*>([^<]+)<', html, re.IGNORECASE)
    )
    purposes = [m.group(1).strip() for m in purpose_matches]

    judg_matches = list(
        re.finditer(
            r'id="JUDG_DTM"[^>]*>([\s\S]*?)</div>', html, re.IGNORECASE
        )
    )
    judg_dates = [
        format_date_str(strip_html_tags(m.group(1))) for m in judg_matches
    ]

    total_records = max(len(appl_dates), status_count)
    for i in range(total_records):
        status_kor = statuses[i]["text"] if i < status_count else ""
        parsed_status = parse_korean_status(status_kor)

        entry_date = ""
        if i < len(judg_dates) and re.match(r"\d{4}-\d{2}-\d{2}", judg_dates[i]):
            entry_date = judg_dates[i]
        else:
            date_m = re.search(r"(\d{4}[.-]\d{2}[.-]\d{2})", status_kor)
            if date_m:
                entry_date = date_m.group(1).replace(".", "-").rstrip("-")

        app_date_val = appl_dates[i] if i < len(appl_dates) else ""
        if entry_date == app_date_val:
            entry_date = ""

        is_reject = parsed_status in [
            "REJECTED",
            "CANCELLED",
            "RETURNED",
        ] or "SUPPLEMENT" in parsed_status

        results.append(
            {
                "application_date": app_date_val,
                "status": parsed_status,
                "status_korean": status_kor,
                "entry_date": entry_date,
                "entry_purpose": purposes[i] if i < len(purposes) else "",
                "rejection_reason": (
                    mapped_rejections[i] if (is_reject and i < len(mapped_rejections)) else ""
                ),
            }
        )

    return results


def check_visa_direct(
    passport: str,
    full_name: str,
    birth_date: str,
    visa_type: str = "Embassy",
    application_no: str = "",
) -> Dict[str, Any]:
    """Queries visa status directly from visa.go.kr."""
    cleaned_passport = passport.strip().upper()
    cleaned_name = re.sub(r"\s+", " ", full_name.strip()).upper()
    cleaned_dob = birth_date.strip()
    cleaned_app_no = application_no.strip().upper()
    visa_type = visa_type.strip()

    is_evisa = (visa_type == "E-Visa") and bool(cleaned_app_no)
    is_regional = (visa_type == "Regional") and bool(cleaned_app_no)

    if is_evisa:
        body_params = {
            "pRADIOSEARCH": "gb01",
            "sINVITEE_SEQ": cleaned_app_no,
            "ssINVITEE_SEQ": cleaned_app_no,
            "sPASS_NO": cleaned_passport,
            "sEK_NM": cleaned_name,
            "sFROMDATE": cleaned_dob,
            "sMainPopUpGB": "main",
        }
    elif is_regional:
        body_params = {
            "pRADIOSEARCH": "gb02",
            "sBUSI_GB_gb02": "INVITEE_SEQ_gb02",
            "sPASS_NO": cleaned_passport,
            "sINVITEE_SEQ": cleaned_app_no,
            "ssINVITEE_SEQ": cleaned_app_no,
            "ssBUSI_GBNO_gb02": cleaned_app_no,
            "sEK_NM": cleaned_name,
            "sFROMDATE": cleaned_dob,
            "sMainPopUpGB": "main",
        }
    else:
        body_params = {
            "pRADIOSEARCH": "gb03",
            "sBUSI_GB": "PASS_NO",
            "sBUSI_GBNO": cleaned_passport,
            "ssBUSI_GBNO": cleaned_passport,
            "sEK_NM": cleaned_name,
            "sFROMDATE": cleaned_dob,
            "sMainPopUpGB": "main",
        }

    session = get_session()
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": f"{HOST}/openPage.do?MENU_ID=10301",
        "Origin": HOST,
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    try:
        resp = session.post(
            f"{HOST}/openPage.do?MENU_ID=10301",
            data=body_params,
            headers=headers,
            timeout=15,
        )
    except Exception:
        # Retry with fresh session
        session = get_session(force_refresh=True)
        resp = session.post(
            f"{HOST}/openPage.do?MENU_ID=10301",
            data=body_params,
            headers=headers,
            timeout=15,
        )

    html = resp.text

    # Check for not-found condition
    count_m = re.search(r'"(\d+)"\s*==\s*0', html)
    result_count = int(count_m.group(1)) if count_m else None

    has_status_elements = bool(
        re.search(
            r'id="PROC_STS_CDNM"' if (is_evisa or is_regional) else r'id="PROC_STS_CDNM_1"',
            html,
        )
    )

    if result_count == 0 and not has_status_elements:
        return {
            "found": False,
            "records": [],
            "latest_status": "NOT FOUND",
            "latest_status_korean": "",
            "latest_date": "",
            "result_count": 0,
        }

    records = (
        parse_result_evisa_gb01(html)
        if (is_evisa or is_regional)
        else parse_result_embassy_gb03(html)
    )

    if not records:
        return {
            "found": False,
            "records": [],
            "latest_status": "NOT FOUND",
            "latest_status_korean": "",
            "latest_date": "",
            "result_count": 0,
        }

    if result_count is None:
        result_count = len(records)

    latest = records[0]

    # Extract dynamic variables for printing/downloading certificate PDF
    ev_seq = (re.search(r'var\s+evSeq\s*=\s*"([^"]+)"', html) or [None, ""])[1]
    ccvi_seq = (re.search(r'var\s+ccvi_seq\s*=\s*"([^"]+)"', html) or [None, ""])[1]
    inv_seq = (
        re.search(r'var\s+(?:invSeq|invitee_seq)\s*=\s*"([^"]+)"', html)
        or [None, ""]
    )[1]
    appl_no = (re.search(r'var\s+applNo\s*=\s*"([^"]+)"', html) or [None, ""])[1]
    ccvi_appl_no = (
        re.search(r'var\s+ccviApplNo\s*=\s*"([^"]+)"', html) or [None, ""]
    )[1]

    if not ev_seq:
        report_m = re.search(
            r"fn_reportBy\w*\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]*)['\"]\s*,\s*['\"]([^'\"]*)['\"]",
            html,
            re.IGNORECASE,
        )
        if report_m:
            ev_seq = report_m.group(1)
            inv_seq = report_m.group(2) or "0"
            appl_no = report_m.group(3) or ""

    if not ev_seq:
        ev_m = re.search(r"(?:evSeq|EV_SEQ)=([^&\"'\s]+)", html, re.IGNORECASE)
        if ev_m:
            ev_seq = ev_m.group(1)
            inv_m = re.search(
                r"(?:invSeq|INVITEE_SEQ)=([^&\"'\s]+)", html, re.IGNORECASE
            )
            app_m = re.search(
                r"(?:applNo|APPL_NO)=([^&\"'\s]+)", html, re.IGNORECASE
            )
            inv_seq = inv_m.group(1) if inv_m else "0"
            appl_no = app_m.group(1) if app_m else ""

    pdf_url = ""
    if ev_seq or ccvi_seq:
        pdf_url = (
            f"{HOST}/biz/ap/ev/selectElectronicVisaPrint3.do?"
            f"evSeq={ev_seq}&invSeq={inv_seq}&applNo={appl_no}&ccviApplNo={ccvi_appl_no}&ccviSeq={ccvi_seq}"
        )

    # Extra fields
    visa_expiry = ""
    expr_m = re.search(
        r'id="VISA_EXPR_YMD"[^>]*>([\s\S]*?)</div>', html, re.IGNORECASE
    )
    if expr_m:
        raw_expr = strip_html_tags(expr_m.group(1))
        date_m = re.search(r"(\d{4}\.\d{2}\.\d{2})", raw_expr)
        if date_m:
            visa_expiry = date_m.group(1).replace(".", "-")

    visa_kind = ""
    kind_m = re.search(
        r'id="VISA_KIND_CD"[^>]*>([\s\S]*?)</div>', html, re.IGNORECASE
    )
    if kind_m:
        raw_kind = strip_html_tags(kind_m.group(1)).lower()
        if "단수" in raw_kind:
            visa_kind = "Single"
        elif "복수" in raw_kind:
            visa_kind = "Multiple"
        else:
            visa_kind = strip_html_tags(kind_m.group(1))

    residence_classes = [
        m.group(1).strip()
        for m in re.finditer(r'id="SOJ_QUAL_NM"[^>]*>([^<]+)', html, re.IGNORECASE)
    ]
    status_of_residence = residence_classes[-1] if residence_classes else ""

    inviters = [
        m.group(1).strip()
        for m in re.finditer(r'id="MEM_NM"[^>]*>([^<]+)', html, re.IGNORECASE)
    ]
    inviting_company = inviters[-1] if inviters else ""

    return {
        "found": True,
        "records": records,
        "result_count": result_count,
        "latest_status": latest.get("status") or "UNKNOWN",
        "latest_status_korean": latest.get("status_korean") or "",
        "latest_date": latest.get("application_date") or "",
        "entry_date": latest.get("entry_date") or "",
        "entry_purpose": latest.get("entry_purpose") or "",
        "rejection_reason": latest.get("rejection_reason") or "",
        "visa_expiry": visa_expiry,
        "visa_kind": visa_kind,
        "status_of_residence": status_of_residence,
        "inviting_company": inviting_company,
        "pdf_url": pdf_url,
        "ccvi_appl_no": ccvi_appl_no,
        "ccvi_seq": ccvi_seq,
        "ev_seq": ev_seq,
        "inv_seq": inv_seq,
        "appl_no": appl_no,
    }


def download_visa_pdf(
    passport: str,
    full_name: str,
    birth_date: str,
    visa_type: str = "Embassy",
    application_no: str = "",
    pdf_url: str = "",
) -> bytes:
    """Downloads binary PDF certificate from visa.go.kr."""
    cleaned_passport = passport.strip().upper()
    cleaned_name = re.sub(r"\s+", " ", full_name.strip()).upper()
    cleaned_dob = birth_date.strip()
    birth_ymd = cleaned_dob.replace("-", "")
    cleaned_app_no = application_no.strip().upper()
    visa_type = visa_type.strip()

    is_regional = (visa_type == "Regional")
    is_evisa = (visa_type == "E-Visa" or is_regional) and bool(cleaned_app_no)

    ev_seq = ""
    inv_seq = "0"
    appl_no = ""
    ccvi_appl_no = ""
    ccvi_seq = ""

    if pdf_url:
        parsed = urlparse(pdf_url)
        q = parse_qs(parsed.query)
        ev_seq = (q.get("evSeq") or [""])[0]
        inv_seq = (q.get("invSeq") or ["0"])[0]
        appl_no = (q.get("applNo") or [""])[0]
        ccvi_appl_no = (q.get("ccviApplNo") or [""])[0]
        ccvi_seq = (q.get("ccviSeq") or [""])[0]

    if not pdf_url or (is_regional and (not ccvi_seq or not ccvi_appl_no)):
        res = check_visa_direct(
            cleaned_passport, cleaned_name, cleaned_dob, visa_type, cleaned_app_no
        )
        if not res.get("found") or not res.get("pdf_url"):
            raise ValueError("No visa record or PDF download parameters found on visa.go.kr.")
        parsed = urlparse(res["pdf_url"])
        q = parse_qs(parsed.query)
        ev_seq = (q.get("evSeq") or [""])[0]
        inv_seq = (q.get("invSeq") or ["0"])[0]
        appl_no = (q.get("applNo") or [""])[0]
        ccvi_appl_no = (q.get("ccviApplNo") or [""])[0]
        ccvi_seq = (q.get("ccviSeq") or [""])[0]

    session = get_session(force_refresh=True)

    # Pre-populate search in session
    if is_evisa:
        body_params = {
            "pRADIOSEARCH": "gb01",
            "sINVITEE_SEQ": cleaned_app_no,
            "ssINVITEE_SEQ": cleaned_app_no,
            "sPASS_NO": cleaned_passport,
            "sEK_NM": cleaned_name,
            "sFROMDATE": cleaned_dob,
            "sMainPopUpGB": "main",
        }
    elif is_regional:
        body_params = {
            "pRADIOSEARCH": "gb02",
            "sBUSI_GB_gb02": "INVITEE_SEQ_gb02",
            "sPASS_NO": cleaned_passport,
            "sINVITEE_SEQ": cleaned_app_no,
            "ssINVITEE_SEQ": cleaned_app_no,
            "ssBUSI_GBNO_gb02": cleaned_app_no,
            "sEK_NM": cleaned_name,
            "sFROMDATE": cleaned_dob,
            "sMainPopUpGB": "main",
        }
    else:
        body_params = {
            "pRADIOSEARCH": "gb03",
            "sBUSI_GB": "PASS_NO",
            "sBUSI_GBNO": cleaned_passport,
            "ssBUSI_GBNO": cleaned_passport,
            "sEK_NM": cleaned_name,
            "sFROMDATE": cleaned_dob,
            "sMainPopUpGB": "main",
        }

    headers = {
        "User-Agent": USER_AGENT,
        "Referer": f"{HOST}/openPage.do?MENU_ID=10301",
        "Origin": HOST,
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    session.post(
        f"{HOST}/openPage.do?MENU_ID=10301",
        data=body_params,
        headers=headers,
        timeout=15,
    )

    if is_regional:
        print_params = {
            "PARAM_CCVI_SEQ": ccvi_seq,
            "INVITEE_SEQ": inv_seq,
            "PARAM_CCVI_APPL_NO": ccvi_appl_no,
        }
        print_path = "/biz/si/pr/selectVisaPrintOnOff.do"
    else:
        print_params = {
            "sBUSI_GB": "PASS_NO",
            "sBUSI_GBNO": cleaned_passport,
            "EV_SEQ": ev_seq,
            "INVITEE_SEQ": inv_seq,
            "APPL_NO": appl_no,
            "ENG_NM": cleaned_name,
            "BIRTH_YMD": birth_ymd,
            "IN_PHOTO": "/biz/ap/ev/selectInviteeXvarmImage.do",
            "TRAN_TYPE": "ComSubmit",
            "SE_FLAG_YN": "",
            "LANG_TYPE": "KO",
            "CMM_TEST_VAL": "test",
        }
        print_path = "/biz/ap/ev/selectElectronicVisaPrint3.do"

    print_headers = {
        "User-Agent": USER_AGENT,
        "Referer": f"{HOST}/openPage.do?MENU_ID=10301",
        "Origin": HOST,
        "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    pdf_resp = session.post(
        f"{HOST}{print_path}",
        data=print_params,
        headers=print_headers,
        timeout=25,
    )

    content_type = pdf_resp.headers.get("Content-Type", "").lower()
    if pdf_resp.status_code != 200:
        raise RuntimeError(f"visa.go.kr returned HTTP {pdf_resp.status_code}")

    if "pdf" not in content_type and "octet-stream" not in content_type:
        raise RuntimeError("visa.go.kr did not return a valid PDF certificate file.")

    return pdf_resp.content
