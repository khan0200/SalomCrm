from django.test import TestCase
from apps.authentication.models import User
from apps.tenants.models import Tenant
from apps.students.models import Student, Folder
from apps.students.views import alphanumeric_key
from apps.students.services import calculate_missing_documents, archive_student, restore_student

class StudentsTestCase(TestCase):
    """
    Automated tests for student business rules:
    - Alphanumeric ID sorting
    - Missing document calculations
    - Soft delete / restore workflows
    """
    def setUp(self):
        self.tenant = Tenant.objects.create(id='test-tenant', name='Test Tenant', slug='test-tenant')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='pass',
            full_name='Test Manager',
            role='MANAGER',
            tenant=self.tenant
        )

    def test_alphanumeric_sorting_key(self):
        """Alphanumeric sorting correctly groups prefixes and orders numeric suffixes numerically."""
        ids = ['UB10', 'UB2', 'UB1', 'AA05', 'AA02', 'UB100', '25B12']
        sorted_ids = sorted(ids, key=alphanumeric_key)
        self.assertEqual(sorted_ids, ['25B12', 'AA02', 'AA05', 'UB1', 'UB2', 'UB10', 'UB100'])

    def test_missing_document_calculation(self):
        """Missing documents auto-computes absent required fields."""
        incomplete_student = {
            'phone1': None,
            'passport': None,
            'address': None,
            'father_phone': None,
            'mother_phone': None,
            'level': 'BACHELOR',
            'pic_hand_count': 4
        }
        missing = calculate_missing_documents(incomplete_student)
        self.assertIn('TELEFON', missing)
        self.assertIn('PASSPORT', missing)
        self.assertIn('MANZIL', missing)
        self.assertIn('OTA-ONA', missing)
        self.assertIn('DIPLOM / ATTESTAT', missing)
        self.assertIn('3x4 RASM', missing)

        complete_student = {
            'phone1': '90-123-45-67',
            'passport': 'FA1234567',
            'address': 'TASHKENT',
            'father_phone': '90-999-99-99',
            'mother_phone': '90-888-88-88',
            'level': 'BACHELOR',
            'pic_hand_count': 8
        }
        missing_complete = calculate_missing_documents(complete_student)
        self.assertNotIn('TELEFON', missing_complete)
        self.assertNotIn('PASSPORT', missing_complete)
        self.assertNotIn('MANZIL', missing_complete)
        self.assertNotIn('OTA-ONA', missing_complete)
        self.assertNotIn('3x4 RASM', missing_complete)

    def test_archive_and_restore_workflow(self):
        """Soft-archive hides student from active queries without deleting data."""
        student = Student.objects.create(
            id='UB300',
            full_name='ARCHIVE TEST STUDENT',
            tenant=self.tenant,
            created_by=self.user
        )
        self.assertFalse(student.is_deleted)

        archive_student(student, self.user)
        student.refresh_from_db()
        self.assertTrue(student.is_deleted)

        restore_student(student, self.user)
        student.refresh_from_db()
        self.assertFalse(student.is_deleted)
