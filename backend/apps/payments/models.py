import uuid
from decimal import Decimal
from django.db import models
from apps.core.models import TenantAwareModel

class PaymentMethodOption(models.TextChoices):
    KARTA_JA = 'Karta J.A', 'Karta J.A'
    KARTA_ABDULAZIZ = 'Karta Abdulaziz', 'Karta Abdulaziz'
    NAQD = 'Naqd', 'Naqd'
    KARTA_MA = 'Karta M.A', 'Karta M.A'
    BANK = 'Bank', 'Bank'
    DISCOUNT = 'Discount', 'Discount'
    WITHDRAWAL = 'Withdrawal', 'Withdrawal'


class Payment(TenantAwareModel):
    """
    Financial Payment / Ledger record.
    Positive amount for payments and discounts.
    Negative amount for withdrawals.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        db_index=True
    )
    # Stored student name snapshot for audit history if student is ever detached
    student_name = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, db_index=True)
    method = models.CharField(max_length=100, db_index=True)
    received_by = models.CharField(max_length=100, db_index=True)
    notes = models.TextField(blank=True, null=True)
    is_discount = models.BooleanField(default=False, db_index=True)
    is_withdrawal = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = 'crm_payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['tenant', 'method']),
            models.Index(fields=['tenant', 'received_by']),
        ]

    def __str__(self):
        sign = "-" if self.is_withdrawal else "+"
        return f"{self.method}: {sign}{self.amount} UZS ({self.student_id or 'General'})"


class PaymentMethodTemplate(TenantAwareModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'crm_payment_method_templates'
        unique_together = ('tenant', 'name')
        ordering = ['name']


class PaymentReceiverTemplate(TenantAwareModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'crm_payment_receiver_templates'
        unique_together = ('tenant', 'name')
        ordering = ['name']


class PaymentNotePill(TenantAwareModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'crm_payment_note_pills'
        unique_together = ('tenant', 'name')
        ordering = ['name']
