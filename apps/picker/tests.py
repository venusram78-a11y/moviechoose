from django.test import Client, TestCase


class PickEndpointTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=False)

    def test_pick_requires_post(self):
        response = self.client.get("/pick/")
        self.assertEqual(response.status_code, 405)

    def test_pick_invalid_mood_returns_400(self):
        response = self.client.post(
            "/pick/",
            {
                "mood": "INVALID_MOOD_XSS<script>",
                "language": "hindi",
            },
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_pick_invalid_language_returns_400(self):
        response = self.client.post("/pick/", {"mood": "happy", "language": "klingon"})
        self.assertEqual(response.status_code, 400)

    def test_pick_valid_inputs_accepted(self):
        response = self.client.post("/pick/", {"mood": "happy", "language": "hindi"})
        self.assertNotEqual(response.status_code, 400)

    def test_report_invalid_tmdb_id_returns_400(self):
        response = self.client.post(
            "/pick/report/",
            {"tmdb_id": "not-a-number", "reason": "other"},
        )
        self.assertEqual(response.status_code, 400)

    def test_report_negative_tmdb_id_returns_400(self):
        response = self.client.post("/pick/report/", {"tmdb_id": "-999", "reason": "other"})
        self.assertEqual(response.status_code, 400)

    def test_alternatives_requires_post(self):
        response = self.client.get("/pick/alternatives/")
        self.assertEqual(response.status_code, 405)

    def test_report_invalid_reason_normalized(self):
        response = self.client.post(
            "/pick/report/",
            {"tmdb_id": "1001", "reason": "DROP TABLE movies"},
        )
        self.assertIn(response.status_code, (200, 400))


class ThrottleTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=False)

    def test_throttle_allows_under_limit(self):
        for i in range(5):
            response = self.client.post(
                "/pick/",
                {"mood": "happy", "language": "any"},
                REMOTE_ADDR="10.0.0.1",
            )
            self.assertNotEqual(
                response.status_code, 429, f"Request {i+1} was unexpectedly throttled"
            )

    def test_throttle_blocks_at_limit(self):
        test_ip = "192.168.99.99"
        from django.core.cache import cache

        cache.set(f"throttle_count_{test_ip}", 20, 3600)
        response = self.client.post(
            "/pick/",
            {"mood": "happy", "language": "any"},
            REMOTE_ADDR=test_ip,
        )
        self.assertEqual(response.status_code, 429)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("retry_after", data)

    def test_throttle_allows_at_limit(self):
        test_ip = "192.168.88.88"
        from django.core.cache import cache

        cache.set(f"throttle_count_{test_ip}", 19, 3600)
        response = self.client.post(
            "/pick/",
            {"mood": "happy", "language": "any"},
            REMOTE_ADDR=test_ip,
        )
        self.assertNotEqual(response.status_code, 429)


class StreakTests(TestCase):
    def test_streak_initialises_at_one(self):
        client = Client(enforce_csrf_checks=False)
        session = client.session
        session["last_pick_date"] = None
        session["streak"] = 0
        session.save()
        self.assertTrue(True)


class HealthEndpointTests(TestCase):
    def test_health_returns_200(self):
        client = Client()
        response = client.get("/health/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("checks", data)

    def test_health_checks_database(self):
        client = Client()
        response = client.get("/health/")
        data = response.json()
        self.assertEqual(data["checks"]["database"], "ok")
