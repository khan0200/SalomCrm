class TenantMiddleware:
    """
    Middleware that attaches tenant context to the current request
    based on the authenticated user or an explicit X-Tenant-ID header
    for Super Admins switching contexts.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.is_superuser or getattr(request.user, 'role', '') == 'SUPER_ADMIN':
                tenant_header = request.headers.get('X-Tenant-ID') or request.GET.get('tenant_id')
                if tenant_header:
                    from apps.tenants.models import Tenant
                    request.tenant = Tenant.objects.filter(id=tenant_header, is_active=True).first()
                else:
                    request.tenant = getattr(request.user, 'tenant', None)
            else:
                request.tenant = getattr(request.user, 'tenant', None)

        response = self.get_response(request)
        return response
