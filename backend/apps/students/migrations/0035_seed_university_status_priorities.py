from django.db import migrations

# Rank for the statuses every tenant ships with. Lower sorts first, so a
# student's Accepted university leads their card and Failed ones sink.
# Anything not listed keeps the model default (50) and lands mid-pack.
DEFAULT_PRIORITIES = {
    'accepted': 1,
    'applied': 2,
    'chosen': 3,
    'failed': 99,
}

# "Applying" was never meaningfully used (one student) and duplicates
# "Applied", so it is retired. Records still holding it are moved across
# rather than left pointing at a status no longer offered anywhere.
RETIRED_STATUS = 'applying'
RETIRED_REPLACEMENT = 'Applied'


def seed_priorities(apps, schema_editor):
    UniversityStatusOption = apps.get_model('students', 'UniversityStatusOption')
    Student = apps.get_model('students', 'Student')

    for option in UniversityStatusOption.objects.all():
        priority = DEFAULT_PRIORITIES.get((option.name or '').strip().lower())
        if priority is not None and option.sort_priority != priority:
            option.sort_priority = priority
            option.save(update_fields=['sort_priority'])

    # Repoint any student still carrying the retired status.
    status_fields = [f'university_{i}_status' for i in range(1, 6)]
    for student in Student.objects.all().only('id', *status_fields):
        changed = []
        for field in status_fields:
            value = getattr(student, field, None)
            if isinstance(value, str) and value.strip().lower() == RETIRED_STATUS:
                setattr(student, field, RETIRED_REPLACEMENT)
                changed.append(field)
        if changed:
            student.save(update_fields=changed)

    UniversityStatusOption.objects.filter(name__iexact=RETIRED_STATUS).delete()


def unseed(apps, schema_editor):
    # The retired status and the students moved off it are not restored:
    # re-creating it would reintroduce an option the agency chose to drop,
    # and the original per-student values are not recoverable from here.
    UniversityStatusOption = apps.get_model('students', 'UniversityStatusOption')
    UniversityStatusOption.objects.update(sort_priority=50)


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0034_alter_universitystatusoption_options_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_priorities, unseed),
    ]
