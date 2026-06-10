from .base import *
import dj_database_url
from decouple import config

DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

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

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
