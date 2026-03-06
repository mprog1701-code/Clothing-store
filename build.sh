#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Collect static files - تجاهل الأخطاء
export DJANGO_SETTINGS_MODULE=clothing_store.settings_railway
python manage.py collectstatic --no-input --clear || true

# Migrate database
python manage.py migrate --noinput

# Create superuser
python create_superuser.py || true
