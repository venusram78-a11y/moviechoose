"""
MovieChoose Production Smoke Test
Run before every deployment: python smoke_test.py https://moviechoose.com
"""
import sys

import requests

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"

TESTS = [
    ("GET", "/", 200, "Homepage"),
    ("GET", "/about/", 200, "About page"),
    ("GET", "/privacy/", 200, "Privacy Policy"),
    ("GET", "/terms/", 200, "Terms of Service"),
    ("GET", "/health/", 200, "Health check"),
    ("GET", "/robots.txt", 200, "robots.txt"),
    ("GET", "/sitemap.xml", 200, "sitemap.xml"),
    ("POST", "/pick/", 400, "Pick - no data = 400"),
    ("GET", "/static/css/main.css", 200, "Static CSS"),
    ("GET", "/static/images/favicon.ico", 200, "Favicon"),
]

passed = 0
failed = 0


def post_with_csrf(path, data=None, timeout=10):
    session = requests.Session()
    session.get(BASE_URL + "/", timeout=timeout)
    csrf = session.cookies.get("csrftoken", "")
    headers = {"X-CSRFToken": csrf} if csrf else {}
    return session.post(BASE_URL + path, timeout=timeout, headers=headers, data=data or {})

print(f"\nMovieChoose Smoke Test - {BASE_URL}\n{'='*50}")

for method, path, expected_status, label in TESTS:
    url = BASE_URL + path
    try:
        if method == "GET":
            r = requests.get(url, timeout=10, allow_redirects=True)
        else:
            r = post_with_csrf(path, {})

        status = "PASS" if r.status_code == expected_status else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1

        symbol = "OK" if status == "PASS" else "XX"
        print(f"  {symbol} [{r.status_code}] {label} - {path}")
    except Exception as e:
        failed += 1
        print(f"  XX [ERR] {label} - {path} - {str(e)}")

print(f"\n{'='*50}")
print("\n--- Security Header Verification ---")
r = requests.get(BASE_URL + "/", timeout=10)
required_headers = [
    "Content-Security-Policy",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
]
for header in required_headers:
    present = header in r.headers
    status = "PASS" if present else "FAIL"
    if not present:
        failed += 1
    else:
        passed += 1
    symbol = "OK" if present else "XX"
    print(f"  {symbol} [{status}] Header: {header}")

print("\n--- Pick Endpoint Quality Tests ---")
try:
    r = post_with_csrf("/pick/", data={"mood": "happy", "language": "hindi"}, timeout=15)
    if r.status_code == 200:
        data = r.json()
        required_fields = ["title", "poster_url", "overview", "watch_links"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            print(f"  XX [FAIL] Pick response missing fields: {missing}")
            failed += 1
        else:
            print(f"  OK [PASS] Pick returns valid movie: {data.get('title', '?')}")
            passed += 1
    elif r.status_code == 404:
        print("  WARN [WARN] Pick returned 404 - seed_movies may not be loaded")
    else:
        print(f"  XX [FAIL] Pick returned {r.status_code}")
        failed += 1
except Exception as e:
    print(f"  XX [ERR] Pick quality test failed: {e}")
    failed += 1

try:
    r = post_with_csrf(
        "/pick/",
        data={"mood": "INVALID<script>alert(1)</script>", "language": "hindi"},
        timeout=5,
    )
    if r.status_code == 400:
        print("  OK [PASS] Invalid mood correctly rejected (400)")
        passed += 1
    else:
        print(f"  XX [FAIL] Invalid mood returned {r.status_code} not 400")
        failed += 1
except Exception as e:
    print(f"  XX [ERR] Validation test failed: {e}")
    failed += 1

try:
    r = post_with_csrf(
        "/pick/alternatives/",
        data={"mood": "happy", "language": "any"},
        timeout=15,
    )
    if r.status_code == 200:
        data = r.json()
        alts = data.get("alternatives", [])
        if len(alts) >= 1:
            print(f"  OK [PASS] Alternatives returns {len(alts)} films")
            passed += 1
        else:
            print("  WARN [WARN] Alternatives returned 0 films")
    else:
        print(f"  XX [FAIL] Alternatives returned {r.status_code}")
        failed += 1
except Exception as e:
    print(f"  XX [ERR] Alternatives test failed: {e}")
    failed += 1

print("\n--- Asset Tests ---")
try:
    r = requests.get(BASE_URL + "/static/images/favicon.ico", timeout=5)
    status = "PASS" if r.status_code == 200 else "FAIL"
    if r.status_code == 200:
        passed += 1
    else:
        failed += 1
    sym = "OK" if r.status_code == 200 else "XX"
    print(f"  {sym} [{r.status_code}] Favicon")
except Exception as e:
    failed += 1
    print(f"  XX [ERR] Favicon - {e}")

print("\n--- Legal Compliance Tests ---")
try:
    r = requests.get(BASE_URL + "/", timeout=10)
    has_tmdb = "themoviedb" in r.text.lower()
    has_amazon = "amazon associate" in r.text.lower()
    status = "PASS" if has_tmdb else "FAIL"
    if has_tmdb:
        passed += 1
    else:
        failed += 1
    sym = "OK" if has_tmdb else "XX"
    print(f"  {sym} [{status}] TMDB attribution on homepage")
    status = "PASS" if has_amazon else "FAIL"
    if has_amazon:
        passed += 1
    else:
        failed += 1
    sym = "OK" if has_amazon else "XX"
    print(f"  {sym} [{status}] Amazon disclosure on homepage")
except Exception as e:
    failed += 2
    print(f"  XX [ERR] Legal compliance checks failed: {e}")

try:
    r = requests.get(BASE_URL + "/privacy/", timeout=5)
    has_phrase = "as an amazon associate" in r.text.lower()
    status = "PASS" if has_phrase else "FAIL"
    if has_phrase:
        passed += 1
    else:
        failed += 1
    sym = "OK" if has_phrase else "XX"
    print(f"  {sym} [{status}] Amazon phrase in Privacy Policy")
except Exception as e:
    failed += 1
    print(f"  XX [ERR] Privacy policy check: {e}")

print("\n--- DPDP Compliance Tests ---")
try:
    r = requests.post(BASE_URL + "/consent/", data={"consent": "accepted"}, timeout=5)
    status = "PASS" if r.status_code == 200 else "FAIL"
    if r.status_code == 200:
        passed += 1
    else:
        failed += 1
    sym = "OK" if r.status_code == 200 else "XX"
    print(f"  {sym} [{r.status_code}] Consent endpoint accepts 'accepted'")
except Exception as e:
    failed += 1
    print(f"  XX [ERR] Consent endpoint: {e}")

print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed")
print("READY TO LAUNCH" if failed == 0 else "FIX FAILURES BEFORE LAUNCH")
sys.exit(0 if failed == 0 else 1)
