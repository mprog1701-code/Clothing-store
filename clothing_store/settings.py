"""
Django settings for clothing_store project.
"""

from pathlib import Path
from decimal import Decimal
from decouple import AutoConfig
from dotenv import load_dotenv
import os, sys
import dj_database_url
from django.contrib.messages import constants as messages

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
config = AutoConfig(search_path=BASE_DIR)

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

DEBUG = config('DEBUG', default=True, cast=bool)

_AH = config('ALLOWED_HOSTS', default='').strip()
_ENV_HOSTS = [h.strip() for h in _AH.split(',') if h.strip()]
_DEFAULT_HOSTS = [
    '127.0.0.1',
    'localhost',
    '.railway.app',
    '.up.railway.app',
    '.onrender.com',
    '.vercel.app',
]
# allow union of env + defaults to prevent DisallowedHost on cloud previews
ALLOWED_HOSTS = list(dict.fromkeys(_ENV_HOSTS + _DEFAULT_HOSTS))

INSTALLED_APPS = [
    'core',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'storages',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'clothing_store.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'clothing_store.wsgi.application'

DATABASE_URL = config('DATABASE_URL', default='').strip()
_IS_COLLECTSTATIC = any(arg.endswith('collectstatic') for arg in sys.argv)
if not DATABASE_URL:
    if _IS_COLLECTSTATIC:
        DATABASES = {}
    else:
        raise RuntimeError('DATABASE_URL is required and must be provided via environment. No SQLite or localhost fallback is allowed.')
else:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# خريطة مستويات الرسائل إلى فئات Bootstrap
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

LANGUAGE_CODE = 'ar'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Cloudflare R2 storage configuration
AWS_ACCESS_KEY_ID = config('R2_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = config('R2_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = config('R2_BUCKET_NAME', default='')
AWS_S3_ENDPOINT_URL = config('R2_ENDPOINT_URL', default='').strip()
AWS_S3_REGION_NAME = config('R2_REGION', default='auto')
AWS_QUERYSTRING_AUTH = False
AWS_S3_ADDRESSING_STYLE = 'path'
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_CUSTOM_DOMAIN = config('R2_PUBLIC_DOMAIN', default='')

def _valid_url(u):
    try:
        from urllib.parse import urlparse
        if not isinstance(u, str):
            return False
        p = urlparse(u.strip())
        return p.scheme in ('http', 'https') and bool(p.netloc)
    except Exception:
        return False

def _is_r2_api_endpoint(u):
    try:
        from urllib.parse import urlparse
        if not isinstance(u, str):
            return False
        p = urlparse(u.strip())
        if p.scheme not in ('http', 'https') or not p.netloc:
            return False
        host = p.netloc.lower()
        # Require Cloudflare R2 API host without bucket suffix
        if not host.endswith('.r2.cloudflarestorage.com'):
            return False
        # No bucket segment allowed in path
        path = (p.path or '').strip()
        return path in ('', '/')
    except Exception:
        return False

USE_R2 = all([
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_STORAGE_BUCKET_NAME,
    _is_r2_api_endpoint(AWS_S3_ENDPOINT_URL),
])

if USE_R2:
    STORAGES = {
        "default": {
            "BACKEND": "core.storage.R2MediaStorage",
        },
        "staticfiles": {
            "BACKEND": (
                "whitenoise.storage.CompressedManifestStaticFilesStorage"
                if not DEBUG else "django.contrib.staticfiles.storage.StaticFilesStorage"
            ),
        },
    }
    R2_PUBLIC_BASE_URL = config('R2_PUBLIC_BASE_URL', default='').strip()
    R2_PUBLIC_DOMAIN = config('R2_PUBLIC_DOMAIN', default='').strip()
    if R2_PUBLIC_DOMAIN:
        MEDIA_URL = f"https://{R2_PUBLIC_DOMAIN.strip('/')}/"
    elif _valid_url(R2_PUBLIC_BASE_URL):
        MEDIA_URL = R2_PUBLIC_BASE_URL.rstrip('/') + '/'
    else:
        MEDIA_URL = '/media/'
    print("USE_R2 =", USE_R2)
    print("MEDIA_URL =", MEDIA_URL)
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": (
                "whitenoise.storage.CompressedManifestStaticFilesStorage"
                if not DEBUG else "django.contrib.staticfiles.storage.StaticFilesStorage"
            ),
        },
    }
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

 

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# Feature flags (controlled via environment variables)
FEATURE_FLAGS = {
    'otp_verification': config('FEATURE_OTP_VERIFICATION', default=False, cast=bool),
    'fast_delivery': config('FEATURE_FAST_DELIVERY', default=False, cast=bool),
    'bank_transfer': config('FEATURE_BANK_TRANSFER', default=False, cast=bool),
    'card_payment': config('FEATURE_CARD_PAYMENT', default=False, cast=bool),
    'app_icon_customization': config('FEATURE_APP_ICON', default=False, cast=bool),
    'NEW_ARRIVALS_SECTION': config('FEATURE_NEW_ARRIVALS_SECTION', default=True, cast=bool),
    'ADS_SECTION': config('FEATURE_ADS_SECTION', default=True, cast=bool),
    'OWNER_DASHBOARD_REPORTS': config('FEATURE_OWNER_DASHBOARD_REPORTS', default=True, cast=bool),
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_ALL_ORIGINS = True

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Custom authentication backends
AUTHENTICATION_BACKENDS = [
    'core.backends.PhoneBackend',  # Custom phone authentication
    'django.contrib.auth.backends.ModelBackend',  # Default Django authentication
]

DELIVERY_FEE = Decimal('5000')  # 5000 IQD
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS_ENV = config('CSRF_TRUSTED_ORIGINS', default='')
if CSRF_TRUSTED_ORIGINS_ENV:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in CSRF_TRUSTED_ORIGINS_ENV.split(',') if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        'https://*.railway.app',
        'https://*.up.railway.app',
        'https://*.onrender.com',
        'https://*.vercel.app',
    ]
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0

try:
    from django.core.files.storage import default_storage
    print(f"[diagnostic] default_storage backend: {default_storage.__class__.__module__}.{default_storage.__class__.__name__}")
except Exception:
    pass

try:
    _db = DATABASES.get('default', {})
    _engine = _db.get('ENGINE') or ''
    _name = str(_db.get('NAME') or '')
    _host = str(_db.get('HOST') or '')
    _port = str(_db.get('PORT') or '')
    _url = (DATABASE_URL or '').strip()
    if not _host and _url:
        from urllib.parse import urlparse
        _p = urlparse(_url)
        _h = _p.netloc.split('@')[-1]
        _host = _h.split(':')[0]
        _name = ( _p.path or '' ).lstrip('/') or _name
    print(f"[diagnostic] db engine: {_engine}")
    print(f"[diagnostic] db name: {_name}")
    print(f"[diagnostic] db host: {_host}")
    print(f"[diagnostic] db port: {_port}")
    print(f"[diagnostic] has DATABASE_URL: {bool(_url)}")
except Exception:
    pass
