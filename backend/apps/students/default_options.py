"""
Default option lists given to every tenant.

These are per-tenant defaults, not shared rows: a new tenant starts from the
same list as everyone else, and whatever it adds, renames or deletes afterwards
affects only that tenant.
"""

DEFAULT_UNIVERSITY_STATUSES = [
    ('Chosen', 'text-blue-500'),
    ('Applying', 'text-amber-500'),
    ('Applied', 'text-indigo-500'),
    ('Accepted', 'text-emerald-500'),
    ('Failed', 'text-rose-500'),
]


def seed_default_options(tenant):
    """
    Give `tenant` the default universities and university statuses.

    Idempotent: existing names are left alone, so this is safe to re-run and
    will not clobber a tenant's own edits.
    """
    from .models import UniversityOption, UniversityStatusOption

    # ── University statuses ───────────────────────────────────────────
    existing_statuses = {
        (n or '').strip().lower()
        for n in UniversityStatusOption.objects.filter(tenant=tenant).values_list('name', flat=True)
    }
    for name, color in DEFAULT_UNIVERSITY_STATUSES:
        if name.lower() not in existing_statuses:
            UniversityStatusOption.objects.create(
                name=name, color_class=color, tenant=tenant
            )

    # ── Universities ──────────────────────────────────────────────────
    # Copy the catalogue an existing tenant already has, so a new agency does
    # not start with an empty university list. Falls back to nothing if this is
    # the very first tenant; universities can then be added in Settings.
    existing_unis = {
        (n or '').strip().lower()
        for n in UniversityOption.objects.filter(tenant=tenant).values_list('name', flat=True)
    }

    source_names = (
        UniversityOption.objects.exclude(tenant=tenant)
        .values_list('name', flat=True)
        .order_by('name')
    )

    seen = set()
    to_create = []
    for raw in source_names:
        name = (raw or '').strip()
        key = name.lower()
        if not name or key in seen or key in existing_unis:
            continue
        seen.add(key)
        to_create.append(UniversityOption(name=name, tenant=tenant))

    if to_create:
        UniversityOption.objects.bulk_create(to_create)
