from django.core.cache import cache
from django.http import JsonResponse


class PickRateThrottle:
    """
    IP-based rate limit: 20 requests per hour to /pick/ endpoint.
    Uses Django DB cache backend. No Redis needed.
    PythonAnywhere compatible.
    """

    RATE = 20
    WINDOW = 3600
    THROTTLED_PATHS = {"/pick/", "/pick/alternatives/"}

    def __call__(self, request):
        if request.path not in self.THROTTLED_PATHS:
            return None
        if request.method != "POST":
            return None

        ip = self._get_ip(request)
        counter_key = f"throttle_count_{ip}"
        cache.add(counter_key, 0, self.WINDOW)
        count = cache.incr(counter_key)
        if count > self.RATE:
            return JsonResponse(
                {
                    "error": "Too many picks. Please wait before trying again.",
                    "retry_after": 60,
                },
                status=429,
            )

        return None

    def _get_ip(self, request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "0.0.0.0")
