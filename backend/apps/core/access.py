from django.db.models import Q
from apps.authentication.models import DataScope, UserRole


def is_branch_restricted(user) -> bool:
    """
    Whether `user` must only see their own branch's data.

    A tenant can have several HEAD_MANAGER accounts (e.g. one per branch
    office, plus the agency's actual owner/CEO) - role alone doesn't tell you
    who should see everything, so this only exempts the platform-wide
    SUPER_ADMIN and defers to each user's own data_scope otherwise.
    """
    if user.is_superuser:
        return False
    if getattr(user, 'role', None) == UserRole.SUPER_ADMIN:
        return False
    return getattr(user, 'data_scope', DataScope.ALL) == DataScope.BRANCH_ONLY


def branch_scope_filter(user, office_field: str = 'office') -> Q:
    """
    Q object restricting a Student (or student-joined) queryset to `user`'s
    own branch when they're branch-restricted; an unrestricted no-op Q()
    otherwise.

    `office_field` is the lookup path to Student.office from the model being
    queried - 'office' when querying Student directly, 'student__office' for
    models with an FK to Student (Payment, Contract, ...).

    A record with no office set yet (blank/NULL - or, via the FK path, no
    linked student at all) belongs to no one's branch - it's unclaimed
    shared-pool data, not "someone else's branch", so it stays visible to
    every BRANCH_ONLY user rather than vanishing until an ALL-scope manager
    happens to assign it an office. Only a record tagged to a *different*
    branch is actually excluded.

    A branch-restricted user with no branch of their own assigned matches
    nothing - that's a misconfigured account state the serializer already
    refuses to create, so this is just a conservative fallback, never the
    normal path.
    """
    if not is_branch_restricted(user):
        return Q()
    branch_name = getattr(getattr(user, 'branch', None), 'name', None)
    if not branch_name:
        return Q(pk__in=[])
    return (
        Q(**{office_field: branch_name}) |
        Q(**{f'{office_field}__isnull': True}) |
        Q(**{office_field: ''})
    )
