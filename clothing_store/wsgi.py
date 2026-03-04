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

# Force correct settings module
current_settings = os.environ.get('DJANGO_SETTINGS_MODULE')
if current_settings == 'clothing_store.settings.production':
    # If production settings is requested but file might be missing or causing issues,
    # try to use the newly created one or fallback to standard settings
    if os.path.exists(os.path.join(os.path.dirname(__file__), 'settings_production.py')):
        print("WSGI: Using clothing_store.settings_production")
        os.environ['DJANGO_SETTINGS_MODULE'] = 'clothing_store.settings_production'
    else:
        print("WSGI: settings_production.py not found. Forcing 'clothing_store.settings'.")
        os.environ['DJANGO_SETTINGS_MODULE'] = 'clothing_store.settings'
elif not current_settings:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clothing_store.settings')

try:
    from django.conf import settings
    if not settings.configured:
        import django
        django.setup()
    
    # Log which settings file is actually used (if possible)
    try:
        settings_module = sys.modules.get(os.environ.get('DJANGO_SETTINGS_MODULE'))
        settings_file = getattr(settings_module, '__file__', 'unknown')
        print(f"WSGI: Actual settings file: {settings_file}")
    except Exception:
        pass
        
    print(f"WSGI: Settings configured. ROOT_URLCONF={getattr(settings, 'ROOT_URLCONF', 'MISSING')}")
except Exception as e:
    print(f"WSGI: Error loading settings: {e}")
    # Last resort fallback
    if os.path.exists(os.path.join(os.path.dirname(__file__), 'settings_production.py')):
         os.environ['DJANGO_SETTINGS_MODULE'] = 'clothing_store.settings_production'
    else:
         os.environ['DJANGO_SETTINGS_MODULE'] = 'clothing_store.settings'

application = get_wsgi_application()