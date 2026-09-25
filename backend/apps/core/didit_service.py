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


def verify_webhook_signature(body_dict: dict, signature: str, timestamp: str) -> bool:
    """
    Verifies an inbound webhook actually came from Didit. Without this,
    anyone who finds our webhook URL could POST a fake "Approved" decision
    for any session_id.

    Algorithm (per Didit's own docs): HMAC-SHA256, over
    "{timestamp}:{canonical_json_of_body}" where the canonical JSON has
    sorted keys, compact separators, and whole-number floats collapsed to
    ints - keyed by DIDIT_WEBHOOK_SECRET. A request whose timestamp is more
    than 5 minutes old is rejected even with a valid signature, to block
    replay of a captured payload.

    Returns False (never raises) when the secret isn't configured yet, or
    either header is missing/invalid - callers must treat that as "cannot
    verify", not "verified".
    """
    if not settings.DIDIT_WEBHOOK_SECRET or not signature or not timestamp:
        return False
    try:
        if abs(time.time() - int(timestamp)) > 300:
            return False
    except (TypeError, ValueError):
        return False

    canonical = json.dumps(
        _canonicalize(body_dict), sort_keys=True, ensure_ascii=False, separators=(',', ':')
    )
    message = f"{timestamp}:{canonical}"
    expected = hmac.new(
        settings.DIDIT_WEBHOOK_SECRET.encode(), message.encode('utf-8'), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


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
