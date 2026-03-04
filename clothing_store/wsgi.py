
import os
import sys
from django.core.wsgi import get_wsgi_application

# Diagnostic: Print settings module and path
print("WSGI: Starting application loading...")
print(f"WSGI: Initial DJANGO_SETTINGS_MODULE = {os.environ.get('DJANGO_SETTINGS_MODULE')}")
print(f"WSGI: PYTHONPATH = {sys.path}")

# Explicitly set the settings module for Railway
# We use 'setdefault' so it can still be overridden by env var if needed, 
# but the Procfile will also enforce it.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "clothing_store.settings_railway")

print(f"WSGI: Final DJANGO_SETTINGS_MODULE = {os.environ.get('DJANGO_SETTINGS_MODULE')}")

application = get_wsgi_application()
