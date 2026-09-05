"""
Data migration: populate payment_id for existing students and
update existing payment rows to store payment_id values.

Key: must DROP the old FK constraint (payments -> students.id)
BEFORE updating payment rows, otherwise the commit fails.
The new FK (payments -> students.payment_id) is added by payments/0002.
"""
from django.db import migrations


def populate_payment_ids(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        # Step 1: Drop old FK constraint so we can freely update student_id values
        cursor.execute("""
            ALTER TABLE payments
            DROP CONSTRAINT IF EXISTS payments_student_id_afd7e8d1_fk_students_id;
        """)
        print("  [OK] Dropped old FK constraint payments -> students.id")

        # Step 2: Set payment_id = 'P' + id for all students
        cursor.execute("""
            UPDATE students
            SET payment_id = 'P' || id
            WHERE payment_id IS NULL
        """)
        print(f"  [OK] Set payment_id on {cursor.rowcount} student(s).")

        # Step 3: Update payment rows — prefix student_id with 'P'
        cursor.execute("""
            UPDATE payments
            SET student_id = 'P' || student_id
            WHERE student_id IS NOT NULL
              AND student_id NOT LIKE 'P%'
        """)
        print(f"  [OK] Updated student_id on {cursor.rowcount} payment(s).")


def reverse_payment_ids(apps, schema_editor):
    """Reverse: restore old FK and strip 'P' prefix from payment student_id values."""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            UPDATE payments
            SET student_id = SUBSTRING(student_id FROM 2)
            WHERE student_id IS NOT NULL
              AND student_id LIKE 'P%'
        """)
        cursor.execute("""
            ALTER TABLE payments
            ADD CONSTRAINT payments_student_id_afd7e8d1_fk_students_id
            FOREIGN KEY (student_id) REFERENCES students(id)
            DEFERRABLE INITIALLY DEFERRED;
        """)


class Migration(migrations.Migration):

    # Must run after the payment_id column is added to students
    dependencies = [
        ('students', '0007_add_payment_id_field'),
        ('payments', '0001_initial'),
    ]

    # Not atomic so the DROP CONSTRAINT and data UPDATE commit independently
    atomic = False

    operations = [
        migrations.RunPython(populate_payment_ids, reverse_code=reverse_payment_ids),
    ]
