"""
Data migration: backfill workflow_stage for every existing student.

The 0023 schema migration added workflow_stage with default='student', so
every pre-existing row currently reads 'student' regardless of its real
pipeline position. This migration recomputes the correct stage for each row
from its existing university/invoice/coa/embassy fields using a frozen
snapshot of the priority algorithm.

KEEP IN SYNC (manually - Django migrations must never import live app code,
since that code can change shape after this migration is written and
permanently break `manage.py migrate` on a fresh clone) with:
  - apps.students.services.compute_workflow_stage (the live, production-facing version)
  - frontend/src/modules/status/utils/statusWorkflow.ts: calculateStudentWorkflowStage
Priority order: VISA > COA > INVOICE > APPLY > STUDENT, first match wins.
Covered by backend/apps/students/tests/test_workflow_stage.py.
"""
from django.db import migrations

BATCH_SIZE = 2000
WORKFLOW_VISA_VALUES = {'APPLIED', 'APPROVED', 'REJECTED', 'CANCELLED'}


def _compute_stage(embassy, coa, invoice, uni_statuses):
    visa_status = (embassy or '').strip().upper()
    if visa_status in WORKFLOW_VISA_VALUES:
        return 'visa'

    if (coa or '').strip().upper() == 'TAKEN':
        return 'coa'

    is_any_uni_accepted = any((s or '').strip().upper() == 'ACCEPTED' for s in uni_statuses)
    invoice_val = (invoice or '').strip().upper()
    has_active_invoice = bool(invoice_val and invoice_val != 'NOT TAKEN')
    if is_any_uni_accepted or has_active_invoice:
        return 'invoice'

    is_any_uni_applied = any((s or '').strip().upper() == 'APPLIED' for s in uni_statuses[:2])
    if is_any_uni_applied:
        return 'apply'

    return 'student'


def backfill_workflow_stage(apps, schema_editor):
    Student = apps.get_model('students', 'Student')

    qs = Student.objects.all().only(
        'id', 'embassy', 'coa', 'invoice',
        'university_1_status', 'university_2_status', 'university_3_status',
        'university_4_status', 'university_5_status', 'workflow_stage',
    )

    updates = []
    total_updated = 0
    for student in qs.iterator(chunk_size=BATCH_SIZE):
        new_stage = _compute_stage(
            student.embassy, student.coa, student.invoice,
            [
                student.university_1_status, student.university_2_status,
                student.university_3_status, student.university_4_status,
                student.university_5_status,
            ],
        )
        if student.workflow_stage != new_stage:
            student.workflow_stage = new_stage
            updates.append(student)

        if len(updates) >= BATCH_SIZE:
            Student.objects.bulk_update(updates, ['workflow_stage'])
            total_updated += len(updates)
            updates = []

    if updates:
        Student.objects.bulk_update(updates, ['workflow_stage'])
        total_updated += len(updates)

    print(f"  [OK] Backfilled workflow_stage on {total_updated} student(s).")


def reverse_backfill(apps, schema_editor):
    # Intentional no-op: resetting every student back to 'student' on
    # reverse would be destructive and wrong, since workflow_stage is meant
    # to reflect real, current data - not a value this migration "owns".
    # The true undo is removing the column itself (0023's reverse).
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0023_student_workflow_stage'),
    ]

    # Not atomic: this touches every row in a production table in batches;
    # a crash mid-run should keep already-committed batches rather than
    # holding one giant transaction open, and reruns are idempotent since
    # the computation only reads source-of-truth fields.
    atomic = False

    operations = [
        migrations.RunPython(backfill_workflow_stage, reverse_code=reverse_backfill),
    ]
