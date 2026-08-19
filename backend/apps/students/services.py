from django.db import transaction
from apps.audit.services import log_audit_event

def calculate_missing_documents(student_dict):
    """
    Computes list of missing document / field tags matching Uniapp v2 validation rules.
    """
    missing = []
    
    # 1. Phone number
    phone1 = student_dict.get('phone1')
    if not phone1 or not str(phone1).strip():
        missing.append('TELEFON')

    # 2. Passport
    passport = student_dict.get('passport')
    if not passport or not str(passport).strip():
        missing.append('PASSPORT')

    # 3. Address
    address = student_dict.get('address')
    if not address or not str(address).strip():
        missing.append('MANZIL')

    # 4. Parents
    father_phone = student_dict.get('father_phone')
    mother_phone = student_dict.get('mother_phone')
    if not father_phone and not mother_phone:
        missing.append('OTA-ONA')

    # 5. Diploma / Certificate by Education Level
    level = student_dict.get('level')
    if level in ('COLLEGE', 'BACHELOR', 'LANGUAGE COURSE'):
        missing.append('DIPLOM / ATTESTAT')
    elif level in ('MASTERS', 'MASTER NO CERTIFICATE'):
        missing.append('BAKALAVR DIPLOM')

    # 6. Photos
    pic_count = student_dict.get('pic_hand_count', 0) or 0
    if pic_count < 8:
        missing.append('3x4 RASM')

    return missing


@transaction.atomic
def archive_student(student, user=None):
    """Soft-delete/archive a student."""
    student.is_deleted = True
    student.save(update_fields=['is_deleted', 'updated_at'])
    log_audit_event(
        action='STUDENT_ARCHIVED',
        entity_type='Student',
        entity_id=student.id,
        tenant=student.tenant,
        user=user,
        description=f"Student {student.id} ({student.full_name}) archived."
    )
    return student


@transaction.atomic
def restore_student(student, user=None):
    """Restore an archived student."""
    student.is_deleted = False
    student.save(update_fields=['is_deleted', 'updated_at'])
    log_audit_event(
        action='STUDENT_RESTORED',
        entity_type='Student',
        entity_id=student.id,
        tenant=student.tenant,
        user=user,
        description=f"Student {student.id} ({student.full_name}) restored."
    )
    return student


@transaction.atomic
def permanent_delete_student(student, user=None):
    """
    Permanently delete a student.
    Payments are preserved or cascaded per tenant policy.
    """
    student_id = student.id
    student_name = student.full_name
    tenant = student.tenant

    student.delete()
    log_audit_event(
        action='STUDENT_PERMANENTLY_DELETED',
        entity_type='Student',
        entity_id=student_id,
        tenant=tenant,
        user=user,
        description=f"Student {student_id} ({student_name}) permanently deleted."
    )
    return True
