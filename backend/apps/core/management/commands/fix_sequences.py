"""
Realigns PostgreSQL id sequences with the data actually in each table.

Rows imported with explicit primary keys (see import_from_supabase) leave the
table's sequence behind, so the next INSERT reuses an id that already exists and
fails with:

    IntegrityError: duplicate key value violates unique constraint "<table>_pkey"

Run this after any import that writes explicit ids:

    python manage.py fix_sequences            # repair every drifted sequence
    python manage.py fix_sequences --check    # report only, change nothing
"""

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Resets id sequences so they continue past the largest existing id."

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Report drifted sequences without changing anything.',
        )

    def handle(self, *args, **options):
        check_only = options['check']

        if connection.vendor != 'postgresql':
            self.stdout.write(self.style.WARNING(
                f"Database is '{connection.vendor}', not postgresql -- nothing to do."
            ))
            return

        drifted = []
        checked = 0

        for model in apps.get_models():
            pk = model._meta.pk
            if pk is None or pk.get_internal_type() not in ('AutoField', 'BigAutoField'):
                continue

            table = model._meta.db_table
            column = pk.column

            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_get_serial_sequence(%s, %s)", [table, column])
                row = cursor.fetchone()
                sequence = row[0] if row else None
                if not sequence:
                    continue

                checked += 1
                cursor.execute(f'SELECT COALESCE(MAX("{column}"), 0) FROM "{table}"')
                max_id = cursor.fetchone()[0]

                cursor.execute(f"SELECT last_value, is_called FROM {sequence}")
                last_value, is_called = cursor.fetchone()
                next_id = last_value + 1 if is_called else last_value

                if next_id > max_id:
                    continue

                drifted.append((table, sequence, max_id, next_id))

                if not check_only:
                    # setval(..., true) makes the *next* value max_id + 1.
                    cursor.execute("SELECT setval(%s, %s, true)", [sequence, max_id])

        self.stdout.write(f"Sequences checked: {checked}")

        if not drifted:
            self.stdout.write(self.style.SUCCESS("All sequences are in sync."))
            return

        for table, _sequence, max_id, next_id in drifted:
            self.stdout.write(
                f"  {table}: max id {max_id}, next id would have been {next_id}"
            )

        if check_only:
            self.stdout.write(self.style.WARNING(
                f"{len(drifted)} sequence(s) out of sync. Re-run without --check to repair."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Repaired {len(drifted)} sequence(s)."
            ))
