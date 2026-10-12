"""
Views for the public, non-staff-authenticated parts of the online
contracts system:
  - IdentityVerificationWebhookView: Didit's push-notification receiver
    for the staff-prefilled signing-link flow (contract_sign_views.py).
  - PublicVerifyContractView: the "check authenticity" lookup by
    verification code (QR code on a printed/exported contract) - fully
    unrelated to contract signing, usable by anyone holding the code.

The old self-service flow (student sign-up via email+OTP, account-based
identity verification, 9-field self-fill form) has been removed entirely
in favor of contract_sign_views.py's staff-prefilled, token-based flow.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.throttling import AnonRateThrottle

from .models import Contract

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Safely extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def normalize_code(val: str) -> str:
    """Normalize verification code: uppercase and trim."""
    if not val:
        return ''
    return val.strip().upper()


# Shared with ContractDetailSerializer (backend/apps/students/serializers.py)
# so the guardian appendix appears whether a minor's contract is downloaded
# from the public side or the internal staff Contracts admin.
from .services import get_guardian_contract_text  # noqa: E402
from apps.core import didit_service  # noqa: E402


class IdentityVerificationWebhookView(APIView):
    """
    Public endpoint: POST /api/contracts/online/verification/webhook/
    Called by Didit whenever a session's status changes. Never trusts the
    payload's own field values unless the HMAC signature (X-Signature +
    X-Timestamp, per Didit's docs) checks out against DIDIT_WEBHOOK_SECRET.

    The only caller of Didit sessions left in this codebase is the
    staff-prefilled signing-link flow (contract_sign_views.py), which tags
    its sessions' vendor_data as "contract:<uuid>" - so this view simply
    routes every verified webhook to that flow's Contract-scoped decision
    handler.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not didit_service.verify_webhook(request.data, request.headers):
            logger.warning(
                'Didit webhook signature verification failed. headers=%s body=%s',
                {k: v for k, v in request.headers.items() if k.lower().startswith('x-')},
                dict(request.data) if hasattr(request.data, 'keys') else request.data,
            )
            return Response({'detail': 'Invalid signature.'}, status=status.HTTP_401_UNAUTHORIZED)

        session_id = request.data.get('session_id')
        vendor_data = request.data.get('vendor_data')
        if not session_id:
            return Response({'detail': 'session_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not vendor_data or not isinstance(vendor_data, str) or not vendor_data.startswith('contract:'):
            logger.warning('Didit webhook with unrecognized vendor_data=%s', vendor_data)
            return Response({'detail': 'Unknown session.'}, status=status.HTTP_404_NOT_FOUND)

        contract_id = vendor_data.split(':', 1)[1]
        contract = Contract.objects.filter(id=contract_id).first()
        if not contract:
            logger.warning('Didit webhook for unknown contract vendor_data=%s', vendor_data)
            return Response({'detail': 'Unknown session.'}, status=status.HTTP_404_NOT_FOUND)

        decision = request.data.get('decision')
        if not decision:
            try:
                decision = didit_service.get_session_decision(session_id)
            except Exception:
                logger.exception('Failed to fetch Didit decision for session_id=%s', session_id)
                return Response({'detail': 'Could not fetch decision.'}, status=status.HTTP_502_BAD_GATEWAY)

        didit_status = (request.data.get('status') or (decision or {}).get('status') or '').upper()

        from .contract_sign_views import _apply_kyc_decision
        if not contract.kyc_session_id:
            contract.kyc_session_id = session_id
        _apply_kyc_decision(contract, decision, didit_status)
        return Response({'detail': 'ok'}, status=status.HTTP_200_OK)


class ContractVerifyThrottle(AnonRateThrottle):
    scope = 'contract_verify'


class PublicVerifyContractView(APIView):
    """
    Public endpoint: GET /api/contracts/public/<code>/
    Looks up a contract purely by its verification code - the same code
    printed on the paper contract and encoded in its QR - so a bank,
    embassy, or the student themself can confirm its current status
    (verified / pending / rejected / cancelled) and re-download the
    official PDF at any time.

    No authentication or ownership check by design: knowing the code IS
    the proof of access, exactly like physically holding the paper
    contract. The code space is cryptographically random (~1.1x10^12
    combinations - see generate_verification_code), so a throttle here
    guards against scripted enumeration rather than being the real
    security boundary.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ContractVerifyThrottle]

    def get(self, request, code):
        clean_code = normalize_code(code)
        contract = Contract.objects.filter(
            verification_code=clean_code,
            is_deleted=False
        ).select_related('tenant').first()

        if not contract:
            return Response(
                {'detail': "Shartnoma topilmadi. Tasdiqlash kodini tekshiring."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'status': contract.status,
            'contract_number': contract.contract_number,
            'title': contract.title,
            'tariff_name': contract.tariff_name,
            'tariff_price': float(contract.tariff_price),
            'discount': float(contract.discount or 0),
            'full_name': contract.full_name,
            'passport_number': contract.passport_number,
            'education_level': contract.education_level,
            'date_of_birth': contract.date_of_birth,
            'office': contract.office,
            'phone1': contract.phone1,
            'phone2': contract.phone2,
            'signature_data': contract.signature_data,
            'is_minor': contract.is_minor,
            'guardian_full_name': contract.guardian_full_name,
            'guardian_passport_number': contract.guardian_passport_number,
            'guardian_relation': contract.guardian_relation,
            'guardian_phone': contract.guardian_phone,
            'guardian_address': contract.guardian_address,
            'guardian_signature_data': contract.guardian_signature_data,
            'guardian_contract_text': get_guardian_contract_text(contract.tenant) if contract.is_minor else '',
            'content': contract.content,
            # Original canvas-contract JSON (unresolved {{tokens}}, each
            # page's own fixed 210x297mm sizing) - without it, downloadContractAsPdf
            # falls back to content (flattened HTML with no page sizing) and
            # produces a squashed PDF, same issue the signing-link page had.
            'canvas_source': contract.canvas_source,
            'verification_code': contract.verification_code,
            'verified_at': contract.verified_at.isoformat() if contract.verified_at else None,
            'signed_at': contract.signed_at.isoformat() if contract.signed_at else None,
            'created_at': contract.created_at.isoformat() if contract.created_at else None,
            'contract_hash': contract.contract_hash,
            'tenant': {
                'id': str(contract.tenant.id),
                'name': contract.tenant.name,
                'slug': contract.tenant.slug,
                'logo_url': contract.tenant.logo_url,
            }
        }, status=status.HTTP_200_OK)
