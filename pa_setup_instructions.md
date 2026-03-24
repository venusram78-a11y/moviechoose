# PythonAnywhere setup for MovieChoose

## Step 0 - Whitelist external URLs (do this first)

Before uploading any code, do this on PythonAnywhere free tier:
1. Log into pythonanywhere.com.
2. Go to Account -> API Token (or Dashboard -> Whitelist).
3. In Allowed external URLs / Allowlisted domains, add:
   - `api.themoviedb.org`
   - `image.tmdb.org`
   - `www.themoviedb.org`
4. Save and wait 60 seconds for propagation.
5. Test from PythonAnywhere Bash:
   - `python -c "import requests; r=requests.get('https://api.themoviedb.org/3/configuration', params={'api_key':'YOUR_TMDB_KEY'}, timeout=5); print(r.status_code)"`
   - Must print `200`.

Note: paid PythonAnywhere plans do not require outbound whitelist setup.

## Initial deployment

1. Create PythonAnywhere account.
2. Open Bash console and clone repository.
3. Create and activate virtualenv:
   - `mkvirtualenv moviechoose --python=python3.11`
4. Install dependencies:
   - `pip install -r requirements.txt`
5. Create `.env` from `.env.example`.
6. Generate admin URL:
   - `python -c "import secrets; print(secrets.token_hex(8) + '-panel/')"`
   - Set output as `ADMIN_URL` in `.env`.
   - Never use a predictable admin path.
7. Run setup commands:
   - `python manage.py create_cache_table`
   - `python manage.py migrate`
   - `python manage.py init_counters`
   - `python manage.py seed_movies`
   - `python manage.py download_assets`
   - `python manage.py collectstatic --noinput`
8. Configure WSGI file `/var/www/yourusername_pythonanywhere_com_wsgi.py`:
   - `import os, sys`
   - `path = '/home/yourusername/moviechoose'`
   - `if path not in sys.path: sys.path.append(path)`
   - `os.environ['DJANGO_SETTINGS_MODULE'] = 'moviechoose.settings.production'`
   - `from django.core.wsgi import get_wsgi_application`
   - `application = get_wsgi_application()`
9. Static mapping in PythonAnywhere dashboard:
   - URL `/static/` -> `/home/yourusername/moviechoose/staticfiles`
10. Reload web app.

## Generating frozen requirements (on PythonAnywhere)

1. After successful `pip install -r requirements.txt` on PythonAnywhere:
   - `pip freeze > requirements_frozen_linux.txt`
2. Download `requirements_frozen_linux.txt` from PythonAnywhere Files.
3. Commit that Linux-generated file into repo for exact Linux pins.

Do not use frozen files generated on Windows for PythonAnywhere Linux installs.

## Post-fix deployment steps

1. `pip install -r requirements.txt`
2. `python manage.py migrate`
3. `python manage.py collectstatic --noinput`
4. `python manage.py check`
5. `python smoke_test.py http://yourusername.pythonanywhere.com`
6. Reload web app
7. `python manage.py warm_cache` after every git pull + reload
8. `python manage.py download_assets` after pulls if TMDB logo missing

If favicon is missing after first deploy:
- `python manage.py generate_favicon`
- `python manage.py collectstatic --noinput`
- Reload app.

## Google Search Console verification

After deployment:
1. Go to <https://search.google.com/search-console>.
2. Add property -> URL prefix -> `https://moviechoose.com`.
3. Choose HTML tag verification.
4. Copy `content=` value to `.env` as `GOOGLE_SITE_VERIFICATION=`.
5. Pull latest code and reload app.

## Uptime monitoring (free - 5 minutes setup)

1. Go to <https://uptimerobot.com> and sign up.
2. Add monitor:
   - Type: HTTP(s)
   - Name: MovieChoose Health
   - URL: `https://moviechoose.com/health/`
   - Interval: 5 minutes
3. Add alert contact email.

Why:
- Free-tier apps sleep on inactivity.
- 5-minute pings keep app warm and alert you quickly.

## Custom domain setup - moviechoose.com on PythonAnywhere

Important: custom domains require paid PythonAnywhere plan.
Free plan supports only `yourusername.pythonanywhere.com`.

Option A (recommended launch):
1. Upgrade to paid plan.
2. Web tab -> Add new web app -> `moviechoose.com`.
3. Copy PythonAnywhere CNAME target.
4. In registrar DNS:
   - `www` CNAME -> PythonAnywhere target
   - root `@` redirect or A/ALIAS to `www.moviechoose.com`
5. Wait for DNS propagation (0-48h).
6. Enable HTTPS in PythonAnywhere and Let’s Encrypt auto-renew.
7. Set `.env`:
   - `CANONICAL_BASE_URL=https://moviechoose.com`
   - `ALLOWED_HOSTS=moviechoose.com,www.moviechoose.com`
8. Pull, collectstatic, reload, and smoke test.

## Weekly backup routine

1. Open PythonAnywhere Bash.
2. Run:
   - `cd ~/moviechoose && python manage.py backup_db`
3. Download latest backup from `~/moviechoose/backups/`.
4. Keep at least 4 weekly local backups.
5. Set a weekly reminder (PythonAnywhere does not auto-backup your project DB).
