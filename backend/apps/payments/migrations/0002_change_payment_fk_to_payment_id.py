# Re-points the Payment student FK to the immutable payment_id field.
# The old FK constraint was already dropped by students/0008_populate_payment_ids.
# This migration just adds the new constraint referencing students.payment_id.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
        ('students', '0008_populate_payment_ids'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='student',
            field=models.ForeignKey(
                blank=True,
                db_column='student_id',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='payments',
                to='students.student',
                to_field='payment_id',
            ),
        ),
    ]
