"""
ASGI config for clothing_store project.
"""

import os

from django.core.asgi import get_asgi_application

# Default to settings_dev for local development if not set
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clothing_store.settings_dev')

application = get_asgi_application()
