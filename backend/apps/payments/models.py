import uuid
from decimal import Decimal
from django.db import models
from apps.core.models import TenantAwareModel, SimpleTenantModel

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
    Mapped directly to 'payments' table in Supabase.
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
        db_column='student_id',
        to_field='payment_id',
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
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_created',
        db_column='created_by',
        db_index=True
    )

    class Meta:
        db_table = 'payments'
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


class PaymentMethodTemplate(SimpleTenantModel):
    """Mapped to 'payment_methods' table in Supabase."""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'payment_methods'
        ordering = ['name']

    def __str__(self):
        return self.name


class PaymentReceiverTemplate(SimpleTenantModel):
    """Mapped to 'payment_receivers' table in Supabase."""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'payment_receivers'
        ordering = ['name']

    def __str__(self):
        return self.name


class PaymentNotePill(SimpleTenantModel):
    """Mapped to 'payment_note_templates' table in Supabase."""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'payment_note_templates'
        ordering = ['name']

    def __str__(self):
        return self.name
