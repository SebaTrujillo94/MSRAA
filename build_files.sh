#!/bin/bash
set -e
pip install -r requirements.txt --break-system-packages
pip install groq --break-system-packages
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py auto_translate || echo "auto_translate skipped (no GROQ_API_KEY or already done)"
python manage.py createsuperuser --noinput || echo "superuser already exists"
python manage.py seed_data --force || echo "seed_data skipped"
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
U = get_user_model()
u = U.objects.filter(username=os.environ.get('DJANGO_SUPERUSER_USERNAME','admin')).first()
if u and os.environ.get('DJANGO_SUPERUSER_PASSWORD'):
    u.set_password(os.environ['DJANGO_SUPERUSER_PASSWORD'])
    u.save()
    print('password updated')
" || echo "password update skipped"
