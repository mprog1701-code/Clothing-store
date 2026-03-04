"""
WSGI config for clothing_store project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys
from django.core.wsgi import get_wsgi_application

# Debugging: Print settings module and path
print(f"WSGI: Loading application...")
print(f"WSGI: Current DJANGO_SETTINGS_MODULE={os.environ.get('DJANGO_SETTINGS_MODULE')}")
print(f"WSGI: PYTHONPATH={sys.path}")

# Force correct settings module if it's set to a missing file
current_settings = os.environ.get('DJANGO_SETTINGS_MODULE')
if current_settings == 'clothing_store.settings.production':
    print("WSGI: Detected deprecated settings module. Forcing 'clothing_store.settings'.")
    os.environ['DJANGO_SETTINGS_MODULE'] = 'clothing_store.settings'
elif not current_settings:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clothing_store.settings')

try:
    from django.conf import settings
    if not settings.configured:
        import django
        django.setup()
    print(f"WSGI: Settings configured. ROOT_URLCONF={getattr(settings, 'ROOT_URLCONF', 'MISSING')}")
except Exception as e:
    print(f"WSGI: Error loading settings: {e}")
    # Last resort fallback
    os.environ['DJANGO_SETTINGS_MODULE'] = 'clothing_store.settings'

application = get_wsgi_application()