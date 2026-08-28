from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.authentication.models import User
from apps.tenants.models import Tenant
from apps.students.models import Student, Folder, LeadSourceOption
from apps.payments.models import Payment, PaymentMethodTemplate, PaymentReceiverTemplate
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

    def test_super_admin_switched_into_tenant_sees_only_that_tenant_users(self):
        """
        Regression: the Staff page leaked every tenant's users while a Super
        Admin was switched into one tenant. UserViewSet.get_queryset only
        honoured an explicit ?tenant_id= and ignored request.tenant, which is
        what TenantMiddleware sets from the X-Tenant-ID header.
        """
        self.client.force_authenticate(user=self.super_admin)

        response = self.client.get('/api/users/', HTTP_X_TENANT_ID=self.tenant_a.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = [u['email'] for u in response.data['results']]
        self.assertIn('user_a@unibridge.com', emails)
        self.assertNotIn('user_b@apex.com', emails)

        response = self.client.get('/api/users/', HTTP_X_TENANT_ID=self.tenant_b.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = [u['email'] for u in response.data['results']]
        self.assertIn('user_b@apex.com', emails)
        self.assertNotIn('user_a@unibridge.com', emails)

    def test_super_admin_without_tenant_context_sees_all_users(self):
        """Scoping by X-Tenant-ID must not break the platform-wide view."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = [u['email'] for u in response.data['results']]
        self.assertIn('user_a@unibridge.com', emails)
        self.assertIn('user_b@apex.com', emails)

    def test_tenant_a_cannot_add_tenant_b_student_to_own_folder(self):
        """
        Regression: FolderViewSet.add_students fetched students by
        `id__in=student_ids` with no tenant filter, so Tenant A could add
        Tenant B's student (guessed/known ID) into Tenant A's own folder,
        silently writing Tenant A's folder UUID into Tenant B's record.
        """
        folder_a = Folder.objects.create(tenant=self.tenant_a, name='VIP')
        self.client.force_authenticate(user=self.user_a)

        response = self.client.post(
            f'/api/folders/{folder_a.id}/add-students/',
            {'student_ids': [self.student_b.id]},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['added_count'], 0)

        self.student_b.refresh_from_db()
        curr_strs = [str(x) for x in (self.student_b.folder_ids or [])]
        self.assertNotIn(str(folder_a.id), curr_strs)

    def test_tenant_a_can_add_own_student_to_own_folder(self):
        """Sanity check: the tenant filter must not block legitimate same-tenant adds."""
        folder_a = Folder.objects.create(tenant=self.tenant_a, name='VIP')
        self.client.force_authenticate(user=self.user_a)

        response = self.client.post(
            f'/api/folders/{folder_a.id}/add-students/',
            {'student_ids': [self.student_a.id]},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['added_count'], 1)

        self.student_a.refresh_from_db()
        curr_strs = [str(x) for x in (self.student_a.folder_ids or [])]
        self.assertIn(str(folder_a.id), curr_strs)

    def test_tenant_a_cannot_see_tenant_b_lead_sources(self):
        """
        Lead sources are per-tenant with no shared defaults: what one tenant
        adds must never appear in another tenant's list.
        """
        LeadSourceOption.objects.create(tenant=self.tenant_a, name='Ali Uncle')
        lead_b = LeadSourceOption.objects.create(tenant=self.tenant_b, name='Apex Referral')

        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/lead-sources/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item['name'] for item in response.data]
        self.assertIn('Ali Uncle', names)
        self.assertNotIn('Apex Referral', names)

        # Tenant A must not be able to read, modify, or delete Tenant B's row by id.
        detail_url = f'/api/lead-sources/{lead_b.id}/'
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            self.client.patch(detail_url, {'name': 'HACKED'}).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(self.client.delete(detail_url).status_code, status.HTTP_404_NOT_FOUND)
        lead_b.refresh_from_db()
        self.assertEqual(lead_b.name, 'Apex Referral')

    def test_tenant_a_cannot_see_tenant_b_payment_methods(self):
        """Payment method templates are per-tenant with no shared defaults."""
        PaymentMethodTemplate.objects.create(tenant=self.tenant_a, name='Naqd')
        method_b = PaymentMethodTemplate.objects.create(tenant=self.tenant_b, name='Apex Card')

        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/payment-methods/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item['name'] for item in response.data]
        self.assertIn('Naqd', names)
        self.assertNotIn('Apex Card', names)

        detail_url = f'/api/payment-methods/{method_b.id}/'
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            self.client.patch(detail_url, {'name': 'HACKED'}).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(self.client.delete(detail_url).status_code, status.HTTP_404_NOT_FOUND)
        method_b.refresh_from_db()
        self.assertEqual(method_b.name, 'Apex Card')

    def test_tenant_a_cannot_see_tenant_b_payment_receivers(self):
        """Payment receiver templates are per-tenant with no shared defaults."""
        PaymentReceiverTemplate.objects.create(tenant=self.tenant_a, name='ADMIN')
        receiver_b = PaymentReceiverTemplate.objects.create(tenant=self.tenant_b, name='APEX ADMIN')

        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/payment-receivers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item['name'] for item in response.data]
        self.assertIn('ADMIN', names)
        self.assertNotIn('APEX ADMIN', names)

        detail_url = f'/api/payment-receivers/{receiver_b.id}/'
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            self.client.patch(detail_url, {'name': 'HACKED'}).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(self.client.delete(detail_url).status_code, status.HTTP_404_NOT_FOUND)
        receiver_b.refresh_from_db()
        self.assertEqual(receiver_b.name, 'APEX ADMIN')

    def test_new_tenant_starts_with_empty_lead_sources_and_payment_templates(self):
        """
        These catalogs intentionally have no seeded defaults (unlike
        universities): a brand new tenant must start completely empty so it
        never inherits another tenant's lead sources or payment templates.
        """
        self.assertEqual(LeadSourceOption.objects.filter(tenant=self.tenant_b).count(), 0)
        self.assertEqual(PaymentMethodTemplate.objects.filter(tenant=self.tenant_b).count(), 0)
        self.assertEqual(PaymentReceiverTemplate.objects.filter(tenant=self.tenant_b).count(), 0)
