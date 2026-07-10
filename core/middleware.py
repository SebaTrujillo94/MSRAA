class PermissionsPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Permissions-Policy'] = (
            'picture-in-picture=*, '
            'autoplay=*, '
            'fullscreen=*'
        )
        return response


class TrafficMiddleware:
    """Record daily page visit counts. Skips admin, static, and media paths."""

    SKIP_PREFIXES = ('/admin/', '/static/', '/media/', '/favicon', '/__debug__/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        path = request.path
        if (response.status_code == 200
                and request.method == 'GET'
                and not any(path.startswith(p) for p in self.SKIP_PREFIXES)):
            try:
                from django.utils import timezone
                from django.db.models import F
                from .models import SiteVisit
                today = timezone.localdate()
                # Normalize path: strip query string, truncate to 300 chars
                clean = path[:300]
                obj, created = SiteVisit.objects.get_or_create(
                    date=today, path=clean,
                    defaults={'count': 1},
                )
                if not created:
                    SiteVisit.objects.filter(pk=obj.pk).update(count=F('count') + 1)
            except Exception:
                pass  # never break the site for monitoring
        return response
