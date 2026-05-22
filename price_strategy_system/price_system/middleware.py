import re

from django.conf import settings


# Host syntax (RFC-compatible enough for our purposes): letters, digits, dots,
# hyphens, underscores, plus an optional `:port`.
_HOST_RE = re.compile(r"^[A-Za-z0-9._\-]+(:\d+)?$")


class DynamicCsrfTrustedOriginsMiddleware:
    """Add the current request's `<scheme>://<host>` to CSRF_TRUSTED_ORIGINS.

    Why this exists
    ---------------
    Django's CSRF protection rejects POSTs whose Origin/Referer is not listed
    in ``CSRF_TRUSTED_ORIGINS``. In Docker deployments people typically reach
    the same image via several URLs (``127.0.0.1``, a LAN IP, a public IP, a
    reverse-proxy domain). Asking each operator to predeclare every variant
    in an env var is brittle, especially for one-click demo deployments.

    What this does
    --------------
    For every incoming request, we look at ``request.get_host()`` — which
    Django has *already* validated against ``ALLOWED_HOSTS`` before this
    middleware runs — and ensure ``<scheme>://<host>`` is in
    ``CSRF_TRUSTED_ORIGINS``. We never trust a host that ALLOWED_HOSTS
    rejected, so the security boundary is the same as Django's built-in
    host validation.

    Operators who want stricter behavior can:
      * set ``DPS_ALLOWED_HOSTS`` to an explicit list (instead of the default
        ``*``), which limits what this middleware will ever trust, or
      * predeclare every origin via ``DPS_CSRF_TRUSTED_ORIGINS``.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            host = request.get_host()
        except Exception:
            host = None

        if host and _HOST_RE.match(host):
            # request.scheme respects SECURE_PROXY_SSL_HEADER if configured.
            # For convenience we ALSO trust the opposite scheme so reverse
            # proxies that terminate TLS (browser sees https://, the Django
            # process sees http://) work out of the box. Host validation
            # still gates which hosts are trusted at all.
            origins = {
                f"http://{host}",
                f"https://{host}",
                f"{request.scheme}://{host}",
            }

            trusted = list(getattr(settings, "CSRF_TRUSTED_ORIGINS", []) or [])
            changed = False
            for origin in origins:
                if origin not in trusted:
                    trusted.append(origin)
                    changed = True
            if changed:
                settings.CSRF_TRUSTED_ORIGINS = trusted

        return self.get_response(request)


# Backwards-compatible alias so existing settings.py references keep working
# without forcing an env-var migration on people upgrading from v1.0.2.
DevLocalhostCsrfTrustedOriginsMiddleware = DynamicCsrfTrustedOriginsMiddleware


class DevForceUtf8CharsetMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if getattr(settings, "DEBUG", False):
            content_type = response.get("Content-Type", "")
            if content_type.startswith("text/") and "charset=" not in content_type.lower():
                response["Content-Type"] = (
                    f"{content_type}; charset=utf-8" if content_type else "text/html; charset=utf-8"
                )
        return response
