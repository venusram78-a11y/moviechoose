from django.test import Client, TestCase


class CorePageTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_homepage_returns_200(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_about_returns_200(self):
        response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)

    def test_privacy_returns_200(self):
        response = self.client.get("/privacy/")
        self.assertEqual(response.status_code, 200)

    def test_terms_returns_200(self):
        response = self.client.get("/terms/")
        self.assertEqual(response.status_code, 200)

    def test_robots_txt_returns_200(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User-agent")

    def test_sitemap_returns_200(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<urlset")

    def test_health_returns_200(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)

    def test_404_returns_branded_page(self):
        response = self.client.get("/this-page-does-not-exist-at-all/")
        self.assertEqual(response.status_code, 404)
        self.assertNotContains(
            response, "Django tried these URL patterns", status_code=404
        )

    def test_consent_accepted_saves_to_session(self):
        response = self.client.post("/consent/", {"consent": "accepted"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get("dpdp_consent"), "accepted")

    def test_consent_declined_saves_to_session(self):
        response = self.client.post("/consent/", {"consent": "declined"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get("dpdp_consent"), "declined")

    def test_consent_invalid_value_returns_400(self):
        response = self.client.post("/consent/", {"consent": "maybe"})
        self.assertEqual(response.status_code, 400)
