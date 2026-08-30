from django.db import migrations

def normalize_offices(apps, schema_editor):
    Tenant = apps.get_model('tenants', 'Tenant')
    Branch = apps.get_model('tenants', 'Branch')
    Student = apps.get_model('students', 'Student')

    for tenant in Tenant.objects.all():
        branches = list(Branch.objects.filter(tenant=tenant))
        branch_map = {b.name.strip().upper(): b.name for b in branches}
        base_map = {}
        for b in branches:
            clean_b = b.name.strip().upper().replace(' OFFIS', '').replace(' OFFICE', '').strip()
            base_map[clean_b] = b.name

        for student in Student.objects.filter(tenant=tenant):
            if not student.office:
                continue
            curr = student.office.strip()
            curr_upper = curr.upper()
            
            if curr_upper in branch_map:
                if student.office != branch_map[curr_upper]:
                    student.office = branch_map[curr_upper]
                    student.save(update_fields=['office'])
                continue

            curr_clean = curr_upper.replace(' OFFIS', '').replace(' OFFICE', '').strip()
            if curr_clean in base_map:
                student.office = base_map[curr_clean]
                student.save(update_fields=['office'])
                continue
            if curr_upper in base_map:
                student.office = base_map[curr_upper]
                student.save(update_fields=['office'])
                continue

class Migration(migrations.Migration):

    dependencies = [
        ('students', '0005_student_telegram_username'),
        ('tenants', '0002_branch_icon'),
    ]

    operations = [
        migrations.RunPython(normalize_offices, migrations.RunPython.noop),
    ]
