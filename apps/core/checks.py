import requests as req_lib
from django.conf import settings
from django.core.checks import Error, Tags, Warning, register


@register(Tags.security)
def check_secret_key(app_configs, **kwargs):
    errors = []
    key = settings.SECRET_KEY
    placeholder_values = [
        "your-secret-key-here",
        "changeme",
        "django-insecure",
        "secret",
        "",
    ]

    if len(key) < 50:
        errors.append(
            Error(
                "SECRET_KEY is too short (minimum 50 characters).",
                hint='Run: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"',
                id="moviechoose.E001",
            )
        )

    for placeholder in placeholder_values:
        if not placeholder:
            if key.strip() == "":
                errors.append(
                    Error(
                        "SECRET_KEY appears to be a placeholder value.",
                        hint="Generate a proper secret key before deploying.",
                        id="moviechoose.E002",
                    )
                )
                break
            continue
        if placeholder in key.lower():
            errors.append(
                Error(
                    "SECRET_KEY appears to be a placeholder value.",
                    hint="Generate a proper secret key before deploying.",
                    id="moviechoose.E002",
                )
            )
            break
    return errors


@register("configuration")
def check_tmdb_reachable(app_configs, **kwargs):
    warnings = []
    api_key = getattr(settings, "TMDB_API_KEY", "")
    if not api_key:
        return warnings
    try:
        r = req_lib.get(
            "https://api.themoviedb.org/3/configuration",
            params={"api_key": api_key},
            timeout=3,
        )
        if r.status_code != 200:
            warnings.append(
                Warning(
                    f"TMDB API returned {r.status_code}. Check your API key.",
                    id="moviechoose.W001",
                )
            )
    except Exception as e:
        warnings.append(
            Warning(
                f"TMDB API unreachable: {str(e)}. On PythonAnywhere free tier, whitelist api.themoviedb.org in your account settings.",
                id="moviechoose.W002",
            )
        )
    return warnings
