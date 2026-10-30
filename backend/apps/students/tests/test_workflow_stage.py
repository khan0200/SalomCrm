from django.test import TestCase
from apps.authentication.models import User
from apps.tenants.models import Tenant
from apps.students.models import Student
from apps.students.services import compute_workflow_stage


class WorkflowStageTestCase(TestCase):
    """
    Covers the 9-case Status Board Kanban acceptance checklist for
    compute_workflow_stage (apps/students/services.py). Must be kept in
    sync with the frontend's calculateStudentWorkflowStage
    (frontend/src/modules/status/utils/statusWorkflow.ts) and the backfill
    migration's frozen snapshot (migrations/0024_backfill_workflow_stage.py)
    - this test is the drift-detection mechanism for all three.
    """
    def setUp(self):
        self.tenant = Tenant.objects.create(id='wf-tenant', name='WF Tenant', slug='wf-tenant')
        self.user = User.objects.create_user(
            email='wf@example.com', password='pass',
            full_name='WF Manager', role='MANAGER', tenant=self.tenant,
        )
        self._counter = 0

    def make_student(self, **fields):
        self._counter += 1
        defaults = dict(
            id=f'WF{self._counter}', full_name='Workflow Test Student',
            tenant=self.tenant, created_by=self.user,
        )
        defaults.update(fields)
        return Student.objects.create(**defaults)

    def test_case_1_neither_university_applied_stays_student(self):
        student = self.make_student(university_1='Seoul Uni', university_1_status='Chosen')
        self.assertEqual(compute_workflow_stage(student), 'student')
        self.assertEqual(student.workflow_stage, 'student')

    def test_case_2_university_1_applied_moves_to_apply(self):
        student = self.make_student(university_1='Seoul Uni', university_1_status='Applied')
        self.assertEqual(compute_workflow_stage(student), 'apply')
        self.assertEqual(student.workflow_stage, 'apply')

    def test_case_3_university_2_applied_moves_to_apply(self):
        student = self.make_student(
            university_1='Seoul Uni', university_1_status='Not Applied',
            university_2='Busan Uni', university_2_status='Applied',
        )
        self.assertEqual(compute_workflow_stage(student), 'apply')

    def test_case_3c_university_3_to_5_applied_moves_to_apply(self):
        for slot in (3, 4, 5):
            with self.subTest(slot=slot):
                student = self.make_student(**{
                    f'university_{slot}': f'University {slot}',
                    f'university_{slot}_status': 'Applied',
                })
                self.assertEqual(compute_workflow_stage(student), 'apply')

    def test_case_3b_university_1_failed_stays_student(self):
        student = self.make_student(university_1='Seoul Uni', university_1_status='Failed')
        self.assertEqual(compute_workflow_stage(student), 'student')

    def test_failed_university_moves_after_active_universities(self):
        student = self.make_student(
            university_1='A University', university_1_status='Applied',
            university_2='B University', university_2_status='Applied',
            university_3='C University', university_3_status='Chosen',
        )

        student.university_1_status = 'Failed'
        student.save()
        student.refresh_from_db()

        self.assertEqual(student.university_1, 'B University')
        self.assertEqual(student.university_1_status, 'Applied')
        self.assertEqual(student.university_2, 'C University')
        self.assertEqual(student.university_2_status, 'Chosen')
        self.assertEqual(student.university_3, 'A University')
        self.assertEqual(student.university_3_status, 'Failed')

    def test_case_4_either_accepted_moves_to_invoice(self):
        student = self.make_student(
            university_1='Seoul Uni', university_1_status='Accepted',
            university_2='Busan Uni', university_2_status='Not Applied',
        )
        self.assertEqual(compute_workflow_stage(student), 'invoice')

    def test_case_4b_active_invoice_without_acceptance_is_invoice(self):
        student = self.make_student(invoice='TAKEN')
        self.assertEqual(compute_workflow_stage(student), 'invoice')

    def test_case_4c_not_taken_invoice_is_not_active(self):
        student = self.make_student(invoice='NOT TAKEN')
        self.assertEqual(compute_workflow_stage(student), 'student')

    def test_case_5_coa_taken_moves_to_coa(self):
        student = self.make_student(
            university_1='Seoul Uni', university_1_status='Accepted', coa='TAKEN',
        )
        self.assertEqual(compute_workflow_stage(student), 'coa')

    def test_case_5b_coa_mistake_stays_coa(self):
        student = self.make_student(
            university_1='Seoul Uni', university_1_status='Accepted', coa='MISTAKE',
        )
        self.assertEqual(compute_workflow_stage(student), 'coa')

    def test_case_5c_coa_cancelled_stays_coa(self):
        student = self.make_student(
            university_1='Seoul Uni', university_1_status='Accepted', coa='CANCELLED',
        )
        self.assertEqual(compute_workflow_stage(student), 'coa')

    def test_case_5d_coa_not_taken_moves_back_to_invoice(self):
        student = self.make_student(
            university_1='Seoul Uni', university_1_status='Accepted', coa='NOT TAKEN',
        )
        self.assertEqual(compute_workflow_stage(student), 'invoice')

    def test_case_6_visa_applied_moves_to_visa(self):
        student = self.make_student(coa='TAKEN', embassy='APPLIED')
        self.assertEqual(compute_workflow_stage(student), 'visa')

    def test_case_7_visa_approved_stays_visa(self):
        student = self.make_student(coa='TAKEN', embassy='APPROVED')
        self.assertEqual(compute_workflow_stage(student), 'visa')

    def test_case_7b_visa_rejected_stays_visa(self):
        student = self.make_student(coa='TAKEN', embassy='REJECTED')
        self.assertEqual(compute_workflow_stage(student), 'visa')

    def test_case_7c_legacy_cancelled_is_visa_equivalent_to_rejected(self):
        student = self.make_student(coa='TAKEN', embassy='CANCELLED')
        self.assertEqual(compute_workflow_stage(student), 'visa')

    def test_case_8_reversal_recalculates_without_data_loss(self):
        student = self.make_student(
            university_1='Seoul Uni', university_1_status='Accepted',
            coa='TAKEN', embassy='APPLIED',
            embassy_father_docs=['PASSPORT'], embassy_sponsor_notes='Uncle sponsors',
        )
        student.refresh_from_db()
        self.assertEqual(student.workflow_stage, 'visa')

        # Visa reverted to "Not Yet" -> back to COA, historical docs/notes intact
        student.embassy = None
        student.save()
        student.refresh_from_db()
        self.assertEqual(student.workflow_stage, 'coa')
        self.assertEqual(student.embassy_father_docs, ['PASSPORT'])
        self.assertEqual(student.embassy_sponsor_notes, 'Uncle sponsors')

        # COA un-set -> back to Invoice (university_1 still Accepted)
        student.coa = None
        student.save()
        student.refresh_from_db()
        self.assertEqual(student.workflow_stage, 'invoice')

        # Acceptance reversed, nothing else applied -> back to Student
        student.university_1_status = 'Failed'
        student.save()
        student.refresh_from_db()
        self.assertEqual(student.workflow_stage, 'student')

    def test_case_9_refresh_preserves_persisted_stage(self):
        student = self.make_student(university_1='Seoul Uni', university_1_status='Applied')
        reloaded = Student.objects.get(pk=student.pk)
        self.assertEqual(reloaded.workflow_stage, 'apply')

    def test_garbage_embassy_value_falls_back_to_student(self):
        student = self.make_student(embassy='banana')
        self.assertEqual(compute_workflow_stage(student), 'student')

    def test_quick_update_recomputes_stage_via_full_save(self):
        """
        Mirrors StatusBoardViewSet.quick_update's setattr(...) + student.save()
        pattern (no update_fields passed) - confirms the stage recomputes on
        a full save exactly as it would through that endpoint.
        """
        student = self.make_student()
        self.assertEqual(student.workflow_stage, 'student')

        student.coa = 'TAKEN'
        student.save()
        student.refresh_from_db()
        self.assertEqual(student.workflow_stage, 'coa')

    def test_partial_update_fields_save_still_recomputes_stage(self):
        """
        archive_student/restore_student call student.save(update_fields=[...])
        with a short explicit list. Student.save() must extend that list with
        'workflow_stage' itself (a pre_save signal could not do this - Django
        freezes update_fields to an immutable frozenset before pre_save
        fires) or the recomputed value would be silently dropped from the SQL
        UPDATE.
        """
        student = self.make_student(university_1='Seoul Uni', university_1_status='Applied')
        self.assertEqual(student.workflow_stage, 'apply')

        student.university_1_status = 'Accepted'
        student.save(update_fields=['university_1_status', 'updated_at'])
        student.refresh_from_db()
        self.assertEqual(student.workflow_stage, 'invoice')
