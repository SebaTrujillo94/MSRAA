from .base import *
import dj_database_url
import os
from pathlib import Path

# Load .env file if present
_env_path = Path(__file__).resolve().parent.parent.parent / '.env'
if _env_path.exists():
    for _line in _env_path.read_text(encoding='utf-8').splitlines():
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _k, _v = _line.split('=', 1)
            os.environ.setdefault(_k.strip(), _v.strip())

DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600,
    )
}

# Use local filesystem for media in development
STORAGES = {**STORAGES, 'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'}}
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configure Cloudinary SDK for API calls (usage stats) even in dev
_cloudinary_url = os.environ.get('CLOUDINARY_URL', '')
if _cloudinary_url:
    import cloudinary
    import re
    _m = re.match(r'cloudinary://(\d+):([^@]+)@(.+)', _cloudinary_url)
    if _m:
        cloudinary.config(api_key=_m.group(1), api_secret=_m.group(2), cloud_name=_m.group(3))

# Use console email backend in development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
