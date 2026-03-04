
import os
import sys
from django.core.wsgi import get_wsgi_application

# Diagnostic: Print settings module and path
print("WSGI: Starting application loading...")
print(f"WSGI: Initial DJANGO_SETTINGS_MODULE = {os.environ.get('DJANGO_SETTINGS_MODULE')}")

# Explicitly FORCE the settings module for Railway
# This overwrites any existing environment variable to ensure we use the correct file.
os.environ["DJANGO_SETTINGS_MODULE"] = "clothing_store.settings_railway"

print(f"WSGI: Forced DJANGO_SETTINGS_MODULE = {os.environ.get('DJANGO_SETTINGS_MODULE')}")

application = get_wsgi_application()
