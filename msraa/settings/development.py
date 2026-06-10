from .base import *
import dj_database_url

DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600,
    )
}

# Use local filesystem for media in development
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Use console email backend in development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
