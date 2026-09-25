import hashlib
import hmac
import json
import logging
import time
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class DiditNotConfigured(Exception):
    """Raised when DIDIT_API_KEY / DIDIT_WORKFLOW_ID haven't been set yet."""


def _require_config():
    if not settings.DIDIT_API_KEY or not settings.DIDIT_WORKFLOW_ID:
        raise DiditNotConfigured(
            'DIDIT_API_KEY and DIDIT_WORKFLOW_ID must be set (create a workflow '
            'in the Didit dashboard first) before identity verification can start.'
        )


def create_verification_session(vendor_data: str = '') -> dict:
    """
    Creates a new Didit verification session for the configured workflow.
    Returns the raw {session_id, url, session_token, ...} response.

    `vendor_data` is an opaque string Didit echoes back unchanged in the
    webhook/decision payload - used to carry our own IdentityVerification id
    so the webhook handler can find the right row without guessing.
    """
    _require_config()
    resp = requests.post(
        f'{settings.DIDIT_BASE_URL}/v3/session/',
        headers={'x-api-key': settings.DIDIT_API_KEY, 'Content-Type': 'application/json'},
        json={'workflow_id': settings.DIDIT_WORKFLOW_ID, 'vendor_data': vendor_data},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def get_session_decision(session_id: str) -> dict:
    """Fetches the current decision/result for a session."""
    _require_config()
    resp = requests.get(
        f'{settings.DIDIT_BASE_URL}/v3/session/{session_id}/decision/',
        headers={'x-api-key': settings.DIDIT_API_KEY},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def _canonicalize(value):
    """
    Mirrors Didit's own canonicalization before signing: floats that are
    whole numbers collapse to ints (so 5.0 and 5 sign identically), applied
    recursively through dicts/lists.
    """
    if isinstance(value, float) and value == int(value):
        return int(value)
    if isinstance(value, dict):
        return {k: _canonicalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_canonicalize(v) for v in value]
    return value


def _hmac_hex(secret: str, message: str) -> str:
    return hmac.new(secret.encode(), message.encode('utf-8'), hashlib.sha256).hexdigest()


def verify_webhook(body_dict: dict, headers) -> bool:
    """
    Verifies an inbound webhook actually came from Didit. Without this,
    anyone who finds our webhook URL could POST a fake "Approved" decision
    for any session_id.

    Didit's own docs describe two signing schemes and were unverifiable
    against a live payload before this went live (no test webhook available
    ahead of time) - a first production attempt (6/6 deliveries) failed
    verification, so this now tries every documented combination rather
    than a single hard-coded interpretation:
      - timestamp from the X-Timestamp header, or from the body's own
        "timestamp" field, if the header is absent
      - the primary scheme: HMAC-SHA256("{timestamp}:{canonical_json}"),
        canonical JSON = sorted keys, compact separators, whole-number
        floats collapsed to ints
      - the documented fallback: HMAC-SHA256 of
        "{timestamp}:{session_id}:{status}:{webhook_type}" only
    Accepting whichever combination matches is still fully secure - every
    path requires DIDIT_WEBHOOK_SECRET, so a forged request can't satisfy
    any of them without it.

    `headers` is anything supporting .get(name), e.g. a Django
    HttpHeaders/request.headers object.

    Returns False (never raises) when the secret isn't configured, no
    signature header is present at all, or every combination is stale/
    mismatched - callers must treat that as "cannot verify", not
    "verified".
    """
    secret = settings.DIDIT_WEBHOOK_SECRET
    signature = headers.get('X-Signature') or headers.get('X-Signature-Simple')
    if not secret or not signature:
        return False

    header_ts = headers.get('X-Timestamp')
    body_ts = body_dict.get('timestamp') if isinstance(body_dict, dict) else None
    candidate_timestamps = [t for t in (header_ts, str(body_ts) if body_ts is not None else None) if t]
    if not candidate_timestamps:
        return False

    fresh_timestamps = []
    for ts in candidate_timestamps:
        try:
            if abs(time.time() - int(ts)) <= 300:
                fresh_timestamps.append(ts)
        except (TypeError, ValueError):
            continue
    if not fresh_timestamps:
        return False

    canonical = json.dumps(
        _canonicalize(body_dict), sort_keys=True, ensure_ascii=False, separators=(',', ':')
    )
    simple_message_parts = (
        str(body_dict.get('session_id', '')),
        str(body_dict.get('status', '')),
        str(body_dict.get('webhook_type', '')),
    )

    for ts in fresh_timestamps:
        if hmac.compare_digest(_hmac_hex(secret, f"{ts}:{canonical}"), signature):
            return True
        simple_message = f"{ts}:{':'.join(simple_message_parts)}"
        if hmac.compare_digest(_hmac_hex(secret, simple_message), signature):
            return True

    return False


def _unwrap(item: dict, singular_key: str) -> dict:
    """
    Didit's per-feature API docs (didit-protocol/skills) show each result
    nested one level, e.g. {"request_id": ..., "id_verification": {...}}.
    Whether the aggregate GET /v3/session/{id}/decision/ endpoint keeps that
    nesting inside each id_verifications[] entry, or flattens it, wasn't
    confirmed against a live response - so this accepts either shape rather
    than assuming one.
    """
    if not item:
        return {}
    nested = item.get(singular_key)
    return nested if isinstance(nested, dict) else item


def extract_fields_from_decision(decision: dict) -> dict:
    """
    Extraction of the fields shown to the student for confirmation, from a
    Didit v3 decision payload (array-based: id_verifications[],
    face_matches[], liveness_checks[]). Field names below are confirmed from
    Didit's own per-feature schemas (didit-id-document-verification,
    didit-face-match, didit-liveness-detection skills):
      - id_verification: full_name, document_number, date_of_birth (YYYY-MM-DD)
      - face_match / liveness: status ("Approved" | "Declined" | "In Review")
    """
    result = {
        'full_name': None,
        'document_number': None,
        'date_of_birth': None,
        'face_match_result': None,
        'liveness_result': None,
    }

    id_verifications = decision.get('id_verifications') or []
    if id_verifications:
        doc = _unwrap(id_verifications[0], 'id_verification')
        full_name = doc.get('full_name')
        if not full_name:
            parts = [doc.get('first_name'), doc.get('last_name')]
            full_name = ' '.join(p for p in parts if p).strip() or None
        result['full_name'] = full_name
        result['document_number'] = doc.get('document_number')
        result['date_of_birth'] = doc.get('date_of_birth')

    face_matches = decision.get('face_matches') or []
    if face_matches:
        result['face_match_result'] = _unwrap(face_matches[0], 'face_match').get('status')

    liveness_checks = decision.get('liveness_checks') or []
    if liveness_checks:
        result['liveness_result'] = _unwrap(liveness_checks[0], 'liveness').get('status')

    return result
