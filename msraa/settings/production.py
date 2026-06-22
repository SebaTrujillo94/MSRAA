from .base import *
import dj_database_url
from decouple import config

DEBUG = False
_hosts_env = [h.strip() for h in config('ALLOWED_HOSTS', default='').split(',') if h.strip()]
ALLOWED_HOSTS = _hosts_env or ['msraaproject.vercel.app', 'msraa.cl', 'www.msraa.cl']
ALLOWED_HOSTS += ['msraa.cl', 'www.msraa.cl', 'msraaproject.vercel.app', 'msraa.vercel.app', '.vercel.app']
ALLOWED_HOSTS = list(set(ALLOWED_HOSTS))

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True,
    )
}

# Cloudinary for media uploads (logos, portfolio images)
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
CLOUDINARY_STORAGE = {
    'CLOUDINARY_URL': config('CLOUDINARY_URL'),
}

# Use compressed (no manifest) storage — videos excluded from git break manifest
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CSRF_TRUSTED_ORIGINS = [
    'https://msraa.cl',
    'https://www.msraa.cl',
    'https://msraaproject.vercel.app',
    'https://msraa.vercel.app',
    'https://*.vercel.app',
]
