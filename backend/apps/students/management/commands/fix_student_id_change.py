"""
Management command: fix_student_id_change
==========================================
Fallback utility for when a student's primary-key ID is changed manually
(e.g. F51 -> F49) and the orphan old-ID row needs cleaning up.

With the payment_id system, payments are now linked via the immutable
payment_id field (e.g. 'PF49'), so renaming Student.id no longer
orphans payments. This command is mainly a safety cleanup tool.

Usage:
    python manage.py fix_student_id_change --old-id F51 --new-id F49

Flags:
    --old-id   The stale/orphan student ID (e.g. F51)
    --new-id   The correct new student ID that should own all history (e.g. F49)
    --dry-run  Preview changes without saving anything
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Re-links payments from an orphan old student ID to the new student ID and deletes the orphan."

    def add_arguments(self, parser):
        parser.add_argument('--old-id', required=True, help='The orphan/stale student ID (e.g. F51)')
        parser.add_argument('--new-id', required=True, help='The correct new student ID (e.g. F49)')
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving')

    def handle(self, *args, **options):
        from apps.students.models import Student
        from apps.payments.models import Payment
        from apps.payments.services import recalculate_student_financials

        old_id = options['old_id'].strip().upper()
        new_id = options['new_id'].strip().upper()
        dry_run = options['dry_run']

        if old_id == new_id:
            raise CommandError("--old-id and --new-id must be different.")

        # Fetch both students
        try:
            old_student = Student.objects.get(id=old_id)
        except Student.DoesNotExist:
            raise CommandError(f"Old student '{old_id}' not found in DB.")

        try:
            new_student = Student.objects.get(id=new_id)
        except Student.DoesNotExist:
            raise CommandError(f"New student '{new_id}' not found in DB. Has the ID change been saved?")

        # Find payments pointing at old student's payment_id (or fallback to student=old_student)
        payments = Payment.objects.filter(student=old_student)
        count = payments.count()

        self.stdout.write(f"\n{'[DRY RUN] ' if dry_run else ''}Fix student ID change: {old_id} -> {new_id}")
        self.stdout.write(f"  Old student: {old_student.full_name} (id={old_id}, payment_id={old_student.payment_id})")
        self.stdout.write(f"  New student: {new_student.full_name} (id={new_id}, payment_id={new_student.payment_id})")
        self.stdout.write(f"  Payments to re-link: {count}")

        if count == 0:
            self.stdout.write(self.style.WARNING("  No payments found under old ID — nothing to migrate."))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] No changes were saved."))
            return

        with transaction.atomic():
            # 1. Re-point all payments to new student's payment_id
            updated = payments.update(student=new_student)
            self.stdout.write(self.style.SUCCESS(f"  [OK] Re-linked {updated} payment(s) to {new_id} ({new_student.payment_id})"))

            # 2. Recalculate new student's balance
            new_student = recalculate_student_financials(new_student)
            self.stdout.write(self.style.SUCCESS(
                f"  [OK] Recalculated balance for {new_id}: {new_student.balance} UZS"
            ))

            # 3. Delete the orphan old student row
            old_student.delete()
            self.stdout.write(self.style.SUCCESS(f"  [OK] Deleted orphan student record '{old_id}'"))

        self.stdout.write(self.style.SUCCESS("\nDone. Payments page and student page should now be consistent."))
