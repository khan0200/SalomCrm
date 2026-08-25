from decimal import Decimal
from typing import Any, cast
from django.db import transaction
from django.db.models import Sum
from apps.audit.services import log_audit_event
from .models import Payment

DEFAULT_TARIFF_PRICES = {
    'STANDART': Decimal('13000000'),
    'PREMIUM': Decimal('32500000'),
    'VISA PLUS': Decimal('65000000'),
    'E-VISA (TIL SERTIFIKATISIZ)': Decimal('24000000'),
    'E-VISA (TIL SERTIFIKATLI)': Decimal('16000000'),
    'REGIONAL VISA': Decimal('24000000'),
    'ZERO RISK': Decimal('18500000'),
    'E-VISA': Decimal('24000000'),  # Default if certificate not specified
}

def get_tariff_price(tariff_name, certificate=None, tenant=None):
    """
    Computes price of a tariff in UZS.
    Handles dynamic E-VISA distinction:
    - E-VISA with language certificate -> 16,000,000 UZS
    - E-VISA without certificate -> 24,000,000 UZS
    """
    if not tariff_name or tariff_name in ('No Tariff', 'Select', 'None', ''):
        return Decimal('0')

    tariff_upper = str(tariff_name).strip().upper()

    # Dynamic E-VISA pricing rule
    if tariff_upper == 'E-VISA':
        has_cert = bool(certificate and str(certificate).strip().upper() not in ('NO CERTIFICATE', '', 'NONE'))
        return DEFAULT_TARIFF_PRICES['E-VISA (TIL SERTIFIKATLI)'] if has_cert else DEFAULT_TARIFF_PRICES['E-VISA (TIL SERTIFIKATISIZ)']

    # Look up from tenant tariff options if available
    if tenant:
        from apps.students.models import TariffOption
        t_opt = TariffOption.objects.filter(tenant=tenant, name__iexact=tariff_upper).first()
        if t_opt:
            return t_opt.price

    return DEFAULT_TARIFF_PRICES.get(tariff_upper, Decimal('0'))


def recalculate_student_financials(student):
    """
    Recalculates a student's balance and discount strictly from payment history and assigned tariff.
    Formula: Balance = (Total Payments + Total Discount) - Tariff Price - abs(Total Withdrawals)
    - Negative balance indicates remaining debt.
    - Zero balance indicates fully paid.
    - Positive balance indicates overpayment.
    """
    from apps.students.models import Student
    with cast(Any, transaction.atomic()):
        # Lock row to prevent race conditions
        student_obj = Student.objects.select_for_update().get(id=student.id)

        # 1. Calculate sum of standard payments (non-discount, non-withdrawal)
        payments_sum = student_obj.payments.filter(
            is_discount=False, is_withdrawal=False
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        # 2. Calculate sum of discounts
        discounts_sum = student_obj.payments.filter(is_discount=True).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        # 3. Calculate sum of withdrawals (stored as negative amounts, take absolute value)
        withdrawals_sum = student_obj.payments.filter(is_withdrawal=True).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        withdrawals_abs = abs(withdrawals_sum)

        # 4. Get tariff price
        tariff_price = get_tariff_price(student_obj.tariff, student_obj.language_certificate, student_obj.tenant)

        # 5. Compute balance: (Payments + Discount) - Tariff - Withdrawals
        if tariff_price > 0:
            computed_balance = (payments_sum + discounts_sum) - tariff_price - withdrawals_abs
        else:
            computed_balance = (payments_sum + discounts_sum) - withdrawals_abs

        student_obj.balance = computed_balance
        student_obj.discount = discounts_sum
        student_obj.save(update_fields=['balance', 'discount', 'updated_at'])
        return student_obj


def record_payment(tenant, student, amount, method, received_by, notes='', is_discount=False, is_withdrawal=False, user=None):
    """
    Creates a Payment record and transactional financial update.
    """
    raw_amount = Decimal(str(amount))
    final_amount = -abs(raw_amount) if is_withdrawal else abs(raw_amount)

    with cast(Any, transaction.atomic()):
        payment = Payment.objects.create(
            tenant=tenant,
            student=student,
            student_name=student.full_name if student else None,
            amount=final_amount,
            method=method,
            received_by=received_by,
            notes=notes,
            is_discount=is_discount,
            is_withdrawal=is_withdrawal,
            created_by=user
        )

        if student:
            # recalculate_student_financials fetches and saves a SEPARATE
            # instance (select_for_update), so the caller's `student` object
            # never sees the new balance in memory unless we refresh it here.
            # Without this, a Telegram notification built right after this
            # call (or from payment.student) reports the pre-recalculation
            # balance, since Django does not mutate `student` in place.
            updated_student = recalculate_student_financials(student)
            student.balance = updated_student.balance
            student.discount = updated_student.discount
            payment.student = student

        action_name = 'DISCOUNT_RECORDED' if is_discount else ('WITHDRAWAL_RECORDED' if is_withdrawal else 'PAYMENT_RECORDED')
        log_audit_event(
            action=action_name,
            entity_type='Payment',
            entity_id=payment.id,
            tenant=tenant,
            user=user,
            description=f"{action_name}: {final_amount} UZS ({method}) for student {student.id if student else 'General'}",
            changes={'amount': str(final_amount), 'method': method, 'received_by': received_by}
        )

        return payment


def edit_payment(payment, amount, method, received_by, notes=None, user=None):
    """Edits an existing payment and updates student balance."""
    raw_amount = Decimal(str(amount))
    final_amount = -abs(raw_amount) if payment.is_withdrawal else abs(raw_amount)

    with cast(Any, transaction.atomic()):
        old_amount = payment.amount
        payment.amount = final_amount
        payment.method = method
        payment.received_by = received_by
        if notes is not None:
            payment.notes = notes
        payment.save(update_fields=['amount', 'method', 'received_by', 'notes', 'updated_at'])

        if payment.student:
            updated_student = recalculate_student_financials(payment.student)
            payment.student.balance = updated_student.balance
            payment.student.discount = updated_student.discount

        log_audit_event(
            action='PAYMENT_UPDATED',
            entity_type='Payment',
            entity_id=payment.id,
            tenant=payment.tenant,
            user=user,
            description=f"Payment {payment.id} modified from {old_amount} to {final_amount} UZS.",
            changes={'old_amount': str(old_amount), 'new_amount': str(final_amount)}
        )
        return payment


def delete_payment(payment, user=None):
    """Deletes a payment and recalculates student balance."""
    payment_id = payment.id
    student = payment.student
    tenant = payment.tenant
    amount = payment.amount

    with cast(Any, transaction.atomic()):
        payment.delete()

        if student:
            updated_student = recalculate_student_financials(student)
            student.balance = updated_student.balance
            student.discount = updated_student.discount

        log_audit_event(
            action='PAYMENT_DELETED',
            entity_type='Payment',
            entity_id=payment_id,
            tenant=tenant,
            user=user,
            description=f"Payment {payment_id} ({amount} UZS) was deleted.",
            changes={'amount': str(amount)}
        )
        return True
