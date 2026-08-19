from .models import AuditLog

def log_audit_event(action, entity_type, entity_id=None, tenant=None, user=None, description=None, changes=None, request=None):
    """Utility function to safely record an audit log event."""
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')

    return AuditLog.objects.create(
        tenant=tenant or (getattr(user, 'tenant', None) if user else None),
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        description=description,
        changes=changes or {},
        ip_address=ip_address
    )
