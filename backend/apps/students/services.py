from typing import Any
import re
from django.db import transaction
from apps.audit.services import log_audit_event

atomic: Any = transaction.atomic

MONTH_MAP = {
    'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
    'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12,
    'YAN': 1, 'FEV': 2, 'MART': 3, 'APRIL': 4, 'MAYIS': 5, 'IYUN': 6,
    'IYUL': 7, 'AVG': 8, 'SEN': 9, 'OKT': 10, 'NOY': 11, 'DEK': 12,
    # Uzbek full month names
    'YANVAR': 1, 'FEVRAL': 2, 'MART': 3, 'APREL': 4, 'MAY': 5, 'IYUN': 6,
    'IYUL': 7, 'AVGUST': 8, 'SENTABR': 9, 'OKTABR': 10, 'NOYABR': 11, 'DEKABR': 12,
    # Russian month names
    'ЯНВАРЬ': 1, 'ФЕВРАЛЬ': 2, 'МАРТ': 3, 'АПРЕЛЬ': 4, 'МАЙ': 5, 'ИЮНЬ': 6,
    'ИЮЛЬ': 7, 'АВГУСТ': 8, 'СЕНТЯБРЬ': 9, 'ОКТЯБРЬ': 10, 'НОЯБРЬ': 11, 'ДЕКАБРЬ': 12,
    'ЯНВ': 1, 'ФЕВ': 2, 'АПР': 4, 'ИЮН': 6, 'ИЮЛ': 7, 'АВГ': 8, 'СЕН': 9, 'ОКТ': 10, 'НОЯ': 11, 'ДЕК': 12,
}


def normalize_date_to_iso(val: Any) -> str:
    """
    Normalizes any date string (DD.MM.YYYY, DD/MM/YYYY, '12 oktabr 1997', etc.)
    strictly into ISO 'YYYY-MM-DD' format.
    If already YYYY-MM-DD, returns it as-is.
    """
    if not val:
        return ''
    s = str(val).strip()
    if not s:
        return ''

    # Already ISO YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', s):
        return s

    # DD.MM.YYYY, DD/MM/YYYY, DD-MM-YYYY, DD MM YYYY
    m1 = re.match(r'^(\d{1,2})[\s\.\/\-](\d{1,2})[\s\.\/\-](\d{4})$', s)
    if m1:
        d, m, y = int(m1.group(1)), int(m1.group(2)), int(m1.group(3))
        # Protect against accidental MM/DD/YYYY if month > 12 and day <= 12
        if m > 12 and d <= 12:
            d, m = m, d
        return f"{y:04d}-{m:02d}-{d:02d}"

    # YYYY.MM.DD, YYYY/MM/DD, YYYY-MM-DD, YYYY MM DD
    m2 = re.match(r'^(\d{4})[\s\.\/\-](\d{1,2})[\s\.\/\-](\d{1,2})$', s)
    if m2:
        y, m, d = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
        return f"{y:04d}-{m:02d}-{d:02d}"

    # DD Mon YYYY e.g. "12 oktabr 1997", "12 Oct 1997", "12/OKT/1997"
    m3 = re.match(r'^(\d{1,2})[\s\.\/\-]+([A-Za-zА-Яа-яʻʼ\']+?)[\s\.\/\-]+(\d{4})$', s)
    if m3:
        d = int(m3.group(1))
        mon_str = m3.group(2).upper().replace("'", "").replace("ʻ", "").replace("ʼ", "")
        y = int(m3.group(3))
        mon = MONTH_MAP.get(mon_str) or MONTH_MAP.get(mon_str[:3])
        if mon:
            return f"{y:04d}-{mon:02d}-{d:02d}"

    # Mon DD, YYYY e.g. "October 12, 1997"
    m4 = re.match(r'^([A-Za-zА-Яа-яʻʼ\']+?)\s+(\d{1,2}),?\s+(\d{4})$', s)
    if m4:
        mon_str = m4.group(1).upper().replace("'", "").replace("ʻ", "").replace("ʼ", "")
        d = int(m4.group(2))
        y = int(m4.group(3))
        mon = MONTH_MAP.get(mon_str) or MONTH_MAP.get(mon_str[:3])
        if mon:
            return f"{y:04d}-{mon:02d}-{d:02d}"

    return s


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
