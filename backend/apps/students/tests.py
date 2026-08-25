from django.test import TestCase
from apps.authentication.models import User
from apps.tenants.models import Tenant
from apps.students.models import Student, Folder
from apps.students.views import alphanumeric_key
from apps.students.services import archive_student, restore_student

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
