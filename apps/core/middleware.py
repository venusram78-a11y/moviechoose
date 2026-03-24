import base64
import secrets


class CustomSecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        nonce = base64.b64encode(secrets.token_bytes(16)).decode()
        request.csp_nonce = nonce
        response = self.get_response(request)
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' https://image.tmdb.org "
            "https://www.themoviedb.org data:; "
            f"script-src 'self' 'nonce-{nonce}' "
            "https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net "
            "https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self'; "
            "manifest-src 'self'; "
            "frame-ancestors 'none';"
        )
        return response
