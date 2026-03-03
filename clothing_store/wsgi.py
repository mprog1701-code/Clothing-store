"""
WSGI config for clothing_store project.
"""

import os

from django.core.wsgi import get_wsgi_application

module = os.environ.get('DJANGO_SETTINGS_MODULE') or ''
if not module:
    # Prefer production settings on cloud platforms (Render/Railway) by default
    if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RENDER'):
        module = 'clothing_store.settings_production'
    else:
        module = 'clothing_store.settings'
else:
    # If referencing the removed module clothing_store.settings.production, fallback
    if module.strip() == 'clothing_store.settings.production':
        module = 'clothing_store.settings_production'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', module)

try:
    application = get_wsgi_application()
except Exception:
    # Final safe fallback
    os.environ['DJANGO_SETTINGS_MODULE'] = 'clothing_store.settings'
    application = get_wsgi_application()
