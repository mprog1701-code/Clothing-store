from clothing_store.settings import *  # base settings
import os

# Core production flags
DEBUG = False
ENVIRONMENT = 'production'

# Hosts and security
ALLOWED_HOSTS = ['.onrender.com', 'onrender.com'] + ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
] + CSRF_TRUSTED_ORIGINS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES['staticfiles'] = {
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
}

# Database: expect DATABASE_URL from environment with SSL required
DATABASE_URL = os.environ.get('DATABASE_URL', DATABASE_URL)
if DATABASE_URL:
    if DATABASE_URL.lower().startswith('sqlite'):
        DATABASES = {
            'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=False)
        }
    else:
        DATABASES = {
            'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
        }

# Logging levels tuned for production
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['gunicorn.error']['level'] = 'INFO'
LOGGING['loggers']['gunicorn.access']['level'] = 'INFO'
