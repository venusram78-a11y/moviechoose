from django.conf import settings
from apps.analytics.models import GlobalCounter


def global_counters(request):
    return {"total_picks": GlobalCounter.get_value("total_picks")}


def canonical_base(request):
    return {
        "CANONICAL_BASE": getattr(settings, "CANONICAL_BASE_URL", "https://moviechoose.com"),
        "GOOGLE_SITE_VERIFICATION": getattr(settings, "GOOGLE_SITE_VERIFICATION", ""),
    }


def csp_nonce(request):
    return {"CSP_NONCE": getattr(request, "csp_nonce", "")}
