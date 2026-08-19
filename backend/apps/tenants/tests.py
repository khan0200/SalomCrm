from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.authentication.models import User
from apps.tenants.models import Tenant
from apps.students.models import Student
from apps.payments.models import Payment
from apps.payments.services import record_payment

class TenantIsolationTestCase(TestCase):
    """
    Automated security tests proving complete isolation between tenants.
    """
    def setUp(self):
        self.client = APIClient()

        # 1. Tenant A (Unibridge)
        self.tenant_a = Tenant.objects.create(id='unibridge', name='Unibridge', slug='unibridge')
        self.user_a = User.objects.create_user(
            email='user_a@unibridge.com',
            password='password123',
            full_name='User Tenant A',
            role='MANAGER',
            tenant=self.tenant_a
        )
        self.student_a = Student.objects.create(
            id='UB01',
            full_name='STUDENT A',
            tenant=self.tenant_a,
            tariff='STANDART',
            created_by=self.user_a
        )
        self.payment_a = record_payment(
            tenant=self.tenant_a,
            student=self.student_a,
            amount=Decimal('5000000'),
            method='Naqd',
            received_by='ADMIN',
            user=self.user_a
        )

        # 2. Tenant B (Apex)
        self.tenant_b = Tenant.objects.create(id='apex', name='Apex Consulting', slug='apex')
        self.user_b = User.objects.create_user(
            email='user_b@apex.com',
            password='password123',
            full_name='User Tenant B',
            role='MANAGER',
            tenant=self.tenant_b
        )
        self.student_b = Student.objects.create(
            id='APEX01',
            full_name='STUDENT B',
            tenant=self.tenant_b,
            tariff='STANDART',
            created_by=self.user_b
        )
        self.payment_b = record_payment(
            tenant=self.tenant_b,
            student=self.student_b,
            amount=Decimal('3000000'),
            method='Bank',
            received_by='ADMIN',
            user=self.user_b
        )

        # 3. Platform Super Admin
        self.super_admin = User.objects.create_superuser(
            email='super@uniapp.com',
            password='password123',
            full_name='Super Admin'
        )

    def test_tenant_a_cannot_see_tenant_b_students(self):
        """Tenant A listing students must never return Tenant B students."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/students/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in response.data['results']]
        self.assertIn('UB01', ids)
        self.assertNotIn('APEX01', ids)

    def test_tenant_a_cannot_access_tenant_b_student_detail(self):
        """Tenant A requesting Tenant B student by ID must receive 404."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(f'/api/students/{self.student_b.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_tenant_a_cannot_modify_tenant_b_student(self):
        """Tenant A attempting to patch Tenant B student must receive 404."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.patch(f'/api/students/{self.student_b.id}/', {'full_name': 'HACKED NAME'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.student_b.refresh_from_db()
        self.assertEqual(self.student_b.full_name, 'STUDENT B')

    def test_tenant_a_cannot_see_tenant_b_payments(self):
        """Tenant A listing payments must never return Tenant B payments."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/payments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payment_ids = [str(p['id']) for p in response.data['results']]
        self.assertIn(str(self.payment_a.id), payment_ids)
        self.assertNotIn(str(self.payment_b.id), payment_ids)

    def test_tenant_a_cannot_see_tenant_b_users(self):
        """Tenant A listing users must only see users of Tenant A."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = [u['email'] for u in response.data['results']]
        self.assertIn('user_a@unibridge.com', emails)
        self.assertNotIn('user_b@apex.com', emails)

    def test_super_admin_can_access_all_tenants(self):
        """Platform Super Admin can view all students and switch tenant contexts."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/students/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in response.data['results']]
        self.assertIn('UB01', ids)
        self.assertIn('APEX01', ids)
