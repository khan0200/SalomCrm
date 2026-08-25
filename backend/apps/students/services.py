from typing import Any
from django.db import transaction
from apps.audit.services import log_audit_event

atomic: Any = transaction.atomic

def archive_student(student, user=None):
    """Soft-delete/archive a student."""
    with atomic():
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


def restore_student(student, user=None):
    """Restore an archived student."""
    with atomic():
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


def permanent_delete_student(student, user=None):
    """
    Permanently delete a student.
    Payments are preserved or cascaded per tenant policy.
    """
    with atomic():
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
