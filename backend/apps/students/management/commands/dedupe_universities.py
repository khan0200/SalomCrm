from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = (
        "Find and remove duplicate UniversityOption rows within each tenant "
        "(same name, case-insensitive, ignoring surrounding whitespace). "
        "Keeps the oldest row (lowest id) for each duplicate name. "
        "Runs as a dry-run report unless --apply is passed."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Actually delete the duplicate rows. Without this flag, only reports what would change.',
        )

    def handle(self, *args, **options):
        from apps.students.models import UniversityOption

        apply_changes = options['apply']

        by_tenant = defaultdict(lambda: defaultdict(list))
        for uni in UniversityOption.objects.all().order_by('id'):
            key = (uni.name or '').strip().lower()
            if not key:
                continue
            by_tenant[uni.tenant_id][key].append(uni)

        total_dupe_rows = 0
        total_groups = 0
        ids_to_delete = []

        for tenant_id, groups in by_tenant.items():
            for key, rows in groups.items():
                if len(rows) <= 1:
                    continue
                total_groups += 1
                keep, *rest = rows
                total_dupe_rows += len(rest)
                ids_to_delete.extend(r.id for r in rest)
                names_shown = ", ".join(f"id={r.id}" for r in rest)
                self.stdout.write(
                    f"tenant={tenant_id} name='{keep.name}' "
                    f"keep=id={keep.id} delete=[{names_shown}]"
                )

        self.stdout.write(self.style.WARNING(
            f"\n{total_groups} duplicate name groups, {total_dupe_rows} rows would be deleted."
        ))

        if not apply_changes:
            self.stdout.write(self.style.NOTICE(
                "Dry run only — no changes made. Re-run with --apply to delete duplicates."
            ))
            return

        if not ids_to_delete:
            self.stdout.write(self.style.SUCCESS("Nothing to delete."))
            return

        with transaction.atomic():
            deleted, _ = UniversityOption.objects.filter(id__in=ids_to_delete).delete()

        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} duplicate rows."))
