import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import ArrayField
from apps.core.models import TenantAwareModel, TimeStampedModel, SimpleTenantModel
from apps.students.storage import private_pdf_storage

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
    E_VISA_WITH_CERT = 'E-VISA (TIL SERTIFIKATLI)', 'E-Visa (with certificate)'
    E_VISA_NO_CERT = 'E-VISA (TIL SERTIFIKATISIZ)', 'E-Visa (without certificate)'
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
    # The agency-facing student number (e.g. "UB120", "T15"). Unique WITHIN a
    # tenant, not globally: every branch numbers its own students, so two
    # branches may both have a T15. Always look students up together with
    # their tenant - an id alone is ambiguous across the install.
    id = models.CharField(max_length=50, db_index=True)

    # Immutable anchor and the real primary key. Set once at creation from id
    # (e.g. "PF49" for student "F49") and NEVER updated, so renaming a
    # student's id leaves payments, contracts and preferences attached.
    payment_id = models.CharField(
        max_length=55,
        primary_key=True,
        editable=False,
        help_text="Immutable primary key. Set once on creation (P + student id). Never changes."
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
    father_workplace = models.CharField(max_length=255, blank=True, null=True)  # Ish joyi
    father_job = models.CharField(max_length=255, blank=True, null=True)  # Lavozim
    mother_name = models.CharField(max_length=255, blank=True, null=True)
    mother_phone = models.CharField(max_length=50, blank=True, null=True)
    mother_workplace = models.CharField(max_length=255, blank=True, null=True)  # Ish joyi
    mother_job = models.CharField(max_length=255, blank=True, null=True)  # Lavozim
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
    # Price agreed with this student, captured when the tariff is assigned or
    # changed. Balance is computed from this, NOT from the live TariffOption
    # price: repricing a tariff in Settings must never move the balance of
    # students who already signed at the old price. NULL means "never captured"
    # (legacy rows), and the next recalculation fills it from the live price.
    tariff_price = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )

    # 3. Language Certificates (Supports up to 3 slots)
    # certificate_points holds the raw TOPIK exam score (e.g. 144), distinct
    # from certificate_score which holds the level/band (e.g. "2"). Only
    # TOPIK uses points; other certificate types leave it blank.
    language_certificate = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    certificate_score = models.CharField(max_length=50, blank=True, null=True)
    certificate_points = models.CharField(max_length=50, blank=True, null=True)
    certificate_test_date = models.CharField(max_length=50, blank=True, null=True)
    certificate_valid_date = models.CharField(max_length=50, blank=True, null=True)

    language_certificate_2 = models.CharField(max_length=50, blank=True, null=True)
    certificate_score_2 = models.CharField(max_length=50, blank=True, null=True)
    certificate_points_2 = models.CharField(max_length=50, blank=True, null=True)
    certificate_2_test_date = models.CharField(max_length=50, blank=True, null=True)
    certificate_2_valid_date = models.CharField(max_length=50, blank=True, null=True)

    language_certificate_3 = models.CharField(max_length=50, blank=True, null=True)
    certificate_score_3 = models.CharField(max_length=50, blank=True, null=True)
    certificate_points_3 = models.CharField(max_length=50, blank=True, null=True)
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

    # Computed Kanban pipeline stage for the Status Board, derived from
    # university/invoice/coa/embassy fields on every save via a pre_save
    # signal (see apps/students/signals.py + apps/students/services.py:
    # compute_workflow_stage). Never set directly by API consumers.
    workflow_stage = models.CharField(max_length=20, default='student', blank=True)

    # 8. System & Management Metadata
    office = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    student_group = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    lead_by = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    coordinator = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    quick_notes = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False, db_index=True)  # Soft delete archive

    # "Permanently deleted" no longer means a real DB delete - agencies must
    # never lose a student's historical data. It's a second, deeper hidden
    # state layered on top of is_deleted: the row stays in the database,
    # fully intact, just excluded from the Archive tab and moved into its own
    # "Permanently deleted" sub-tab.
    is_permanently_deleted = models.BooleanField(default=False, db_index=True)
    permanently_deleted_at = models.DateTimeField(null=True, blank=True)

    row_color = models.CharField(max_length=50, blank=True, null=True)
    task_tags = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    folder_ids = ArrayField(models.UUIDField(), default=list, blank=True)
    google_drive_url = models.URLField(max_length=500, blank=True, null=True)
    google_drive_folder_id = models.CharField(max_length=255, blank=True, null=True)
    jarayon_updated_at = models.DateTimeField(blank=True, null=True)
    # Per-field edit dates, as {"<field_name>": "YYYY-MM-DD"}. The drawer shows
    # these as ghost timestamps so staff can tell fresh data from stale. Only
    # keys that have actually been edited are present - a missing key means
    # "never edited since tracking began" and renders blank rather than
    # guessing a date from created_at.
    field_updated_at = models.JSONField(default=dict, blank=True)
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
        constraints = [
            # Student numbers are per-branch; this is what lets unibridge and
            # sodiq each have their own T15.
            models.UniqueConstraint(fields=['tenant', 'id'], name='uniq_student_id_per_tenant'),
        ]
        indexes = [
            models.Index(fields=['tenant', 'id']),
            models.Index(fields=['tenant', 'full_name']),
            models.Index(fields=['tenant', 'is_deleted']),
            models.Index(fields=['tenant', 'is_permanently_deleted']),
            models.Index(fields=['tenant', 'status_hidden']),
            models.Index(fields=['tenant', 'tariff']),
            models.Index(fields=['tenant', 'balance']),
            models.Index(fields=['tenant', 'workflow_stage']),
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
        # A permanently-deleted or renamed-away student can leave its old
        # "P<id>" anchor occupying the row, so when that candidate is already
        # taken we keep doubling the "P" prefix (PPG49, PPPG49, ...) until we
        # land on a free one instead of raising a 500 on save.
        # payment_id is the primary key, so it must exist before the first
        # INSERT and can never change afterwards. Student numbers are only
        # unique per tenant now, so "PT15" can genuinely be taken by another
        # branch's T15 - keep doubling the "P" prefix (PT15, PPT15, PPPT15,
        # ...) until a free anchor is found, which is also how a reused id
        # from a permanently-deleted row is handled.
        if not self.payment_id and self.id:
            candidate = f"P{self.id.strip().upper()}"
            while Student.objects.filter(payment_id=candidate).exists():
                candidate = f"P{candidate}"
            self.payment_id = candidate

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

        # Keep university slots compact and put failed applications last.
        # The slot numbers are display positions, not permanent university IDs.
        unis = []
        for i in range(1, 6):
            u_name = getattr(self, f'university_{i}', None)
            if u_name and isinstance(u_name, str) and u_name.strip():
                unis.append({
                    'name': u_name.strip(),
                    'status': getattr(self, f'university_{i}_status', None) or 'Chosen',
                    'major': getattr(self, f'university_{i}_major', None) or None,
                })

        def is_failed(university):
            return (university['status'] or '').strip().upper() in {'FAILED', 'REJECTED'}

        unis.sort(key=is_failed)

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

        # Status Board Kanban stage, recomputed on every save from the
        # (now-compacted) university/invoice/coa/embassy fields above. Must
        # run here rather than via a pre_save signal: Model.save() freezes
        # update_fields into an immutable frozenset before pre_save is sent,
        # so a signal receiver can no longer append 'workflow_stage' to a
        # partial update_fields list (e.g. services.archive_student's
        # update_fields=['is_deleted', 'updated_at']) by then - it would be
        # silently dropped from the actual SQL UPDATE. Doing it inline here,
        # before super().save(), lets us extend kwargs['update_fields']
        # exactly like the university-compaction block above already does.
        from .services import compute_workflow_stage
        new_stage = compute_workflow_stage(self)
        if self.workflow_stage != new_stage:
            self.workflow_stage = new_stage
            if kwargs.get('update_fields') is not None:
                update_fields = set(kwargs['update_fields'])
                update_fields.add('workflow_stage')
                kwargs['update_fields'] = list(update_fields)

        super().save(*args, **kwargs)


class TariffOption(SimpleTenantModel):
    """Configurable tariff options with default prices. Mapped to 'tariff_options' table."""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    contract_text = models.TextField(blank=True, null=True)
    # Model default stays True so the migration backfills existing tariffs as
    # active (nothing already live gets hidden). New tariffs created through
    # the API are set inactive by TariffOptionViewSet.perform_create instead,
    # so staff can write the contract text before exposing it to students.
    is_active = models.BooleanField(default=True)

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

    def save(self, *args, **kwargs):
        # Enforce uppercase so every tenant's university list stays in one
        # consistent format (e.g. "SEOUL NATIONAL UNIVERSITY (GWANAK, SEOUL)")
        # regardless of how a name was typed when added.
        if self.name:
            self.name = ' '.join(self.name.strip().split()).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class UniversityStatusOption(SimpleTenantModel):
    """Mapped to 'university_statuses' table."""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    color_class = models.CharField(max_length=100, default='text-blue-500')
    # Display rank for a student's universities: the lowest number sorts
    # first, so Accepted (1) floats to the top of a card and Failed (99)
    # sinks. Agencies add their own statuses, so this is editable in
    # Settings rather than hardcoded. The 50 default leaves a new status
    # mid-pack - it can never silently outrank Accepted or sink past
    # Failed until someone positions it deliberately.
    sort_priority = models.IntegerField(default=50)

    class Meta:
        db_table = 'university_statuses'
        ordering = ['sort_priority', 'name']

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


class QuickNoteSuggestion(SimpleTenantModel):
    """
    Configurable quick note suggestions/templates.
    Editable, deletable, and tenant-scoped.
    Mapped to 'crm_quick_note_suggestions' table.
    """
    id = models.BigAutoField(primary_key=True)
    text = models.CharField(max_length=500)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'crm_quick_note_suggestions'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.text


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


class WorkplaceDirectory(TimeStampedModel):
    """
    Global (not tenant-scoped), auto-learning list of parent workplace names
    for the Work Place autocomplete field. Seeded with a curated Uzbek list;
    any custom value a staff member types is upserted here so it becomes a
    suggestion for every tenant going forward - never lost, never duplicated.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, db_index=True)

    class Meta:
        db_table = 'workplace_directory'
        ordering = ['name']

    def __str__(self):
        return self.name


class JobTitleDirectory(TimeStampedModel):
    """Global, auto-learning list of parent job titles - see WorkplaceDirectory."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, db_index=True)

    class Meta:
        db_table = 'job_title_directory'
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
        super().save(*args, **kwargs)


class Contract(TenantAwareModel):
    """
    Multi-tenant Contract model.
    Stores structured document content directly in database (no permanent PDF on server).
    Source of truth for A4 document editor, autosave, and print/export.
    Extends support for online contract signing and verification lifecycle.
    """
    STATUS_CHOICES = [
        ('draft', 'Qoralama'),
        ('pending', 'Kutilmoqda'),
        ('verified', 'Tasdiqlangan'),
        ('rejected', 'Rad etilgan'),
        ('sent', 'Yuborilgan'),
        ('viewed', "Ko'rildi"),
        ('signed', 'Imzolangan'),
        ('completed', 'Yakunlangan'),
        ('cancelled', 'Bekor qilingan'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        Student,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracts',
        db_column='student_id'
    )
    student_account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='online_contracts'
    )
    contract_number = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=255)
    template_name = models.CharField(max_length=100, blank=True, default='')
    content = models.TextField(help_text="Structured HTML document content")
    # When the tariff was built in the A4 canvas editor (ContractDocumentEditor.vue),
    # `content` above stores that page's HTML already rendered with THIS
    # contract's own student data flattened in ({{tokens}} replaced, pages
    # joined with <hr data-page-break="true" />) so the no-login student
    # signing page (contract_sign_views.py) can serve it verbatim with no
    # further templating step. PDF export, however, needs the ORIGINAL
    # canvas-contract JSON (still carrying {{tokens}} and each page's own
    # fixed 210x297mm sizing) to lay the document out correctly -
    # flattening loses the structured per-page layout contractPdf.ts's
    # canvas renderer depends on. This field holds that original source,
    # blank for contracts built from plain-HTML (non-canvas) tariffs.
    canvas_source = models.TextField(blank=True, default='', help_text="Original canvas-contract JSON (tokens unresolved), for PDF export only")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    version = models.PositiveIntegerField(default=1)
    is_deleted = models.BooleanField(default=False, db_index=True)

    # Archive: orthogonal to status - any contract regardless of its status
    # can be archived to hide it from every other filter (All/Pending/
    # Verified/Cancelled), without changing or losing its underlying status.
    is_archived = models.BooleanField(default=False, db_index=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    # Tariff & Student form data snapshots
    tariff_option = models.ForeignKey(
        'students.TariffOption',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracts'
    )
    tariff_name = models.CharField(max_length=255, blank=True, default='')
    tariff_price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    passport_number = models.CharField(max_length=50, blank=True, default='', db_index=True)
    full_name = models.CharField(max_length=255, blank=True, default='')
    education_level = models.CharField(max_length=100, blank=True, default='')
    date_of_birth = models.CharField(max_length=50, blank=True, default='')
    office = models.CharField(max_length=100, blank=True, default='')
    phone1 = models.CharField(max_length=50, blank=True, default='')
    phone2 = models.CharField(max_length=50, blank=True, default='')

    # Electronic Signature & Snapshot Integrity
    signature_data = models.TextField(blank=True, default='', help_text="Base64 data URL of student signature")

    # Guardian (kafil) consent for minors: Fuqarolik kodeksi 27-modda requires
    # a parent/guardian's written consent for a 14-18 year old's contract to
    # be valid at all, so these are only populated (and required at submit
    # time) when the student was under 18 on the day they signed.
    is_minor = models.BooleanField(default=False, help_text="Student was under 18 at signing time")
    guardian_full_name = models.CharField(max_length=255, blank=True, default='')
    guardian_passport_number = models.CharField(max_length=50, blank=True, default='')
    guardian_relation = models.CharField(max_length=100, blank=True, default='')
    guardian_phone = models.CharField(max_length=50, blank=True, default='')
    guardian_address = models.CharField(max_length=255, blank=True, default='')
    guardian_signature_data = models.TextField(blank=True, default='', help_text="Base64 data URL of guardian signature")

    declarations_accepted = models.BooleanField(default=False)
    agreement_confirmations = models.JSONField(default=dict, blank=True)
    contract_hash = models.CharField(max_length=64, blank=True, default='', help_text="SHA-256 hash of immutable snapshot")
    snapshot_data = models.JSONField(default=dict, blank=True, help_text="Immutable snapshot of tariff, template, student data at signing")

    # Agency Verification Flow
    student_id_assigned = models.CharField(max_length=50, blank=True, default='', db_index=True)
    verification_code = models.CharField(max_length=64, blank=True, default='', db_index=True)
    verification_code_expires_at = models.DateTimeField(null=True, blank=True)
    verification_code_generated_at = models.DateTimeField(null=True, blank=True)
    verification_code_used = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    # Rejection Flow
    rejection_reason = models.TextField(blank=True, default='')
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracts_rejected'
    )

    # Tracking & Sign audit
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracts_updated',
        db_column='updated_by_id'
    )
    sign_token = models.CharField(max_length=100, unique=True, null=True, blank=True, db_index=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    signer_ip = models.GenericIPAddressField(null=True, blank=True)
    signer_user_agent = models.TextField(blank=True, null=True)

    # Staff-prefilled signing link lifecycle (no student account/login
    # involved - the token itself is the access key, like sign_token's
    # original intent). Reusable until the flow completes: a student
    # closing the browser mid-flow and reopening the same link resumes
    # instead of starting over. Rejected by every write endpoint once used.
    sign_token_expires_at = models.DateTimeField(null=True, blank=True)
    sign_token_used_at = models.DateTimeField(null=True, blank=True)
    identity_confirm_attempts = models.PositiveSmallIntegerField(default=0)
    identity_confirmed_at = models.DateTimeField(null=True, blank=True)

    # Didit KYC state for the link-based flow, scoped directly to this
    # Contract rather than the IdentityVerification/StudentProfile models -
    # this flow has no student account to hang that table off, and keeping
    # it isolated here means zero changes to the existing self-service
    # flow's models. A contract in this flow has exactly one KYC attempt
    # that matters, so no retry-history table is needed (a decline+retry
    # just overwrites these fields).
    kyc_status = models.CharField(max_length=20, default='NOT_STARTED', db_index=True)
    kyc_session_id = models.CharField(max_length=100, blank=True, default='')
    kyc_session_url = models.TextField(blank=True, default='')
    kyc_raw_decision = models.JSONField(default=dict, blank=True)
    kyc_extracted_full_name = models.CharField(max_length=255, blank=True, default='')
    kyc_extracted_document_number = models.CharField(max_length=50, blank=True, default='')
    kyc_extracted_date_of_birth = models.CharField(max_length=50, blank=True, default='')
    kyc_face_match_result = models.CharField(max_length=50, blank=True, default='')
    kyc_liveness_result = models.CharField(max_length=50, blank=True, default='')
    kyc_confirmed_at = models.DateTimeField(null=True, blank=True)

    # Server-side canonical PDF (Stage 2 canary - see contract_pdf_service.py).
    # Generated once from the authoritative snapshot (template + student data
    # + signature_data, all already persisted above) via headless Chromium,
    # so every device downloads these exact bytes instead of re-rendering
    # with html2canvas/jsPDF locally. Null until first generated. Immutable
    # once set - a contract needing changes goes through the existing
    # re-sign/versioning flow, never a silent overwrite of this file.
    final_pdf = models.FileField(upload_to='', storage=private_pdf_storage, null=True, blank=True)
    final_pdf_generated_at = models.DateTimeField(null=True, blank=True)
    # Guards concurrent generation requests from racing each other into two
    # different renders for the same contract - 'pending' is held for the
    # duration of one render attempt (see generate_final_pdf's select_for_update).
    FINAL_PDF_STATUS_CHOICES = [
        ('not_generated', 'Not generated'),
        ('pending', 'Generating'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    ]
    final_pdf_status = models.CharField(max_length=20, choices=FINAL_PDF_STATUS_CHOICES, default='not_generated')

    class Meta:
        db_table = 'contracts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'is_deleted']),
            models.Index(fields=['tenant', 'is_archived']),
            models.Index(fields=['tenant', 'contract_number']),
            models.Index(fields=['student_account', 'status']),
        ]

    def __str__(self):
        return f"{self.contract_number} - {self.title} ({self.status})"


class ContractAuditEvent(TimeStampedModel):
    """
    Dedicated audit history for contract lifecycle events:
    student view, signature, password submission, agency assignment, verification, rejection.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='audit_events'
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='contract_audit_events'
    )
    action = models.CharField(max_length=100, db_index=True)
    actor_type = models.CharField(max_length=50)  # 'STUDENT', 'STAFF', 'SYSTEM'
    actor_id = models.CharField(max_length=100, blank=True, default='')
    actor_email = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'crm_contract_audit_events'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.action}] Contract {self.contract_id} by {self.actor_email or self.actor_type}"
