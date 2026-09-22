"""
Management command: clear_tenant_task_tags
===========================================
Bulk-clears the custom task tag icons (folder/hourglass/checkmark/flag, etc.)
from every student row belonging to a given tenant, plus each user's private
"Only Me" tag override for those students.

This does NOT touch row_color, status_row_color, or any other status field -
only the task_tags array on Student and StudentUserPreference.

Usage:
    python manage.py clear_tenant_task_tags --tenant unibridge --dry-run
    python manage.py clear_tenant_task_tags --tenant unibridge

Flags:
    --tenant   Tenant slug to scope the clear to (e.g. unibridge)
    --dry-run  Preview counts without saving anything
"""
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Clears task_tags for every student (and their per-user tag overrides) under a given tenant."

    def add_arguments(self, parser):
        parser.add_argument('--tenant', required=True, help='Tenant slug to scope the clear to (e.g. unibridge)')
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving')

    def handle(self, *args, **options):
        from apps.students.models import Student, StudentUserPreference
        from apps.tenants.models import Tenant

        slug = options['tenant'].strip()
        dry_run = options['dry_run']

        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            raise CommandError(f"Tenant with slug '{slug}' not found.")

        students = Student.objects.filter(tenant=tenant).exclude(task_tags=[])
        prefs = StudentUserPreference.objects.filter(tenant=tenant).exclude(task_tags=[])

        student_count = students.count()
        pref_count = prefs.count()

        self.stdout.write(f"\n{'[DRY RUN] ' if dry_run else ''}Clear task_tags for tenant: {tenant.name} ({slug})")
        self.stdout.write(f"  Students with tags to clear: {student_count}")
        self.stdout.write(f"  Per-user tag overrides to clear: {pref_count}")

        if student_count == 0 and pref_count == 0:
            self.stdout.write(self.style.WARNING("  Nothing to clear."))
            return

        if dry_run:
            for s in students[:20]:
                self.stdout.write(f"    - {s.id} {s.full_name}: {s.task_tags}")
            if student_count > 20:
                self.stdout.write(f"    ... and {student_count - 20} more")
            self.stdout.write(self.style.WARNING("\n[DRY RUN] No changes were saved."))
            return

        updated_students = students.update(task_tags=[])
        updated_prefs = prefs.update(task_tags=[])

        self.stdout.write(self.style.SUCCESS(f"  [OK] Cleared task_tags on {updated_students} student(s)"))
        self.stdout.write(self.style.SUCCESS(f"  [OK] Cleared task_tags on {updated_prefs} preference override(s)"))
        self.stdout.write(self.style.SUCCESS("\nDone."))
