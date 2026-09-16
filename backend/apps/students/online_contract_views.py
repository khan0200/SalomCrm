import hashlib
import json
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.throttling import AnonRateThrottle

from apps.authentication.models import User, UserRole
from apps.authentication.serializers import CustomTokenObtainPairSerializer
from apps.tenants.models import Tenant, Branch
from apps.core.email_service import generate_numeric_otp, send_otp_email
from .models import (
    StudentProfile,
    EmailVerificationCode,
    Contract,
    ContractAuditEvent,
    TariffOption,
    EducationLevelOption,
    Student,
)


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


class TenantInfoView(APIView):
    """
    Public endpoint: GET /api/contracts/online/tenant-info/<slug>/
    Loads tenant branding, active tariffs, offices, and education levels.
    Enforces multi-tenant data isolation.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        tenant = Tenant.objects.filter(slug=slug).first()
        if not tenant:
            return Response(
                {'detail': 'Consulting company not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not tenant.is_active:
            return Response(
                {
                    'active': False,
                    'name': tenant.name,
                    'slug': tenant.slug,
                    'detail': 'Online contracts are currently unavailable for this consulting company.'
                },
                status=status.HTTP_200_OK
            )

        # Load available tariffs for this tenant. Inactive tariffs (new ones
        # whose contract text isn't ready yet, or ones staff paused) are
        # never shown on the public signing portal.
        tariffs = TariffOption.objects.filter(tenant=tenant, is_active=True).values(
            'id', 'name', 'price', 'contract_text'
        )

        # Load offices / branches
        offices = Branch.objects.filter(tenant=tenant).values('id', 'name', 'icon')

        # Load education levels
        education_levels = EducationLevelOption.objects.filter(tenant=tenant).values('id', 'name')

        return Response({
            'active': True,
            'id': str(tenant.id),
            'name': tenant.name,
            'slug': tenant.slug,
            'logo_url': tenant.logo_url,
            'branding_color': tenant.branding_color or '#2563eb',
            'description': tenant.description or '',
            'tariffs': list(tariffs),
            'offices': list(offices),
            'education_levels': list(education_levels),
        }, status=status.HTTP_200_OK)


class SendOtpView(APIView):
    """
    Public endpoint: POST /api/contracts/online/send-otp/
    Sends single-use 6-digit OTP to student's email with rate-limiting and hashing.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, tenant_slug=None):
        email = (request.data.get('email') or '').strip().lower()
        tenant_slug = tenant_slug or (request.data.get('tenant_slug') or '').strip()

        if not email or '@' not in email:
            return Response({'detail': 'Valid email address is required.'}, status=status.HTTP_400_BAD_REQUEST)

        tenant = Tenant.objects.filter(slug=tenant_slug, is_active=True).first()
        if not tenant:
            return Response({'detail': 'Tenant not found or inactive.'}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        ten_mins_ago = now - timedelta(minutes=10)

        # Rate-limiting: max 4 OTP requests per email in 10 minutes
        recent_count = EmailVerificationCode.objects.filter(
            email=email,
            tenant=tenant,
            created_at__gte=ten_mins_ago
        ).count()
        if recent_count >= 4:
            return Response(
                {'detail': 'Too many verification code requests. Please wait a few minutes before trying again.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Invalidate existing unused codes for this email
        EmailVerificationCode.objects.filter(
            email=email,
            tenant=tenant,
            is_used=False
        ).update(is_used=True)

        otp_code = generate_numeric_otp(6)
        code_hash = hashlib.sha256(otp_code.encode()).hexdigest()
        expires_at = now + timedelta(minutes=10)

        EmailVerificationCode.objects.create(
            email=email,
            tenant=tenant,
            code_hash=code_hash,
            expires_at=expires_at,
            ip_address=get_client_ip(request)
        )

        send_otp_email(email, otp_code, tenant.name)

        return Response({
            'detail': 'Verification code sent to your email.',
            'expires_in_seconds': 600
        }, status=status.HTTP_200_OK)


class StudentSignUpView(APIView):
    """
    Public endpoint: POST /api/contracts/online/sign-up/
    Verifies Email OTP, creates online student User account, and returns JWT tokens.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, tenant_slug=None):
        email = (request.data.get('email') or '').strip().lower()
        password = (request.data.get('password') or '').strip()
        code = (request.data.get('code') or request.data.get('otp') or '').strip()
        tenant_slug = tenant_slug or (request.data.get('tenant_slug') or '').strip()

        if not email or not password or not code or not tenant_slug:
            return Response({'detail': 'Email, password, verification code, and tenant are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if len(password) < 6:
            return Response({'detail': 'Password must be at least 6 characters long.'}, status=status.HTTP_400_BAD_REQUEST)

        tenant = Tenant.objects.filter(slug=tenant_slug, is_active=True).first()
        if not tenant:
            return Response({'detail': 'Tenant not found or inactive.'}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        active_code = EmailVerificationCode.objects.filter(
            email=email,
            tenant=tenant,
            is_used=False,
            expires_at__gt=now
        ).order_by('-created_at').first()

        if not active_code:
            return Response({'detail': 'Verification code has expired or does not exist. Please request a new code.'}, status=status.HTTP_400_BAD_REQUEST)

        if active_code.attempts >= 5:
            active_code.is_used = True
            active_code.save(update_fields=['is_used'])
            return Response({'detail': 'Too many failed attempts. Please request a new verification code.'}, status=status.HTTP_400_BAD_REQUEST)

        input_hash = hashlib.sha256(code.encode()).hexdigest()
        if input_hash != active_code.code_hash:
            active_code.attempts += 1
            active_code.save(update_fields=['attempts'])
            return Response({'detail': 'Incorrect verification code.'}, status=status.HTTP_400_BAD_REQUEST)

        # Mark OTP as successfully used
        active_code.is_used = True
        active_code.save(update_fields=['is_used'])

        # Check existing user
        user = User.objects.filter(email=email).first()
        if user:
            if user.role != UserRole.STUDENT:
                return Response({'detail': 'An administrative account already exists with this email.'}, status=status.HTTP_400_BAD_REQUEST)
            # Update tenant and password
            user.tenant = tenant
            user.set_password(password)
            user.is_active = True
            user.save()
        else:
            full_name = email.split('@')[0].capitalize()
            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                role=UserRole.STUDENT,
                tenant=tenant,
                is_active=True
            )

        # Ensure student profile exists
        profile, _ = StudentProfile.objects.get_or_create(
            user=user,
            defaults={'tenant': tenant}
        )

        # Issue JWT tokens
        refresh = CustomTokenObtainPairSerializer.get_token(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': str(user.id),
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'tenant': {
                    'id': str(tenant.id),
                    'name': tenant.name,
                    'slug': tenant.slug,
                    'logo_url': tenant.logo_url
                }
            },
            'profile': {
                'passport_number': profile.passport_number,
                'date_of_birth': profile.date_of_birth,
                'phone1': profile.phone1,
                'phone2': profile.phone2,
                'education_level': profile.education_level,
                'office': profile.office,
            }
        }, status=status.HTTP_201_CREATED)


class StudentSignInView(APIView):
    """
    Public endpoint: POST /api/contracts/online/sign-in/
    Authenticates online student with email, password, and tenant isolation.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, tenant_slug=None):
        email = (request.data.get('email') or '').strip().lower()
        password = (request.data.get('password') or '').strip()
        tenant_slug = tenant_slug or (request.data.get('tenant_slug') or '').strip()

        if not email or not password:
            return Response({'detail': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        tenant = Tenant.objects.filter(slug=tenant_slug, is_active=True).first() if tenant_slug else None

        user = User.objects.filter(email=email).first()
        if not user or not user.check_password(password):
            return Response({'detail': 'Incorrect email or password.'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({'detail': 'Your account is currently disabled.'}, status=status.HTTP_403_FORBIDDEN)

        # Verify tenant match for students
        if user.role == UserRole.STUDENT and tenant and user.tenant != tenant:
            return Response({'detail': f'This account belongs to another consulting company.'}, status=status.HTTP_403_FORBIDDEN)

        profile = StudentProfile.objects.filter(user=user).first()
        refresh = CustomTokenObtainPairSerializer.get_token(user)

        target_tenant = user.tenant or tenant

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': str(user.id),
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'tenant': {
                    'id': str(target_tenant.id),
                    'name': target_tenant.name,
                    'slug': target_tenant.slug,
                    'logo_url': target_tenant.logo_url
                } if target_tenant else None
            },
            'profile': {
                'passport_number': profile.passport_number if profile else '',
                'date_of_birth': profile.date_of_birth if profile else '',
                'phone1': profile.phone1 if profile else '',
                'phone2': profile.phone2 if profile else '',
                'education_level': profile.education_level if profile else '',
                'office': profile.office if profile else '',
            } if profile else {}
        }, status=status.HTTP_200_OK)


class StudentProfileView(APIView):
    """
    Authenticated endpoint: GET & PATCH /api/contracts/online/profile/
    Returns student profile information and list of online contracts with statuses.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        tenant = user.tenant
        profile, _ = StudentProfile.objects.get_or_create(user=user, defaults={'tenant': tenant})

        # Load all contracts belonging to this student account
        contracts = Contract.objects.filter(
            student_account=user,
            is_deleted=False
        ).order_by('-created_at')

        contracts_data = []
        for c in contracts:
            contracts_data.append({
                'id': str(c.id),
                'contract_number': c.contract_number,
                'title': c.title,
                'status': c.status,
                'tariff_name': c.tariff_name,
                'tariff_price': float(c.tariff_price),
                'discount': float(c.discount or 0),
                'student_id_assigned': c.student_id_assigned,
                'created_at': c.created_at.isoformat() if c.created_at else None,
                'signed_at': c.signed_at.isoformat() if c.signed_at else None,
                'verified_at': c.verified_at.isoformat() if c.verified_at else None,
                'rejection_reason': c.rejection_reason,
                'has_verification_code': bool(c.verification_code),
                'verification_code_expires_at': c.verification_code_expires_at.isoformat() if c.verification_code_expires_at else None,
                'is_code_expired': bool(c.verification_code_expires_at and c.verification_code_expires_at < timezone.now()),
                'has_signature': bool(c.signature_data),
            })

        return Response({
            'user': {
                'id': str(user.id),
                'email': user.email,
                'full_name': user.full_name,
            },
            'profile': {
                'passport_number': profile.passport_number or '',
                'date_of_birth': profile.date_of_birth or '',
                'phone1': profile.phone1 or '',
                'phone2': profile.phone2 or '',
                'education_level': profile.education_level or '',
                'office': profile.office or '',
            },
            'contracts': contracts_data,
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        user = request.user
        profile, _ = StudentProfile.objects.get_or_create(user=user, defaults={'tenant': user.tenant})
        data = request.data

        if 'full_name' in data and data['full_name'].strip():
            user.full_name = data['full_name'].strip().upper()
            user.save(update_fields=['full_name'])

        for f in ['passport_number', 'date_of_birth', 'phone1', 'phone2', 'education_level', 'office']:
            if f in data:
                val = (data[f] or '').strip()
                if f == 'passport_number':
                    val = val.upper()
                setattr(profile, f, val)

        profile.save()
        return Response({'detail': 'Profile updated successfully.'}, status=status.HTTP_200_OK)


class SubmitContractView(APIView):
    """
    Authenticated endpoint: POST /api/contracts/online/submit-contract/
    Student submits personal information, signature, accepts declarations,
    confirms account password, and freezes an immutable snapshot.
    Status starts as PENDING. Public contract number is 'Pending Student ID'.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        data = request.data
        tenant = user.tenant

        if not tenant:
            return Response({'detail': 'No tenant associated with your account.'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Validate account password
        password = (data.get('password') or '').strip()
        if not password or not user.check_password(password):
            return Response({'detail': 'Incorrect account password.'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Retrieve Authoritative Tariff & Price from Backend (Never trust frontend price)
        tariff_id = data.get('tariff_id')
        if not tariff_id:
            return Response({'detail': 'Tariff selection is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # is_active=True here too: a tariff a student had open in their
        # browser before staff deactivated it must not still be signable.
        tariff = TariffOption.objects.filter(id=tariff_id, tenant=tenant, is_active=True).first()
        if not tariff:
            return Response({'detail': 'Selected tariff does not exist for this company.'}, status=status.HTTP_404_NOT_FOUND)

        authoritative_price = tariff.price

        # 3. Duplicate Contract Protection
        existing_active = Contract.objects.filter(
            student_account=user,
            tariff_option=tariff,
            status__in=['pending', 'verified'],
            is_deleted=False
        ).first()

        if existing_active:
            return Response(
                {'detail': 'You already have an active contract for this service.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Validate Student Information Form Fields
        passport_number = (data.get('passport_number') or '').strip().upper()
        full_name = (data.get('full_name') or '').strip().upper()
        education_level = (data.get('education_level') or '').strip()
        date_of_birth = (data.get('date_of_birth') or '').strip()
        office = (data.get('office') or data.get('office_name') or data.get('office_id') or '').strip()
        phone1 = (data.get('phone1') or '').strip()
        phone2 = (data.get('phone2') or '').strip()
        signature_data = (data.get('signature_data') or '').strip()

        if not passport_number or len(passport_number) < 6:
            return Response({'detail': 'Valid passport number is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not full_name:
            return Response({'detail': 'Full name (as in Passport) is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not education_level:
            return Response({'detail': 'Education level is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not date_of_birth:
            return Response({'detail': 'Date of birth is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not office:
            return Response({'detail': 'Tenant office is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not phone1 or not phone2:
            return Response({'detail': 'Both Mobile Phone 1 and Mobile Phone 2 are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not signature_data or not signature_data.startswith('data:image/'):
            return Response({'detail': 'A valid electronic signature is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # 5. Declarations Checkboxes
        declarations = data.get('declarations') or {}
        decl1 = declarations.get('read_full_contract') or data.get('declaration_read') or False
        decl2 = declarations.get('voluntary_sign') or data.get('declaration_will') or False
        decl3 = declarations.get('confirmation_code_meaning') or data.get('declaration_code_agreed') or False

        if not (decl1 and decl2 and decl3):
            return Response(
                {'detail': 'All three contract declarations must be confirmed before signing.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 6. Prepare Contract Content Snapshot
        base_content = tariff.contract_text or ''
        now = timezone.now()

        # Build comprehensive snapshot
        snapshot_data = {
            'tariff_id': str(tariff.id),
            'tariff_name': tariff.name,
            'price': str(authoritative_price),
            'passport_number': passport_number,
            'full_name': full_name,
            'education_level': education_level,
            'date_of_birth': date_of_birth,
            'office': office,
            'phone1': phone1,
            'phone2': phone2,
            'email': user.email,
            'tenant_name': tenant.name,
            'declarations': declarations,
            'signed_at': now.isoformat(),
        }

        # Calculate cryptographic hash (SHA-256) of document snapshot + signature
        hash_payload = json.dumps(snapshot_data, sort_keys=True) + signature_data
        contract_hash = hashlib.sha256(hash_payload.encode()).hexdigest()

        # 7. Create Contract in PENDING status
        contract = Contract.objects.create(
            tenant=tenant,
            student_account=user,
            contract_number='Pending Student ID',
            title=f"{tariff.name} Shartnomasi",
            template_name=tariff.name,
            content=base_content,
            status='pending',
            tariff_option=tariff,
            tariff_name=tariff.name,
            tariff_price=authoritative_price,
            passport_number=passport_number,
            full_name=full_name,
            education_level=education_level,
            date_of_birth=date_of_birth,
            office=office,
            phone1=phone1,
            phone2=phone2,
            signature_data=signature_data,
            declarations_accepted=True,
            agreement_confirmations=declarations,
            snapshot_data=snapshot_data,
            contract_hash=contract_hash,
            signed_at=now,
            signer_ip=get_client_ip(request),
            signer_user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        # Update student profile info
        user.full_name = full_name
        user.save(update_fields=['full_name'])

        profile, _ = StudentProfile.objects.get_or_create(user=user, defaults={'tenant': tenant})
        profile.passport_number = passport_number
        profile.date_of_birth = date_of_birth
        profile.phone1 = phone1
        profile.phone2 = phone2
        profile.education_level = education_level
        profile.office = office
        profile.save()

        # Record Audit Log
        ContractAuditEvent.objects.create(
            contract=contract,
            tenant=tenant,
            action='CONTRACT_SUBMITTED',
            actor_type='STUDENT',
            actor_id=str(user.id),
            actor_email=user.email,
            description=f"Student signed and submitted contract {contract.id} for tariff '{tariff.name}'. Status set to PENDING.",
            metadata={'price': str(authoritative_price), 'hash': contract_hash},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'detail': 'Your contract has been submitted and is waiting for agency verification.',
            'id': str(contract.id),
            'contract_id': str(contract.id),
            'contract_number': contract.contract_number,
            'status': contract.status,
            'contract_hash': contract_hash,
            'created_at': contract.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)


class VerifyContractView(APIView):
    """
    Authenticated endpoint: POST /api/contracts/online/<contract_id>/verify-code/
    Student verifies their pending contract by entering:
    1. Agency-provided Verification Code (format: XXXX-XXXX-STUDENTID)
    2. Account Password
    Validates ALL 10 rules. On success: PENDING -> VERIFIED and becomes immutable.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, contract_id):
        user = request.user
        code = normalize_code(request.data.get('code') or request.data.get('verification_code') or '')
        password = (request.data.get('password') or '').strip()

        if not code or not password:
            return Response({'detail': 'Verification code and account password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Rule 1 & 2 & 3: Student authenticated and owns contract
        contract = Contract.objects.filter(id=contract_id, student_account=user, is_deleted=False).first()
        if not contract:
            return Response({'detail': 'Contract not found or does not belong to your account.'}, status=status.HTTP_404_NOT_FOUND)

        # Rule 4: Contract status is PENDING
        if contract.status != 'pending':
            return Response({'detail': f'Contract cannot be verified in {contract.status} status.'}, status=status.HTTP_400_BAD_REQUEST)

        # Rule 5: Student ID has been assigned by Agency
        if not contract.student_id_assigned:
            return Response({'detail': 'This contract is still waiting for agency to assign Student ID.'}, status=status.HTTP_400_BAD_REQUEST)

        # Rule 6: Verification code belongs to this exact contract
        stored_code = normalize_code(contract.verification_code)
        if not stored_code:
            return Response({'detail': 'No verification code has been generated for this contract yet.'}, status=status.HTTP_400_BAD_REQUEST)

        # Rule 7: Verification code is not expired (24 hours)
        now = timezone.now()
        if contract.verification_code_expires_at and contract.verification_code_expires_at < now:
            return Response({'detail': 'This verification code has expired. Please contact the consulting company for a new code.'}, status=status.HTTP_400_BAD_REQUEST)

        # Rule 8: Verification code has not already been used
        if contract.verification_code_used:
            return Response({'detail': 'This verification code has already been used.'}, status=status.HTTP_400_BAD_REQUEST)

        # Rule 9: Verification code matches
        # Normalize both (strip hyphens and spaces for robust comparison)
        clean_input = code.replace('-', '').replace(' ', '')
        clean_stored = stored_code.replace('-', '').replace(' ', '')
        if clean_input != clean_stored:
            return Response({'detail': 'Verification code is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        # Rule 10: Student account password is correct
        if not user.check_password(password):
            return Response({'detail': 'Incorrect password.'}, status=status.HTTP_400_BAD_REQUEST)

        # ALL 10 CHECKS PASSED -> PENDING -> VERIFIED
        contract.status = 'verified'
        contract.verification_code_used = True
        contract.verified_at = now

        # Ensure CRM Student is created and linked in Students page (WITHOUT passport)
        if contract.student_id_assigned:
            from apps.students.services import normalize_date_to_iso
            crm_student = Student.objects.filter(tenant=contract.tenant, id=contract.student_id_assigned).first()
            if not crm_student:
                crm_student = Student.objects.create(
                    id=contract.student_id_assigned,
                    tenant=contract.tenant,
                    full_name=contract.full_name or f"Student {contract.student_id_assigned}",
                    phone1=contract.phone1 or '',
                    phone2=contract.phone2 or '',
                    email=user.email or '',
                    office=contract.office or '',
                    tariff=contract.tariff_name or '',
                    level=contract.education_level or '',
                    birthday=normalize_date_to_iso(contract.date_of_birth),
                    discount=contract.discount or Decimal('0.00'),
                )
            else:
                updates = []
                if contract.discount and crm_student.discount != contract.discount:
                    crm_student.discount = contract.discount
                    updates.append('discount')
                if not crm_student.birthday and contract.date_of_birth:
                    crm_student.birthday = normalize_date_to_iso(contract.date_of_birth)
                    updates.append('birthday')
                if updates:
                    crm_student.save(update_fields=updates)

            if not contract.student:
                contract.student = crm_student

            # Ensure official discount payment is recorded in payments system
            if contract.discount and contract.discount > 0:
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
                        received_by='Contract Verification',
                        notes=f"Shartnoma bo'yicha chegirma (#{contract.contract_number or contract.student_id_assigned}, ref: {contract_ref})",
                        is_discount=True,
                        user=None
                    )

        contract.save(update_fields=['status', 'verification_code_used', 'verified_at', 'updated_at', 'student'])

        # Record Audit Log
        ContractAuditEvent.objects.create(
            contract=contract,
            tenant=contract.tenant,
            action='CONTRACT_VERIFIED',
            actor_type='STUDENT',
            actor_id=str(user.id),
            actor_email=user.email,
            description=f"Contract {contract.id} (No: {contract.contract_number}) successfully VERIFIED with verification code and password.",
            metadata={'student_id': contract.student_id_assigned},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'detail': 'Contract successfully verified!',
            'status': 'verified',
            'contract_number': contract.contract_number,
            'student_id': contract.student_id_assigned,
            'verified_at': now.isoformat(),
        }, status=status.HTTP_200_OK)


class ResubmitContractView(APIView):
    """
    Authenticated endpoint: POST /api/contracts/online/<contract_id>/resubmit/
    Allows student to resubmit a previously REJECTED contract.
    Preserves audit history and transitions back to PENDING.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, contract_id):
        user = request.user
        data = request.data

        contract = Contract.objects.filter(id=contract_id, student_account=user, is_deleted=False).first()
        if not contract:
            return Response({'detail': 'Contract not found.'}, status=status.HTTP_404_NOT_FOUND)

        if contract.status != 'rejected':
            return Response({'detail': 'Only rejected contracts can be resubmitted.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate password
        password = (data.get('password') or '').strip()
        if not password or not user.check_password(password):
            return Response({'detail': 'Incorrect account password.'}, status=status.HTTP_400_BAD_REQUEST)

        # Update fields if provided
        for field in ['passport_number', 'full_name', 'education_level', 'date_of_birth', 'office', 'phone1', 'phone2']:
            if field in data and data[field]:
                val = data[field].strip()
                if field in ['passport_number', 'full_name']:
                    val = val.upper()
                setattr(contract, field, val)

        if data.get('signature_data'):
            contract.signature_data = data['signature_data'].strip()

        now = timezone.now()
        contract.status = 'pending'
        contract.rejection_reason = ''
        contract.signed_at = now
        contract.save()

        # Record audit log
        ContractAuditEvent.objects.create(
            contract=contract,
            tenant=contract.tenant,
            action='CONTRACT_RESUBMITTED',
            actor_type='STUDENT',
            actor_id=str(user.id),
            actor_email=user.email,
            description=f"Rejected contract {contract.id} was resubmitted by student. Status returned to PENDING.",
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'detail': 'Contract successfully resubmitted for review.',
            'status': 'pending',
            'contract_id': str(contract.id)
        }, status=status.HTTP_200_OK)


class LogContractViewAuditView(APIView):
    """
    Authenticated endpoint: POST /api/contracts/online/<contract_id>/audit-view/
    Logs audit event when student opens and reads the full contract.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, contract_id):
        user = request.user
        contract = Contract.objects.filter(id=contract_id, student_account=user, is_deleted=False).first()
        if not contract:
            return Response({'detail': 'Contract not found.'}, status=status.HTTP_404_NOT_FOUND)

        ContractAuditEvent.objects.create(
            contract=contract,
            tenant=contract.tenant,
            action='CONTRACT_VIEWED_FULL',
            actor_type='STUDENT',
            actor_id=str(user.id),
            actor_email=user.email,
            description=f"Student opened and read complete A4 contract document.",
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({'detail': 'Audit event recorded.'}, status=status.HTTP_200_OK)


class PublicContractDetailView(APIView):
    """
    Authenticated endpoint: GET /api/contracts/online/<contract_id>/detail/
    Returns full contract snapshot, terms, status, and verification info for student.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, contract_id):
        user = request.user
        contract = Contract.objects.filter(id=contract_id, student_account=user, is_deleted=False).first()
        if not contract:
            return Response({'detail': 'Contract not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'id': str(contract.id),
            'contract_number': contract.contract_number,
            'title': contract.title,
            'status': contract.status,
            'tariff_name': contract.tariff_name,
            'tariff_price': float(contract.tariff_price),
            'discount': float(contract.discount or 0),
            'email': user.email or (contract.snapshot_data.get('email') if contract.snapshot_data else '') or '',
            'passport_number': contract.passport_number,
            'full_name': contract.full_name,
            'education_level': contract.education_level,
            'date_of_birth': contract.date_of_birth,
            'office': contract.office,
            'phone1': contract.phone1,
            'phone2': contract.phone2,
            'signature_data': contract.signature_data,
            'content': contract.content,
            'student_id_assigned': contract.student_id_assigned,
            'has_verification_code': bool(contract.verification_code),
            'verification_code': contract.verification_code if (contract.status == 'verified' or contract.verification_code_used) else '',
            'verification_code_expires_at': contract.verification_code_expires_at.isoformat() if contract.verification_code_expires_at else None,
            'verified_at': contract.verified_at.isoformat() if contract.verified_at else None,
            'rejection_reason': contract.rejection_reason,
            'created_at': contract.created_at.isoformat() if contract.created_at else None,
            'signed_at': contract.signed_at.isoformat() if contract.signed_at else None,
            'contract_hash': contract.contract_hash,
            'tenant': {
                'id': str(contract.tenant.id),
                'name': contract.tenant.name,
                'slug': contract.tenant.slug,
                'logo_url': contract.tenant.logo_url,
            }
        }, status=status.HTTP_200_OK)


class CancelOnlineContractView(APIView):
    """
    Authenticated endpoint: POST /api/contracts/online/<contract_id>/cancel/
    Allows the student to cancel their pending or draft contract.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, contract_id):
        user = request.user
        contract = Contract.objects.filter(id=contract_id, student_account=user, is_deleted=False).first()
        if not contract:
            return Response({'detail': "Shartnoma topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        if contract.status in ['cancelled', 'rejected']:
            return Response(
                {'detail': "Shartnoma allaqachon bekor qilingan yoki rad etilgan."},
                status=status.HTTP_400_BAD_REQUEST
            )

        reason = request.data.get('reason', '').strip() or "Talaba arizani bekor qildi."

        contract.status = 'cancelled'
        contract.rejection_reason = reason
        contract.save(update_fields=['status', 'rejection_reason', 'updated_at'])

        # Record audit log
        ContractAuditEvent.objects.create(
            contract=contract,
            tenant=contract.tenant,
            action='CONTRACT_CANCELLED_BY_STUDENT',
            actor_type='STUDENT',
            actor_id=str(user.id),
            actor_email=user.email,
            description=f"Talaba shartnomani bekor qildi. Sabab: {reason}",
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'detail': "Shartnoma muvaffaqiyatli bekor qilindi.",
            'status': 'cancelled'
        }, status=status.HTTP_200_OK)


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
            'content': contract.content,
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
