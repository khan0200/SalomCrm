from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Print the current union of all tenants' university names as a "
        "Python list literal, ready to paste into DEFAULT_UNIVERSITIES in "
        "apps/students/default_options.py. Read-only — makes no changes."
    )

    def handle(self, *args, **options):
        from apps.students.models import UniversityOption

        seen = set()
        names = []
        qs = UniversityOption.objects.all().order_by('name').values_list('name', flat=True)
        for raw in qs:
            name = (raw or '').strip()
            key = name.lower()
            if not name or key in seen:
                continue
            seen.add(key)
            names.append(name)

        self.stdout.write(self.style.WARNING(f"{len(names)} unique university names found.\n"))
        self.stdout.write("DEFAULT_UNIVERSITIES = [")
        for name in names:
            escaped = name.replace("'", "\\'")
            self.stdout.write(f"    '{escaped}',")
        self.stdout.write("]")
