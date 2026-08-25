from django.db import migrations, models
import django.db.models.deletion


DEFAULT_UNIVERSITY_STATUSES = [
    ('Chosen', 'text-blue-500'),
    ('Applying', 'text-amber-500'),
    ('Applied', 'text-indigo-500'),
    ('Accepted', 'text-emerald-500'),
    ('Failed', 'text-rose-500'),
]


def fan_out_per_tenant(apps, schema_editor):
    """
    Universities and university statuses are per-tenant defaults: every tenant
    starts from the same list, and its later edits are its own.

    Universities currently exist once, globally (tenant=NULL). Give each tenant
    its own copy of that list, then drop the originals so nothing is shared.

    Statuses are already per-tenant, but only one tenant has any; give every
    tenant without them the default set.
    """
    Tenant = apps.get_model('tenants', 'Tenant')
    UniversityOption = apps.get_model('students', 'UniversityOption')
    UniversityStatusOption = apps.get_model('students', 'UniversityStatusOption')

    tenants = list(Tenant.objects.all())
    if not tenants:
        return

    # ── Universities ──────────────────────────────────────────────────
    global_names = list(
        UniversityOption.objects.filter(tenant__isnull=True)
        .values_list('name', flat=True)
    )
    # Deduplicate while keeping order stable.
    seen = set()
    base_names = []
    for n in global_names:
        key = (n or '').strip()
        if key and key.lower() not in seen:
            seen.add(key.lower())
            base_names.append(key)

    for tenant in tenants:
        existing = {
            (n or '').strip().lower()
            for n in UniversityOption.objects.filter(tenant=tenant).values_list('name', flat=True)
        }
        UniversityOption.objects.bulk_create([
            UniversityOption(name=name, tenant=tenant)
            for name in base_names
            if name.lower() not in existing
        ])

    # The originals were the shared copy; each tenant now owns its own.
    UniversityOption.objects.filter(tenant__isnull=True).delete()

    # ── University statuses ───────────────────────────────────────────
    for tenant in tenants:
        existing = {
            (n or '').strip().lower()
            for n in UniversityStatusOption.objects.filter(tenant=tenant).values_list('name', flat=True)
        }
        for name, color in DEFAULT_UNIVERSITY_STATUSES:
            if name.lower() not in existing:
                UniversityStatusOption.objects.create(
                    name=name, color_class=color, tenant=tenant
                )


def collapse_to_global(apps, schema_editor):
    """
    Reverse: collapse the per-tenant university lists back to a single global
    list so the column can be removed without losing the set of names.
    """
    UniversityOption = apps.get_model('students', 'UniversityOption')

    seen = set()
    keep_ids = []
    for opt in UniversityOption.objects.all().order_by('id'):
        key = (opt.name or '').strip().lower()
        if key and key not in seen:
            seen.add(key)
            keep_ids.append(opt.id)

    UniversityOption.objects.exclude(id__in=keep_ids).delete()
    UniversityOption.objects.update(tenant=None)


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0002_tagoption'),
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='universityoption',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='students_universityoption_set',
                db_column='tenant_id',
                to='tenants.tenant',
            ),
        ),
        migrations.RunPython(fan_out_per_tenant, collapse_to_global),
    ]
