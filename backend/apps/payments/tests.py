from decimal import Decimal
from django.test import TestCase
from apps.authentication.models import User
from apps.tenants.models import Tenant
from apps.students.models import Student
from apps.payments.models import Payment
from apps.payments.services import (
    record_payment, edit_payment, delete_payment,
    recalculate_student_financials, get_tariff_price
)

class FinancialIntegrityTestCase(TestCase):
    """
    Automated tests verifying ledger-based balance calculations,
    discounts, withdrawals, and tariff pricing.
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
        # Student with PREMIUM Tariff = 32,500,000 UZS
        self.student = Student.objects.create(
            id='UB200',
            full_name='FINANCIAL TEST STUDENT',
            tenant=self.tenant,
            tariff='PREMIUM',
            language_certificate='TOPIK',
            certificate_score='LEVEL 3',
            created_by=self.user
        )

    def test_initial_balance_is_negative_tariff_price(self):
        """Initial recalculation with no payments gives negative tariff price (full debt)."""
        recalculate_student_financials(self.student)
        self.student.refresh_from_db()
        self.assertEqual(self.student.balance, Decimal('-32500000.00'))
        self.assertEqual(self.student.discount, Decimal('0.00'))

    def test_payment_and_discount_calculation(self):
        """
        Tariff: 32.5M
        Payment: 20M
        Discount: 2.5M
        Expected Balance: (20M + 2.5M) - 32.5M = -10,000,000 UZS
        """
        record_payment(
            tenant=self.tenant,
            student=self.student,
            amount=Decimal('20000000'),
            method='Karta Abdulaziz',
            received_by='ABDULAZIZ',
            user=self.user
        )
        record_payment(
            tenant=self.tenant,
            student=self.student,
            amount=Decimal('2500000'),
            method='Discount',
            received_by='ADMIN',
            is_discount=True,
            user=self.user
        )
        self.student.refresh_from_db()
        self.assertEqual(self.student.balance, Decimal('-10000000.00'))
        self.assertEqual(self.student.discount, Decimal('2500000.00'))

    def test_full_payment_brings_balance_to_zero(self):
        """Paying remaining debt brings balance to exactly 0."""
        # 1. Pay 32,500,000
        record_payment(
            tenant=self.tenant,
            student=self.student,
            amount=Decimal('32500000'),
            method='Bank',
            received_by='MUSLIHIDDIN',
            user=self.user
        )
        self.student.refresh_from_db()
        self.assertEqual(self.student.balance, Decimal('0.00'))

    def test_withdrawal_increases_debt(self):
        """Withdrawal reduces net paid and increases debt."""
        p = record_payment(
            tenant=self.tenant,
            student=self.student,
            amount=Decimal('32500000'),
            method='Bank',
            received_by='MUSLIHIDDIN',
            user=self.user
        )
        # Withdraw 5M
        record_payment(
            tenant=self.tenant,
            student=self.student,
            amount=Decimal('5000000'),
            method='Withdrawal',
            received_by='System',
            is_withdrawal=True,
            user=self.user
        )
        self.student.refresh_from_db()
        # Balance was 0, now -5,000,000
        self.assertEqual(self.student.balance, Decimal('-5000000.00'))

    def test_payment_edit_and_delete_rollbacks(self):
        """Editing and deleting payments safely recalculates balance."""
        p = record_payment(
            tenant=self.tenant,
            student=self.student,
            amount=Decimal('10000000'),
            method='Naqd',
            received_by='JASUR',
            user=self.user
        )
        self.student.refresh_from_db()
        self.assertEqual(self.student.balance, Decimal('-22500000.00'))

        # Edit to 15M
        edit_payment(p, amount=Decimal('15000000'), method='Naqd', received_by='JASUR', user=self.user)
        self.student.refresh_from_db()
        self.assertEqual(self.student.balance, Decimal('-17500000.00'))

        # Delete payment
        delete_payment(p, user=self.user)
        self.student.refresh_from_db()
        self.assertEqual(self.student.balance, Decimal('-32500000.00'))

    def test_evisa_certificate_pricing_distinction(self):
        """
        E-VISA with language certificate is 16,000,000 UZS.
        E-VISA without certificate is 24,000,000 UZS.
        """
        price_with_cert = get_tariff_price('E-VISA', 'TOPIK')
        self.assertEqual(price_with_cert, Decimal('16000000'))

        price_without_cert = get_tariff_price('E-VISA', 'NO CERTIFICATE')
        self.assertEqual(price_without_cert, Decimal('24000000'))

        price_none_cert = get_tariff_price('E-VISA', None)
        self.assertEqual(price_none_cert, Decimal('24000000'))


class StudentSerializerFinancialSyncTestCase(TestCase):
    """
    Regression coverage for assigning/changing a tariff through the Student
    update API: balance must become -tariff_price immediately, not sit at 0
    until a payment happens to be recorded. External consumers (e.g. the
    Telegram bot) read balance right after this request, so the recalculation
    must be synchronous.
    """
    def setUp(self):
        self.tenant = Tenant.objects.create(id='sync-tenant', name='Sync Tenant', slug='sync-tenant')
        self.user = User.objects.create_user(
            email='sync@example.com',
            password='pass',
            full_name='Sync Manager',
            role='MANAGER',
            tenant=self.tenant
        )
        self.student = Student.objects.create(
            id='UB300',
            full_name='SYNC TEST STUDENT',
            tenant=self.tenant,
            created_by=self.user
        )

    def _serializer(self):
        from apps.students.serializers import StudentCreateUpdateSerializer
        class FakeRequest:
            def __init__(self, user):
                self.user = user
        return StudentCreateUpdateSerializer(context={'request': FakeRequest(self.user)})

    def test_assigning_tariff_immediately_sets_negative_balance(self):
        self.assertEqual(self.student.balance, Decimal('0.00'))
        updated = self._serializer().update(self.student, {'tariff': 'PREMIUM'})
        self.assertEqual(updated.balance, Decimal('-32500000.00'))

    def test_full_flow_matches_manual_ledger(self):
        """Matches the exact scenario reported: assign tariff, pay, discount, withdraw."""
        ser = self._serializer()
        student = ser.update(self.student, {'tariff': 'PREMIUM'})
        self.assertEqual(student.balance, Decimal('-32500000.00'))

        record_payment(tenant=self.tenant, student=student, amount=10000000,
                        method='Naqd', received_by='Manager', user=self.user)
        student.refresh_from_db()
        self.assertEqual(student.balance, Decimal('-22500000.00'))

        record_payment(tenant=self.tenant, student=student, amount=2000000,
                        method='Discount', received_by='Manager', is_discount=True, user=self.user)
        student.refresh_from_db()
        self.assertEqual(student.balance, Decimal('-20500000.00'))

        record_payment(tenant=self.tenant, student=student, amount=500000,
                        method='Withdrawal', received_by='Manager', is_withdrawal=True, user=self.user)
        student.refresh_from_db()
        self.assertEqual(student.balance, Decimal('-21000000.00'))

    def test_changing_tariff_recalculates_against_existing_ledger(self):
        ser = self._serializer()
        student = ser.update(self.student, {'tariff': 'PREMIUM'})
        record_payment(tenant=self.tenant, student=student, amount=10000000,
                        method='Naqd', received_by='Manager', user=self.user)
        student.refresh_from_db()

        student = ser.update(student, {'tariff': 'STANDART'})
        self.assertEqual(student.balance, Decimal('-3000000.00'))

    def test_unrelated_field_update_does_not_change_balance(self):
        ser = self._serializer()
        student = ser.update(self.student, {'tariff': 'PREMIUM'})
        record_payment(tenant=self.tenant, student=student, amount=5000000,
                        method='Naqd', received_by='Manager', user=self.user)
        student.refresh_from_db()
        balance_before = student.balance

        student = ser.update(student, {'phone1': '901234567'})
        self.assertEqual(student.balance, balance_before)

    def test_create_with_tariff_sets_negative_balance(self):
        ser = self._serializer()
        student = ser.create({
            'id': 'UB301',
            'full_name': 'SYNC CREATE STUDENT',
            'tenant': self.tenant,
            'created_by': self.user,
            'tariff': 'STANDART',
        })
        self.assertEqual(student.balance, Decimal('-13000000.00'))


class RecordPaymentCallerRefreshTestCase(TestCase):
    """
    Regression coverage for the Telegram-bot-shows-stale-balance bug:
    record_payment/edit_payment/delete_payment recalculate a SEPARATE student
    instance internally (select_for_update), so the caller's own `student`
    variable never saw the new balance unless explicitly refreshed. A bot
    notification built from that stale variable right after the call reported
    the pre-payment (or pre-deletion) balance instead of the recalculated one.
    """
    def setUp(self):
        self.tenant = Tenant.objects.create(id='refresh-tenant', name='Refresh Tenant', slug='refresh-tenant')
        self.user = User.objects.create_user(
            email='refresh@example.com',
            password='pass',
            full_name='Refresh Manager',
            role='MANAGER',
            tenant=self.tenant
        )
        self.student = Student.objects.create(
            id='UB400',
            full_name='REFRESH TEST STUDENT',
            tenant=self.tenant,
            tariff='VISA PLUS',
            created_by=self.user
        )
        recalculate_student_financials(self.student)
        self.student.refresh_from_db()

    def test_record_payment_refreshes_caller_student_reference(self):
        # VISA PLUS = 65,000,000; student starts at -65,000,000.
        self.assertEqual(self.student.balance, Decimal('-65000000.00'))

        payment = record_payment(
            tenant=self.tenant, student=self.student, amount=5000000,
            method='Karta Abdulaziz', received_by='ABDULAZIZ', user=self.user
        )
        # The caller's own `student` object (not a re-fetched copy) must
        # already reflect the recalculated balance right after the call —
        # this is exactly what a Telegram notification reads.
        self.assertEqual(self.student.balance, Decimal('-60000000.00'))
        self.assertEqual(payment.student.balance, Decimal('-60000000.00'))

    def test_edit_payment_refreshes_caller_student_reference(self):
        payment = record_payment(
            tenant=self.tenant, student=self.student, amount=5000000,
            method='Naqd', received_by='Manager', user=self.user
        )
        self.student.refresh_from_db()
        self.assertEqual(self.student.balance, Decimal('-60000000.00'))

        payment.refresh_from_db()
        edit_payment(payment, amount=10000000, method='Naqd', received_by='Manager', user=self.user)
        self.assertEqual(payment.student.balance, Decimal('-55000000.00'))

    def test_delete_payment_refreshes_caller_student_reference(self):
        payment = record_payment(
            tenant=self.tenant, student=self.student, amount=5000000,
            method='Naqd', received_by='Manager', user=self.user
        )
        self.student.refresh_from_db()
        self.assertEqual(self.student.balance, Decimal('-60000000.00'))

        student_ref = payment.student
        delete_payment(payment, user=self.user)
        # student_ref is the SAME object destroy() would pass to the
        # delete-notification; it must show the rolled-back balance.
        self.assertEqual(student_ref.balance, Decimal('-65000000.00'))
