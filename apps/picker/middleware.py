from apps.picker.throttle import PickRateThrottle


class PickThrottleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.throttle = PickRateThrottle()

    def __call__(self, request):
        throttled = self.throttle(request)
        if throttled is not None:
            return throttled
        return self.get_response(request)
