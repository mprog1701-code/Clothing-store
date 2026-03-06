#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

echo "=== BUILD SCRIPT STARTED ==="

# Collect static files - تجاهل الأخطاء
export DJANGO_SETTINGS_MODULE=clothing_store.settings_railway
python manage.py collectstatic --no-input --clear || true

# Migrate database
echo "=== RUNNING MIGRATIONS ==="
python manage.py migrate --noinput

# Create superuser with detailed logging
echo "=== RUNNING SUPERUSER CREATION ==="
python manage.py create_owner

echo "=== BUILD COMPLETED ==="
