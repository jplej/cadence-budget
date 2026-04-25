from .models import Tenant


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0]
        slug = host.split(".")[0]
        try:
            request.tenant = Tenant.objects.get(slug=slug, is_active=True)
        except Tenant.DoesNotExist:
            request.tenant = None
        return self.get_response(request)
