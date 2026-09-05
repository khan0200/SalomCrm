import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import ArrayField
from apps.core.models import TenantAwareModel, TimeStampedModel, SimpleTenantModel

class StudentLevel(models.TextChoices):
    COLLEGE = 'COLLEGE', 'College'
    BACHELOR = 'BACHELOR', 'Bachelor'
    MASTERS = 'MASTERS', 'Masters'
    MASTER_NO_CERTIFICATE = 'MASTER NO CERTIFICATE', 'Master No Certificate'
    LANGUAGE_COURSE = 'LANGUAGE COURSE', 'Language Course'


class StudentTariff(models.TextChoices):
    STANDART = 'STANDART', 'Standart'
    PREMIUM = 'PREMIUM', 'Premium'
    VISA_PLUS = 'VISA PLUS', 'Visa Plus'
    E_VISA = 'E-VISA', 'E-Visa'
    REGIONAL_VISA = 'REGIONAL VISA', 'Regional Visa'
    ZERO_RISK = 'ZERO RISK', 'Zero Risk'


class LanguageCertificate(models.TextChoices):
    TOPIK = 'TOPIK', 'TOPIK'
    IELTS = 'IELTS', 'IELTS'
    TOEFL = 'TOEFL', 'TOEFL'
    CEFR = 'CEFR', 'CEFR'
    SAT = 'SAT', 'SAT'
    SKA = 'SKA', 'SKA'
    NO_CERTIFICATE = 'NO CERTIFICATE', 'No Certificate'


class Folder(SimpleTenantModel):
    """Student folders for categorization within a tenant. Mapped to 'folders' table."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'folders'
        verbose_name = 'Student Folder'
        verbose_name_plural = 'Student Folders'
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"


class Student(TenantAwareModel):
    """
    Core Student Model in Uniapp CRM.
    Mapped directly to 'students' table in Supabase.
    Preserves all business fields, financial parameters, educational backgrounds,
    university choices, language certificates, and status board parameters.
    """
    # 1. Personal & Contact Information
    id = models.CharField(max_length=50, primary_key=True)  # Alphanumeric uppercase e.g. "UB120", "AA01"

    # Immutable payment anchor — set once at creation from id (e.g. "PF49" for student "F49").
    # NEVER updated after initial set. Payments FK points here so renaming Student.id
    # never orphans payment history.
    payment_id = models.CharField(
        max_length=55,
        unique=True,
        null=True,
        blank=True,
        editable=False,
        db_index=True,
        help_text="Immutable payment anchor. Set once on creation (P + student id). Never changes."
    )

    full_name = models.CharField(max_length=255, db_index=True)
    korean_name = models.CharField(max_length=255, blank=True, null=True)
    passport = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    passport_issue_date = models.CharField(max_length=50, blank=True, null=True)
    passport_expire_date = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)  # MALE, FEMALE
    birthday = models.CharField(max_length=50, blank=True, null=True)
    phone1 = models.CharField(max_length=50, blank=True, null=True)
    phone2 = models.CharField(max_length=50, blank=True, null=True)
    telegram_username = models.CharField(max_length=100, blank=True, null=True)
    father_name = models.CharField(max_length=255, blank=True, null=True)

    father_phone = models.CharField(max_length=50, blank=True, null=True)
    father_job = models.CharField(max_length=255, blank=True, null=True)
    mother_name = models.CharField(max_length=255, blank=True, null=True)
    mother_phone = models.CharField(max_length=50, blank=True, null=True)
    mother_job = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    # 2. Educational & Tariff Details
    level = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    level2 = models.CharField(max_length=50, blank=True, null=True)
    educational_background = models.CharField(max_length=255, blank=True, null=True)
    major = models.CharField(max_length=255, blank=True, null=True)
    final_school_name = models.CharField(max_length=255, blank=True, null=True)
    gpa = models.CharField(max_length=50, blank=True, null=True)
    gpa_system = models.CharField(max_length=50, blank=True, null=True)
    degree_no = models.CharField(max_length=100, blank=True, null=True)
    date_of_entry = models.CharField(max_length=50, blank=True, null=True)
    date_of_graduation = models.CharField(max_length=50, blank=True, null=True)
    graduation_expected = models.BooleanField(default=False)
    school_address = models.TextField(blank=True, null=True)
    school_website = models.CharField(max_length=255, blank=True, null=True)
    school_phone = models.CharField(max_length=50, blank=True, null=True)
    school_email = models.CharField(max_length=255, blank=True, null=True)
    tariff = models.CharField(max_length=50, blank=True, null=True, db_index=True)

    # 3. Language Certificates (Supports up to 3 slots)
    language_certificate = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    certificate_score = models.CharField(max_length=50, blank=True, null=True)
    certificate_test_date = models.CharField(max_length=50, blank=True, null=True)
    certificate_valid_date = models.CharField(max_length=50, blank=True, null=True)

    language_certificate_2 = models.CharField(max_length=50, blank=True, null=True)
    certificate_score_2 = models.CharField(max_length=50, blank=True, null=True)
    certificate_2_test_date = models.CharField(max_length=50, blank=True, null=True)
    certificate_2_valid_date = models.CharField(max_length=50, blank=True, null=True)

    language_certificate_3 = models.CharField(max_length=50, blank=True, null=True)
    certificate_score_3 = models.CharField(max_length=50, blank=True, null=True)
    certificate_3_test_date = models.CharField(max_length=50, blank=True, null=True)
    certificate_3_valid_date = models.CharField(max_length=50, blank=True, null=True)

    # 4. University Selections & Statuses (1 to 5)
    university_1 = models.CharField(max_length=255, blank=True, null=True)
    university_1_status = models.CharField(max_length=50, blank=True, null=True, default='Chosen')
    university_1_major = models.CharField(max_length=255, blank=True, null=True)

    university_2 = models.CharField(max_length=255, blank=True, null=True)
    university_2_status = models.CharField(max_length=50, blank=True, null=True)
    university_2_major = models.CharField(max_length=255, blank=True, null=True)

    university_3 = models.CharField(max_length=255, blank=True, null=True)
    university_3_status = models.CharField(max_length=50, blank=True, null=True)
    university_3_major = models.CharField(max_length=255, blank=True, null=True)

    university_4 = models.CharField(max_length=255, blank=True, null=True)
    university_4_status = models.CharField(max_length=50, blank=True, null=True)
    university_4_major = models.CharField(max_length=255, blank=True, null=True)

    university_5 = models.CharField(max_length=255, blank=True, null=True)
    university_5_status = models.CharField(max_length=50, blank=True, null=True)
    university_5_major = models.CharField(max_length=255, blank=True, null=True)

    # 5. Financial Parameters
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'), db_index=True)
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    # 6. Document Checklist & Counts
    pick_needed = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    has_mc = models.BooleanField(default=False)
    bc_hand_count = models.IntegerField(default=0)
    mc_hand_count = models.IntegerField(default=0)
    apos_hand_count = models.IntegerField(default=0)
    pic_hand_count = models.IntegerField(default=0)

    # 7. Status Board & Embassy Parameters
    invoice = models.CharField(max_length=50, blank=True, null=True)  # NOT TAKEN, TAKEN, NOT PAID, PAID, CANCELLED
    invoice_university = models.CharField(max_length=255, blank=True, null=True)
    coa = models.CharField(max_length=50, blank=True, null=True)      # NOT TAKEN, TAKEN, MISTAKE, CANCELLED
    embassy = models.CharField(max_length=50, blank=True, null=True)  # APPROVED, CANCELLED, PENDING
    embassy_documents = ArrayField(models.CharField(max_length=255), default=list, blank=True)
    status_hidden = models.BooleanField(default=False, db_index=True)
    kdb_put_date = models.CharField(max_length=50, blank=True, null=True)
    kdb_take_date = models.CharField(max_length=50, blank=True, null=True)
    embassy_father_docs = ArrayField(models.CharField(max_length=255), default=list, blank=True)
    embassy_mother_docs = ArrayField(models.CharField(max_length=255), default=list, blank=True)
    embassy_sponsor_notes = models.TextField(blank=True, null=True)
    status_row_color = models.CharField(max_length=50, blank=True, null=True)

    # 8. System & Management Metadata
    office = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    student_group = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    lead_by = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    coordinator = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False, db_index=True)  # Soft delete archive
    row_color = models.CharField(max_length=50, blank=True, null=True)
    task_tags = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    folder_ids = ArrayField(models.UUIDField(), default=list, blank=True)
    google_drive_url = models.URLField(max_length=500, blank=True, null=True)
    google_drive_folder_id = models.CharField(max_length=255, blank=True, null=True)
    jarayon_updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students_created',
        db_column='created_by',
        db_index=True
    )

    class Meta:
        db_table = 'students'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'id']),
            models.Index(fields=['tenant', 'full_name']),
            models.Index(fields=['tenant', 'is_deleted']),
            models.Index(fields=['tenant', 'status_hidden']),
            models.Index(fields=['tenant', 'tariff']),
            models.Index(fields=['tenant', 'balance']),
        ]

    def __str__(self):
        return f"{self.id} - {self.full_name}"

    def save(self, *args, **kwargs):
        # Enforce uppercase on alphanumeric ID, name, passport, address
        for attr in ('id', 'full_name', 'passport', 'address'):
            val = getattr(self, attr, None)
            if isinstance(val, str) and val:
                setattr(self, attr, val.strip().upper())

        # Set payment_id exactly once at creation — NEVER overwrite after that.
        # This keeps payments correctly anchored even when Student.id is renamed.
        if not self.payment_id and self.id:
            self.payment_id = f"P{self.id.strip().upper()}"

        # Auto-extract Google Drive Folder ID from URL if not explicitly provided
        if self.google_drive_url and not self.google_drive_folder_id:
            import re
            m = re.search(r'folders/([a-zA-Z0-9_-]+)', str(self.google_drive_url)) or re.search(r'id=([a-zA-Z0-9_-]+)', str(self.google_drive_url))
            if m:
                self.google_drive_folder_id = m.group(1)

        # Automatic English-to-Korean transliteration sync
        if self.full_name:
            should_translate = False
            if not self.korean_name or not self.korean_name.strip():
                should_translate = True
            elif self.pk:
                try:
                    orig = Student.objects.filter(pk=self.pk).values('full_name', 'korean_name').first()
                    # If full_name changed and korean_name was not manually updated in this save
                    if orig and orig['full_name'] != self.full_name and orig['korean_name'] == self.korean_name:
                        should_translate = True
                except Exception:
                    pass

            if should_translate:
                try:
                    from .korean_translation_service import translate_name_to_korean
                    translated = translate_name_to_korean(self.full_name)
                    if translated:
                        self.korean_name = translated
                        if kwargs.get('update_fields') is not None and 'korean_name' not in kwargs['update_fields']:
                            update_fields = list(kwargs['update_fields'])
                            update_fields.append('korean_name')
                            kwargs['update_fields'] = update_fields
                except Exception:
                    pass

        # Sequential university slot compaction (no gaps allowed: e.g. deleting Uni 1 shifts Uni 2 to Uni 1)
        unis = []
        for i in range(1, 6):
            u_name = getattr(self, f'university_{i}', None)
            if u_name and isinstance(u_name, str) and u_name.strip():
                unis.append({
                    'name': u_name.strip(),
                    'status': getattr(self, f'university_{i}_status', None) or 'Chosen',
                    'major': getattr(self, f'university_{i}_major', None) or None,
                })

        uni_fields_changed = False
        for i in range(1, 6):
            if i <= len(unis):
                new_name = unis[i - 1]['name']
                new_status = unis[i - 1]['status']
                new_major = unis[i - 1]['major']
            else:
                new_name = None
                new_status = 'Chosen' if i == 1 else None
                new_major = None

            if (getattr(self, f'university_{i}', None) != new_name or
                getattr(self, f'university_{i}_status', None) != new_status or
                getattr(self, f'university_{i}_major', None) != new_major):
                uni_fields_changed = True

            setattr(self, f'university_{i}', new_name)
            setattr(self, f'university_{i}_status', new_status)
            setattr(self, f'university_{i}_major', new_major)

        if uni_fields_changed and kwargs.get('update_fields') is not None:
            uni_fields = [f'university_{i}' for i in range(1, 6)] + \
                         [f'university_{i}_status' for i in range(1, 6)] + \
                         [f'university_{i}_major' for i in range(1, 6)]
            update_fields = set(kwargs['update_fields'])
            update_fields.update(uni_fields)
            kwargs['update_fields'] = list(update_fields)

        super().save(*args, **kwargs)


class TariffOption(SimpleTenantModel):
    """Configurable tariff options with default prices. Mapped to 'tariff_options' table."""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        db_table = 'tariff_options'
        ordering = ['name']

    def __str__(self):
        return self.name


class EducationLevelOption(SimpleTenantModel):
    """Mapped to 'education_levels' table."""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'education_levels'
        ordering = ['name']

    def __str__(self):
        return self.name


class StudentGroupOption(SimpleTenantModel):
    """Mapped to 'student_groups' table."""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'student_groups'
        ordering = ['name']

    def __str__(self):
        return self.name


class LeadSourceOption(SimpleTenantModel):
    """Mapped to 'lead_sources' table."""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'lead_sources'
        ordering = ['name']

    def __str__(self):
        return self.name


class CoordinatorOption(SimpleTenantModel):
    """Mapped to 'coordinators' table."""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'coordinators'
        ordering = ['name']

    def __str__(self):
        return self.name


class UniversityOption(models.Model):
    """
    Mapped to 'universities' table.

    Per-tenant: every tenant starts from the same default list, but each
    tenant's additions and edits are its own and never affect other tenants.
    Declares the tenant FK directly rather than extending SimpleTenantModel,
    which would switch the primary key to a UUID and orphan existing rows.
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='students_universityoption_set',
        db_column='tenant_id',
        db_index=True,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'universities'
        ordering = ['name']

    def __str__(self):
        return self.name


class UniversityStatusOption(SimpleTenantModel):
    """Mapped to 'university_statuses' table."""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    color_class = models.CharField(max_length=100, default='text-blue-500')

    class Meta:
        db_table = 'university_statuses'
        ordering = ['name']

    def __str__(self):
        return self.name


class TagOption(SimpleTenantModel):
    """Configurable custom tags with icons. Mapped to 'crm_tag_options' table."""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='🏷️')

    class Meta:
        db_table = 'crm_tag_options'
        ordering = ['name']

    def __str__(self):
        return f"{self.icon} {self.name}"


class StudentUserPreference(models.Model):
    """
    Per-user "Only Me" row color and tags for a student -- private data
    visible only to the acting user, never shared tenant-wide. Deliberately
    separate from Student.row_color/task_tags (which remain the "For All"
    shared fields, unchanged).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant', on_delete=models.CASCADE,
        related_name='student_user_preferences', db_index=True,
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE,
        related_name='user_preferences', db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='student_preferences', db_index=True,
    )
    row_color = models.CharField(max_length=50, blank=True, null=True)
    task_tags = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crm_student_user_preferences'
        constraints = [
            models.UniqueConstraint(fields=['student', 'user'], name='uniq_student_user_preference')
        ]
        indexes = [
            models.Index(fields=['tenant', 'user']),
            models.Index(fields=['student', 'user']),
        ]

    def __str__(self):
        return f"{self.student_id} / {self.user_id} preference"


class SchoolDirectory(TimeStampedModel):
    """Mapped to 'schools' table."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    address = models.TextField(blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'schools'
        ordering = ['name']

    def __str__(self):
        return self.name


class MajorOption(TenantAwareModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)

    class Meta:
        db_table = 'crm_majors'
        unique_together = ('tenant', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"


class B2BOption(TenantAwareModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)

    class Meta:
        db_table = 'crm_b2b_partners'
        unique_together = ('tenant', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"


class VisaStudent(TenantAwareModel):
    """
    Dedicated database table for Visa Check module (/visacheck).
    Completely isolated from the main Student table so additions, edits,
    and deletions in Visa Check do not affect the main CRM students database.
    """
    student_id = models.CharField(max_length=50, blank=True, null=True)  # Student ID e.g. "T3", "M445"
    full_name = models.CharField(max_length=255, db_index=True)
    passport = models.CharField(max_length=50, db_index=True)
    birthday = models.CharField(max_length=50, blank=True, null=True)
    visa_type = models.CharField(max_length=50, default='Embassy')  # 'Embassy', 'E-Visa', 'Regional'
    application_no = models.CharField(max_length=100, blank=True, null=True)

    # Status & visa check details
    status = models.CharField(max_length=100, default='PENDING', db_index=True)
    application_date = models.CharField(max_length=50, blank=True, null=True)
    status_date = models.CharField(max_length=50, blank=True, null=True)
    last_checked = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    pdf_url = models.TextField(blank=True, null=True)
    api_response = models.JSONField(default=dict, blank=True)

    # Management fields (matching univisacheck /cabinet)
    tariff = models.CharField(max_length=100, blank=True, null=True)
    university = models.CharField(max_length=255, blank=True, null=True)
    coordinator = models.CharField(max_length=100, blank=True, null=True)
    b2b = models.CharField(max_length=100, blank=True, null=True)
    flag = models.BooleanField(default=False)
    refund_application = models.BooleanField(default=False)
    pinned = models.BooleanField(default=False)
    batch_selected = models.BooleanField(default=False)

    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = 'crm_visa_students'
        verbose_name = 'Visa Student'
        verbose_name_plural = 'Visa Students'
        ordering = ['-created_at']
        unique_together = ('tenant', 'passport')
        indexes = [
            models.Index(fields=['tenant', 'passport']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'is_deleted']),
            models.Index(fields=['tenant', 'pinned']),
        ]

    def __str__(self):
        return f"{self.passport} - {self.full_name}"

    def save(self, *args, **kwargs):
        if self.passport:
            self.passport = self.passport.strip().upper()
        if self.full_name:
            self.full_name = self.full_name.strip().upper()
        if self.student_id:
            self.student_id = self.student_id.strip().upper()
        if self.application_no:
            self.application_no = self.application_no.strip().upper()
        super().save(*args, **kwargs)
