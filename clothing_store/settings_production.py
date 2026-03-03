from clothing_store.settings import *  # import base settings
import os

DEBUG = False
ENVIRONMENT = 'production'

ROOT_URLCONF = 'clothing_store.urls'
WSGI_APPLICATION = 'clothing_store.wsgi.application'

ALLOWED_HOSTS = ['.onrender.com', '.railway.app', '.up.railway.app'] + ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com', 'https://*.railway.app', 'https://*.up.railway.app'] + CSRF_TRUSTED_ORIGINS

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

STATIC_ROOT = BASE_DIR / 'staticfiles'
try:
    STORAGES['staticfiles']['BACKEND'] = "whitenoise.storage.CompressedManifestStaticFilesStorage"
except Exception:
    STORAGES = STORAGES if isinstance(STORAGES, dict) else {}
    STORAGES['staticfiles'] = {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}

DATABASE_URL = os.environ.get('DATABASE_URL', DATABASE_URL)
if DATABASE_URL:
    if DATABASE_URL.lower().startswith('sqlite'):
        DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=False)}
    else:
        DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)}

try:
    LOGGING['loggers']['django']['level'] = 'WARNING'
    LOGGING['loggers']['gunicorn.error']['level'] = 'INFO'
    LOGGING['loggers']['gunicorn.access']['level'] = 'INFO'
except Exception:
    pass
