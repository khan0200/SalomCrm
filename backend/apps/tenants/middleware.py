from django.utils.functional import SimpleLazyObject


def resolve_tenant(request):
    """
    Determine the tenant a request should be scoped to.

    Super Admins may switch context with an X-Tenant-ID header (or a
    ?tenant_id= parameter); everyone else is always pinned to their own
    tenant, so a header from them is ignored.
    """
    user = getattr(request, 'user', None)
    if user is None or not getattr(user, 'is_authenticated', False):
        return None

    is_super = (
        getattr(user, 'is_superuser', False)
        or getattr(user, 'role', '') == 'SUPER_ADMIN'
    )

    if is_super:
        header = request.headers.get('X-Tenant-ID') or request.GET.get('tenant_id')
        if header:
            from apps.tenants.models import Tenant
            return Tenant.objects.filter(id=header, is_active=True).first()

    return getattr(user, 'tenant', None)


class TenantMiddleware:
    """
    Attaches tenant context to the request as `request.tenant`.

    Resolution is LAZY. This middleware runs before DRF authenticates the
    request, and with stateless JWT auth `request.user` is still
    AnonymousUser at that point -- so resolving eagerly always produced None
    and a Super Admin's X-Tenant-ID header was silently ignored, leaking
    every tenant's data into the switched-in view.

    SimpleLazyObject defers evaluation until something actually reads
    `request.tenant`, which happens inside the view, where DRF has populated
    request.user. It is per-request, so nothing is shared between threads.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = SimpleLazyObject(lambda: resolve_tenant(request))
        return self.get_response(request)
