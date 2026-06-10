import sys
import os

# Add project root to path so Django can find the msraa package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'msraa.settings.production')

from django.core.wsgi import get_wsgi_application

# Vercel Python runtime requires the callable to be named `app`
app = get_wsgi_application()
