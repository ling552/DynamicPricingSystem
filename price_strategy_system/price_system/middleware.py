import re

from django.conf import settings


_LOCAL_ORIGIN_RE = re.compile(r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$")


class DevLocalhostCsrfTrustedOriginsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, "DEBUG", False):
            origin = request.META.get("HTTP_ORIGIN")
            if origin and _LOCAL_ORIGIN_RE.match(origin):
                trusted = list(getattr(settings, "CSRF_TRUSTED_ORIGINS", []))
                if origin not in trusted:
                    trusted.append(origin)
                    settings.CSRF_TRUSTED_ORIGINS = trusted
        return self.get_response(request)


class DevForceUtf8CharsetMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if getattr(settings, "DEBUG", False):
            content_type = response.get("Content-Type", "")
            if content_type.startswith("text/") and "charset=" not in content_type.lower():
                response["Content-Type"] = f"{content_type}; charset=utf-8" if content_type else "text/html; charset=utf-8"
        return response
