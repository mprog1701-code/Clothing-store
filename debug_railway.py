import os
import sys

print("Environment diagnostics")
print("Python", sys.version)

try:
    import django
    print("✓ Django imported successfully")
except Exception as e:
    print(f"✗ Django import error: {e}")

module = os.environ.get('DJANGO_SETTINGS_MODULE') or ''
if not module:
    if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RENDER'):
        module = 'clothing_store.settings_production'
    else:
        module = 'clothing_store.settings'
elif module.strip() == 'clothing_store.settings.production':
    module = 'clothing_store.settings_production'
os.environ['DJANGO_SETTINGS_MODULE'] = module
print("DJANGO_SETTINGS_MODULE =", module)

try:
    django.setup()
    print("✓ Django setup successful")
except Exception as e:
    print(f"✗ Django setup error: {e}")
    print(f"Error details: {sys.exc_info()}")

try:
    from django.db import connection
    connection.ensure_connection()
    print("✓ Database connection successful")
except Exception as e:
    print(f"✗ Database error: {e}")

try:
    from django.urls import get_resolver
    resolver = get_resolver()
    patterns = resolver.url_patterns or []
    print(f"✓ URLs loaded: {len(patterns)} patterns")
except Exception as e:
    print(f"✗ URL error: {e}")

print("\nEnvironment variables:")
for key in ['SECRET_KEY', 'DEBUG', 'ALLOWED_HOSTS', 'DATABASE_URL', 'RAILWAY_ENVIRONMENT']:
    value = os.getenv(key, 'NOT SET')
    if key == 'SECRET_KEY' and value != 'NOT SET':
        value = value[:10] + '...'
    print(f"  {key}: {value}")
