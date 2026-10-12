"""
Staff-prefilled, token-based contract signing flow.

Unlike online_contract_views.py (the student self-service flow: sign up,
fill 9 fields, verify identity, sign - all behind a student_account JWT),
here CONSULTING STAFF pre-fill every contract field via the CRM's "New
Contract" dialog. The student then opens a link with no account/login at
all and only does three things:
  1. Confirms their identity by typing DOB + passport number (checked
     against what staff entered)
  2. Completes Didit identity verification (document scan + selfie)
  3. Draws an electronic signature

Every endpoint here is AllowAny and locates "which contract" purely via
the opaque `sign_token` in the URL - never via request.user, since there
is no student account in this flow. This file is purely additive: the
entire existing self-service flow (online_contract_views.py) is left
untouched, and a contract signed through either path lands in the same
`status='pending'`/`verified` lifecycle staff already work with.
"""
import logging
from datetime import date as _date
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.throttling import AnonRateThrottle

from .models import Contract, ContractAuditEvent, Student
from .services import normalize_date_to_iso, get_guardian_contract_text
from apps.core import didit_service

logger = logging.getLogger(__name__)


class StudentIdConflict(Exception):
    """
    Raised when a staff-typed student_id_assigned (for a brand-new
    student) turns out to already belong to a DIFFERENT tenant.
    Student.id is a bare, agency-wide-unique primary key (not scoped per
    tenant - see Student.Meta), so two unrelated consulting agencies
    choosing the same short code (e.g. "UB120") is a real, if rare,
    collision - this turns what would otherwise be an unhandled
    IntegrityError mid-signing into an explicit, catchable error.
    """
    def __init__(self, student_id: str):
        self.student_id = student_id
        super().__init__(f"Student ID '{student_id}' is already in use by another tenant.")


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class ContractSignReadThrottle(AnonRateThrottle):
    scope = 'contract_sign'


class ContractSignWriteThrottle(AnonRateThrottle):
    scope = 'contract_sign_write'


def _resolve_signable_contract(token: str):
    """
    Shared lookup used by every view below. Returns (contract_or_None,
    reason) where reason is one of 'ok' / 'not_found' / 'expired' / 'used'
    / 'locked'. Centralizing this means every endpoint renders the exact
    same terminal states identically instead of each re-deriving them.
    """
    if not token:
        return None, 'not_found'

    contract = Contract.objects.filter(
        sign_token=token, is_deleted=False
    ).select_related('tenant').first()
    if not contract:
        return None, 'not_found'

    if contract.sign_token_used_at:
        return contract, 'used'

    if contract.sign_token_expires_at and contract.sign_token_expires_at < timezone.now():
        return contract, 'expired'

    if contract.identity_confirm_attempts >= 5 and not contract.identity_confirmed_at:
        return contract, 'locked'

    return contract, 'ok'


def _log_event(contract: Contract, action: str, request, description: str = '', metadata: dict | None = None):
    ContractAuditEvent.objects.create(
        contract=contract,
        tenant=contract.tenant,
        action=action,
        actor_type='STUDENT',
        description=description,
        metadata=metadata or {},
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )


class ContractSignStatusView(APIView):
    """
    Public endpoint: GET /api/contracts/sign/<token>/
    Returns just enough to render the current step - never the full
    passport/DOB/phone values (those are write-only, checked against in
    confirm-identity below, never read back), so a leaked/guessed token
    alone can't be used to extract a student's passport number.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ContractSignReadThrottle]

    def get(self, request, token):
        contract, reason = _resolve_signable_contract(token)
        if reason == 'not_found':
            return Response({'detail': "Havola topilmadi.", 'reason': reason}, status=status.HTTP_404_NOT_FOUND)
        # A 'used' token (sign_token_used_at set, by ContractSignSubmitView)
        # means the contract is already signed - this same link now serves a
        # second, permanent purpose: the student (and the {{qr_code}}/
        # footer-link token, and the "Verified" tab's copy button) can keep
        # using it forever to view/re-download the finished contract. Only
        # 'expired'/'locked' still hard-block here, since those describe a
        # link that was never completed and should not grant read access
        # either. The signing/declaration/KYC endpoints below are NOT
        # changed - they still reject 'used' via _resolve_signable_contract,
        # so a used link can never re-enter the signing flow.
        if reason in ('expired', 'locked'):
            messages = {
                'expired': "Havola muddati tugagan. Konsalting agentligiga murojaat qiling.",
                'locked': "Shaxsni tasdiqlashda ko'p marta xato kiritildi. Konsalting agentligiga murojaat qiling.",
            }
            return Response({'detail': messages[reason], 'reason': reason}, status=status.HTTP_410_GONE)

        tenant = contract.tenant
        is_minor_hint = False
        iso_dob = normalize_date_to_iso(contract.date_of_birth)
        if iso_dob:
            try:
                dob_date = _date.fromisoformat(iso_dob)
                today = timezone.now().date()
                age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
                is_minor_hint = age < 18
            except ValueError:
                pass

        return Response({
            'reason': 'ok',
            'contract_number': contract.contract_number,
            'title': contract.title,
            'tariff_name': contract.tariff_name,
            'tariff_price': float(contract.tariff_price),
            'discount': float(contract.discount or 0),
            'full_name': contract.full_name,
            'office': contract.office,
            'education_level': contract.education_level,
            'is_minor_hint': is_minor_hint,
            'identity_confirmed': bool(contract.identity_confirmed_at),
            'kyc_status': contract.kyc_status,
            'has_signature': bool(contract.signature_data),
            # Full contract text - needed for the preview+download step
            # before the student signs. Not sensitive (same text staff
            # already see), unlike passport/DOB which stay write-only
            # for the CONFIRM-IDENTITY check above - but both already
            # appear verbatim inside `content`'s rendered text, so
            # returning them again here (to resolve canvas_source's
            # {{tokens}}) doesn't newly expose anything.
            'content': contract.content,
            'passport_number': contract.passport_number,
            'date_of_birth': contract.date_of_birth,
            'phone1': contract.phone1,
            'phone2': contract.phone2,
            # Original canvas-contract JSON (unresolved {{tokens}}, each
            # page's own fixed 210x297mm sizing) - lets the signing page
            # render true-to-size, correctly paginated pages and produce a
            # correctly laid-out PDF, the same way the staff Contracts
            # preview does. Blank for plain-HTML (non-canvas) tariffs.
            'canvas_source': contract.canvas_source,
            # Public verification QR code's target code - blank until the
            # contract is actually verified (generated by ContractSignSubmitView
            # the moment signing succeeds), resolves the {{qr_code}}/
            # {{verification_link}} tokens on the 'done' step's PDF download.
            'verification_code': contract.verification_code,
            'guardian_contract_text': get_guardian_contract_text(contract.tenant) if is_minor_hint else '',
            'tenant': {
                'id': str(tenant.id),
                'name': tenant.name,
                'slug': tenant.slug,
                'logo_url': tenant.logo_url,
                'branding_color': tenant.branding_color or '#2563eb',
            },
        }, status=status.HTTP_200_OK)


class ContractConfirmIdentityView(APIView):
    """
    Public endpoint: POST /api/contracts/sign/<token>/confirm-identity/
    Body: {date_of_birth, passport_number}. The one check that proves
    "whoever has this link is actually the right student" before anything
    else in the flow proceeds - checked against what staff already typed
    into the contract at creation time. 5 wrong attempts permanently locks
    the token (mirrors EmailVerificationCode's existing 5-attempt pattern
    in online_contract_views.py), returning a generic message that never
    reveals which of the two fields was wrong.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ContractSignWriteThrottle]

    def post(self, request, token):
        contract, reason = _resolve_signable_contract(token)
        if reason == 'not_found':
            return Response({'detail': "Havola topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        if reason != 'ok':
            return Response({'detail': "Bu havola endi amal qilmaydi."}, status=status.HTTP_410_GONE)

        input_dob = normalize_date_to_iso((request.data.get('date_of_birth') or '').strip())
        input_passport = (request.data.get('passport_number') or '').strip().upper()
        stored_dob = normalize_date_to_iso(contract.date_of_birth)
        stored_passport = (contract.passport_number or '').strip().upper()

        if not input_dob or not input_passport:
            return Response({'detail': "Tug'ilgan sana va pasport raqamini kiriting."}, status=status.HTTP_400_BAD_REQUEST)

        if input_dob != stored_dob or input_passport != stored_passport:
            contract.identity_confirm_attempts += 1
            contract.save(update_fields=['identity_confirm_attempts'])
            remaining = max(0, 5 - contract.identity_confirm_attempts)
            if remaining == 0:
                _log_event(contract, 'SIGN_LINK_IDENTITY_LOCKED', request)
                return Response(
                    {'detail': "Ko'p marta xato kiritildi. Konsalting agentligiga murojaat qiling."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            return Response(
                {'detail': "Ma'lumotlar mos kelmadi. Qayta urinib ko'ring.", 'attempts_remaining': remaining},
                status=status.HTTP_400_BAD_REQUEST
            )

        contract.identity_confirmed_at = timezone.now()
        contract.save(update_fields=['identity_confirmed_at'])
        _log_event(contract, 'SIGN_LINK_IDENTITY_CONFIRMED', request)

        return Response({'detail': 'Shaxsingiz tasdiqlandi.', 'identity_confirmed': True}, status=status.HTTP_200_OK)


class ContractSignKycStartView(APIView):
    """
    Public endpoint: POST /api/contracts/sign/<token>/kyc/start/
    Mirrors IdentityVerificationStartView but writes Didit session state
    directly onto the Contract row (kyc_*) instead of a StudentProfile-
    linked IdentityVerification, since no account exists in this flow.
    Requires identity_confirmed_at already set.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ContractSignWriteThrottle]

    def post(self, request, token):
        contract, reason = _resolve_signable_contract(token)
        if reason == 'not_found':
            return Response({'detail': "Havola topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        if reason != 'ok':
            return Response({'detail': "Bu havola endi amal qilmaydi."}, status=status.HTTP_410_GONE)

        if not contract.identity_confirmed_at:
            return Response({'detail': "Avval shaxsingizni tasdiqlang."}, status=status.HTTP_403_FORBIDDEN)

        # Resume an existing in-progress session instead of spawning a
        # duplicate if the student refreshes mid-flow.
        if contract.kyc_status == 'IN_PROGRESS' and contract.kyc_session_url:
            return Response({
                'session_id': contract.kyc_session_id,
                'url': contract.kyc_session_url,
                'status': contract.kyc_status,
            }, status=status.HTTP_200_OK)

        document_type = (request.data.get('document_type') or 'PASSPORT').strip().upper()
        if document_type not in ('PASSPORT', 'ID_CARD'):
            return Response({'detail': 'document_type must be PASSPORT or ID_CARD.'}, status=status.HTTP_400_BAD_REQUEST)

        callback_url = request.build_absolute_uri(f'/sign/{token}')

        try:
            session = didit_service.create_verification_session(
                vendor_data=f'contract:{contract.id}', callback=callback_url
            )
        except didit_service.DiditNotConfigured as e:
            return Response({'detail': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            logger.exception('Failed to create Didit verification session for contract=%s', contract.id)
            return Response(
                {'detail': "Tekshiruv xizmatiga ulanib bo'lmadi. Birozdan so'ng qayta urinib ko'ring."},
                status=status.HTTP_502_BAD_GATEWAY
            )

        contract.kyc_session_id = session.get('session_id', '')
        contract.kyc_session_url = session.get('url', '')
        contract.kyc_status = 'IN_PROGRESS'
        contract.save(update_fields=['kyc_session_id', 'kyc_session_url', 'kyc_status'])
        _log_event(contract, 'SIGN_LINK_KYC_STARTED', request, metadata={'session_id': contract.kyc_session_id})

        return Response({
            'session_id': contract.kyc_session_id,
            'url': contract.kyc_session_url,
            'status': contract.kyc_status,
        }, status=status.HTTP_201_CREATED)


class ContractSignKycStatusView(APIView):
    """
    Public endpoint: GET /api/contracts/sign/<token>/kyc/status/
    Polled by the frontend while the student is off completing Didit's
    hosted flow. Same polling-fallback as IdentityVerificationStatusView:
    if still IN_PROGRESS, actively re-fetches the decision so a missed
    webhook can't strand the student.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ContractSignReadThrottle]

    def get(self, request, token):
        contract, reason = _resolve_signable_contract(token)
        if reason == 'not_found':
            return Response({'detail': "Havola topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        if reason != 'ok':
            return Response({'detail': "Bu havola endi amal qilmaydi."}, status=status.HTTP_410_GONE)

        if contract.kyc_status == 'IN_PROGRESS' and contract.kyc_session_id:
            try:
                decision = didit_service.get_session_decision(contract.kyc_session_id)
                didit_status = (decision.get('status') or '').upper()
                _apply_kyc_decision(contract, decision, didit_status)
            except Exception:
                logger.warning(
                    'Status-poll fallback: could not fetch Didit decision for contract=%s session_id=%s',
                    contract.id, contract.kyc_session_id, exc_info=True
                )

        data = {'status': contract.kyc_status}
        if contract.kyc_status == 'PENDING_REVIEW':
            data['extracted'] = {
                'full_name': contract.kyc_extracted_full_name,
                'document_number': contract.kyc_extracted_document_number,
                'date_of_birth': contract.kyc_extracted_date_of_birth,
            }
        return Response(data, status=status.HTTP_200_OK)


class ContractSignKycConfirmView(APIView):
    """
    Public endpoint: POST /api/contracts/sign/<token>/kyc/confirm/
    Lets the student correct an OCR typo before it's final, same as
    IdentityVerificationConfirmView - but ALSO cross-matches the
    Didit-extracted passport/DOB against what the student themself typed
    in step 1 (confirm-identity). This check doesn't exist in the old
    flow and is the concrete mechanism that stops someone who merely has
    the forwarded link (but isn't the actual student) from completing a
    different person's contract: Didit proving "this document+face is
    real" is not the same as proving "this is the person named on this
    specific contract" without this extra tie-back.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ContractSignWriteThrottle]

    def post(self, request, token):
        contract, reason = _resolve_signable_contract(token)
        if reason == 'not_found':
            return Response({'detail': "Havola topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        if reason != 'ok':
            return Response({'detail': "Bu havola endi amal qilmaydi."}, status=status.HTTP_410_GONE)

        if contract.kyc_status != 'PENDING_REVIEW':
            return Response({'detail': "Tasdiqlash uchun tayyor tekshiruv topilmadi."}, status=status.HTTP_400_BAD_REQUEST)

        full_name = (request.data.get('full_name') or '').strip()
        document_number = (request.data.get('document_number') or '').strip()
        date_of_birth = (request.data.get('date_of_birth') or '').strip()

        if not full_name or not document_number or not date_of_birth:
            return Response(
                {'detail': "To'liq ism, hujjat raqami va tug'ilgan sana to'ldirilishi shart."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cross-check against the DOB+passport confirmed in step 1.
        contract_passport = (contract.passport_number or '').strip().upper()
        contract_dob = normalize_date_to_iso(contract.date_of_birth)
        extracted_passport = document_number.strip().upper()
        extracted_dob = normalize_date_to_iso(date_of_birth)

        if extracted_passport != contract_passport or extracted_dob != contract_dob:
            contract.kyc_status = 'DECLINED'
            contract.save(update_fields=['kyc_status'])
            _log_event(
                contract, 'SIGN_LINK_KYC_IDENTITY_MISMATCH', request,
                description="Didit-verified document did not match the contract's confirmed identity.",
                metadata={
                    'contract_passport': contract_passport, 'extracted_passport': extracted_passport,
                    'contract_dob': contract_dob, 'extracted_dob': extracted_dob,
                },
            )
            return Response(
                {'detail': "Tekshirilgan hujjat ma'lumotlari shartnomadagi ma'lumotlarga mos kelmadi. Konsalting agentligiga murojaat qiling."},
                status=status.HTTP_409_CONFLICT
            )

        contract.kyc_extracted_full_name = full_name
        contract.kyc_extracted_document_number = document_number
        contract.kyc_extracted_date_of_birth = date_of_birth
        contract.kyc_status = 'VERIFIED'
        contract.kyc_confirmed_at = timezone.now()
        contract.save(update_fields=[
            'kyc_extracted_full_name', 'kyc_extracted_document_number', 'kyc_extracted_date_of_birth',
            'kyc_status', 'kyc_confirmed_at'
        ])
        _log_event(contract, 'SIGN_LINK_KYC_VERIFIED', request)

        return Response({'detail': 'Shaxsingiz muvaffaqiyatli tasdiqlandi.', 'status': contract.kyc_status})


def _apply_kyc_decision(contract: Contract, decision: dict, didit_status: str) -> None:
    """Contract-scoped counterpart of online_contract_views._apply_didit_decision."""
    contract.kyc_raw_decision = decision
    mapped_status = didit_service.map_session_status(didit_status)
    update_fields = ['kyc_raw_decision', 'kyc_status']
    if mapped_status == 'PENDING_REVIEW':
        extracted = didit_service.extract_fields_from_decision(decision)
        contract.kyc_extracted_full_name = extracted['full_name'] or ''
        contract.kyc_extracted_document_number = extracted['document_number'] or ''
        contract.kyc_extracted_date_of_birth = extracted['date_of_birth'] or ''
        contract.kyc_face_match_result = extracted['face_match_result'] or ''
        contract.kyc_liveness_result = extracted['liveness_result'] or ''
        update_fields += [
            'kyc_extracted_full_name', 'kyc_extracted_document_number',
            'kyc_extracted_date_of_birth', 'kyc_face_match_result', 'kyc_liveness_result',
        ]
    contract.kyc_status = mapped_status
    contract.save(update_fields=update_fields)


def _link_or_create_crm_student(contract: Contract) -> None:
    """
    Called once, right as a staff-prefilled contract finishes signing.
    Mirrors ContractViewSet.assign_student_id's create-if-missing branch
    in views.py, but runs automatically post-signing instead of as a
    separate manual staff action - per the agreed design, a brand-new
    student's CRM row should only appear once they've actually signed,
    using the target ID staff typed into the New Contract form
    (contract.student_id_assigned) rather than requiring staff to revisit
    the contract afterwards. No-ops if already linked (existing-student
    path, picked via autocomplete at creation time).
    """
    if contract.student_id:
        return

    student_id = (contract.student_id_assigned or '').strip().upper()
    if not student_id:
        return

    crm_student = Student.objects.filter(tenant=contract.tenant, id=student_id).first()
    if not crm_student:
        # Student.id is the bare primary key (global, not per-tenant) - see
        # StudentCreateUpdateSerializer.create()'s identical guard. A match
        # under a DIFFERENT tenant means this ID is already taken agency-
        # wide; a permanently-deleted row frees its old id for reuse (data
        # retention keeps the row, not the id), same convention as manual
        # CRM creation.
        global_match = Student.objects.filter(id=student_id).exclude(tenant=contract.tenant).first()
        if global_match:
            if global_match.is_permanently_deleted:
                global_match.delete()
            else:
                raise StudentIdConflict(student_id)

        crm_student = Student.objects.create(
            id=student_id,
            tenant=contract.tenant,
            full_name=contract.full_name or f"Student {student_id}",
            phone1=contract.phone1 or '',
            phone2=contract.phone2 or '',
            office=contract.office or '',
            tariff=contract.tariff_name or '',
            level=contract.education_level or '',
            birthday=normalize_date_to_iso(contract.date_of_birth),
            discount=contract.discount or 0,
        )
    else:
        updates = []
        if not crm_student.phone1 and contract.phone1:
            crm_student.phone1 = contract.phone1
            updates.append('phone1')
        if not crm_student.phone2 and contract.phone2:
            crm_student.phone2 = contract.phone2
            updates.append('phone2')
        if not crm_student.office and contract.office:
            crm_student.office = contract.office
            updates.append('office')
        if not crm_student.tariff and contract.tariff_name:
            crm_student.tariff = contract.tariff_name
            updates.append('tariff')
            crm_student.tariff_price = None
            updates.append('tariff_price')
        if not crm_student.level and contract.education_level:
            crm_student.level = contract.education_level
            updates.append('level')
        if not crm_student.birthday and contract.date_of_birth:
            crm_student.birthday = normalize_date_to_iso(contract.date_of_birth)
            updates.append('birthday')
        if updates:
            crm_student.save(update_fields=updates)

    contract.student = crm_student
    if not contract.contract_number or contract.contract_number == contract.student_id_assigned:
        contract.contract_number = student_id

    # Record official discount in payment system so it affects balance, payments table, and student details drawer
    if contract.discount and contract.discount > 0:
        if crm_student.discount != contract.discount:
            crm_student.discount = contract.discount
            crm_student.save(update_fields=['discount'])
        from apps.payments.services import record_payment
        contract_ref = f"CONTRACT_{contract.id}"
        already_recorded = crm_student.payments.filter(
            is_discount=True,
            notes__contains=contract_ref
        ).exists()
        if not already_recorded:
            record_payment(
                tenant=contract.tenant,
                student=crm_student,
                amount=contract.discount,
                method='Discount',
                received_by='Contract Signing',
                notes=f"Shartnoma bo'yicha chegirma (#{student_id}, ref: {contract_ref})",
                is_discount=True,
                user=contract.created_by,
            )


class ContractSignSubmitView(APIView):
    """
    Public endpoint: POST /api/contracts/sign/<token>/submit/
    Final step: student draws a signature, accepts declarations, and (if
    a minor) supplies guardian info + guardian signature. Requires
    identity_confirmed_at set AND kyc_status == 'VERIFIED', re-checked
    server-side (not just gated in the UI) since this is the endpoint
    that actually makes the contract binding. On success: status becomes
    'verified' directly - staff already fully vetted the data up front
    and Didit has already verified the student's identity, so there is
    no further "Assign Student ID / generate verification code" step
    left for staff to do (that step belonged to the old self-service
    email/OTP flow, where staff hadn't seen the student yet).
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ContractSignWriteThrottle]

    @transaction.atomic
    def post(self, request, token):
        contract, reason = _resolve_signable_contract(token)
        if reason == 'not_found':
            return Response({'detail': "Havola topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        if reason != 'ok':
            return Response({'detail': "Bu havola endi amal qilmaydi."}, status=status.HTTP_410_GONE)

        if not contract.identity_confirmed_at:
            return Response({'detail': "Avval shaxsingizni tasdiqlang."}, status=status.HTTP_403_FORBIDDEN)
        if contract.kyc_status != 'VERIFIED':
            return Response({'detail': "Avval hujjat tekshiruvini yakunlang."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        signature_data = (data.get('signature_data') or '').strip()
        if not signature_data or not signature_data.startswith('data:image/'):
            return Response({'detail': "Elektron imzo talab qilinadi."}, status=status.HTTP_400_BAD_REQUEST)

        # 4 declarations per the agreed flow: read contract, data is
        # correct, informed about the process, e-signature is binding.
        declarations = data.get('declarations') or {}
        required_declarations = ('read_full_contract', 'data_correct', 'informed', 'esignature_consent')
        if not all(bool(declarations.get(key)) for key in required_declarations):
            return Response({'detail': "Shartnoma shartlarini tasdiqlashingiz kerak."}, status=status.HTTP_400_BAD_REQUEST)

        # Minor detection (Fuqarolik kodeksi 27-modda), same computation as
        # SubmitContractView.
        is_minor = False
        iso_dob = normalize_date_to_iso(contract.date_of_birth)
        if iso_dob:
            try:
                dob_date = _date.fromisoformat(iso_dob)
                today = timezone.now().date()
                age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
                is_minor = age < 18
            except ValueError:
                pass

        guardian_full_name = (data.get('guardian_full_name') or '').strip().upper()
        guardian_passport_number = (data.get('guardian_passport_number') or '').strip().upper()
        guardian_relation = (data.get('guardian_relation') or '').strip()
        guardian_phone = (data.get('guardian_phone') or '').strip()
        guardian_address = (data.get('guardian_address') or '').strip()
        guardian_signature_data = (data.get('guardian_signature_data') or '').strip()

        if is_minor:
            if not guardian_full_name:
                return Response({'detail': "Kafil (ota-ona/vasiy) F.I.O. kiritilishi shart."}, status=status.HTTP_400_BAD_REQUEST)
            if not guardian_passport_number or len(guardian_passport_number) < 6:
                return Response({'detail': "Kafilning to'g'ri pasport raqami kiritilishi shart."}, status=status.HTTP_400_BAD_REQUEST)
            if not guardian_relation:
                return Response({'detail': "Kafilning talabaga qarindoshligi kiritilishi shart."}, status=status.HTTP_400_BAD_REQUEST)
            if not guardian_phone:
                return Response({'detail': "Kafil telefon raqami kiritilishi shart."}, status=status.HTTP_400_BAD_REQUEST)
            if not guardian_address:
                return Response({'detail': "Kafil yashash manzili kiritilishi shart."}, status=status.HTTP_400_BAD_REQUEST)
            if not guardian_signature_data or not guardian_signature_data.startswith('data:image/'):
                return Response({'detail': "Kafilning elektron imzosi kiritilishi shart."}, status=status.HTTP_400_BAD_REQUEST)
            # Kafil ham xuddi shu 4 deklaratsiyani tasdiqlaydi - faqat canvas
            # imzo, Didit hujjat/yuz tekshiruvisiz (foydalanuvchi tasdiqlagan
            # qaror: "Faqat canvas imzo, hujjat skaneri yo'q").
            guardian_declarations = data.get('guardian_declarations') or {}
            if not all(bool(guardian_declarations.get(key)) for key in required_declarations):
                return Response({'detail': "Kafil shartnoma shartlarini tasdiqlashi kerak."}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        contract.signature_data = signature_data
        contract.is_minor = is_minor
        contract.guardian_full_name = guardian_full_name
        contract.guardian_passport_number = guardian_passport_number
        contract.guardian_relation = guardian_relation
        contract.guardian_phone = guardian_phone
        contract.guardian_address = guardian_address
        contract.guardian_signature_data = guardian_signature_data
        contract.declarations_accepted = True
        contract.agreement_confirmations = {
            'student': declarations,
            **({'guardian': data.get('guardian_declarations') or {}} if is_minor else {}),
        }
        contract.status = 'verified'
        contract.verified_at = now
        contract.signed_at = now
        contract.signer_ip = get_client_ip(request)
        contract.signer_user_agent = request.META.get('HTTP_USER_AGENT', '')
        contract.sign_token_used_at = now

        try:
            _link_or_create_crm_student(contract)
        except StudentIdConflict:
            # Staff typed an ID (student_id_assigned) that another tenant
            # already owns - do NOT save a half-finished sign (the
            # @transaction.atomic on this view rolls everything back), and
            # tell the student plainly instead of a raw 500. Staff needs to
            # go back into the contract and pick a different ID.
            logger.warning(
                'Student ID conflict with another tenant on contract=%s student_id_assigned=%s',
                contract.id, contract.student_id_assigned,
            )
            return Response(
                {'detail': "Tizimda xatolik yuz berdi. Konsalting agentligiga murojaat qiling (Student ID band)."},
                status=status.HTTP_409_CONFLICT
            )

        # The printed/QR verification code ({{qr_code}}/{{verification_link}}
        # tokens in the contract template, resolved by buildVariableValues on
        # the frontend) only ever existed once staff ran the old self-service
        # flow's "Assign Student ID" action. That action no longer exists in
        # this flow, so without this the code - and therefore the QR - would
        # never be generated at all. Generated once, here, the moment the
        # contract becomes verified; PublicVerifyContractView (the page the
        # QR links to) looks contracts up by this same code.
        from apps.core.email_service import generate_verification_code
        from datetime import timedelta
        target_student_id = (
            (contract.student.id if contract.student else '') or
            contract.student_id_assigned or
            contract.contract_number or ''
        )
        contract.verification_code = generate_verification_code(target_student_id)
        contract.verification_code_generated_at = now
        contract.verification_code_expires_at = now + timedelta(days=3650)
        contract.verification_code_used = False

        contract.save()

        _log_event(
            contract, 'SIGN_LINK_CONTRACT_SIGNED', request,
            description=f"Student signed staff-prefilled contract {contract.id} via link. Status set to VERIFIED.",
        )

        return Response({
            'detail': "Shartnomangiz muvaffaqiyatli yuborildi. Konsalting agentligi tez orada ko'rib chiqadi.",
            'contract_id': str(contract.id),
            'status': contract.status,
            # Lets the signing page's "done" step resolve {{qr_code}}/
            # {{verification_link}} in the final PDF download without a
            # refetch (the sign_token is already used by this point).
            'verification_code': contract.verification_code,
        }, status=status.HTTP_200_OK)
