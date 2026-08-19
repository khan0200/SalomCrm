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
