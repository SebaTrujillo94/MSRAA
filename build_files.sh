#!/bin/bash
set -e
pip install -r requirements.txt --break-system-packages
pip install groq --break-system-packages
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py auto_translate || echo "auto_translate skipped (no GROQ_API_KEY or already done)"
