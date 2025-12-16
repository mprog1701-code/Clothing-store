"""
Django settings for clothing_store project.
"""

from pathlib import Path
from decimal import Decimal
from decouple import config
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='127.0.0.1,localhost,.railway.app,.up.railway.app,.onrender.com,.vercel.app'
).split(',')

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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DATABASE_URL = config('DATABASE_URL', default='')
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)

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
AWS_S3_ENDPOINT_URL = config('R2_ENDPOINT_URL', default='')
AWS_S3_REGION_NAME = config('R2_REGION', default='auto')
AWS_QUERYSTRING_AUTH = False
AWS_S3_ADDRESSING_STYLE = 'path'
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_CUSTOM_DOMAIN = config('R2_PUBLIC_DOMAIN', default='')

STORAGES = {
    "default": {
        "BACKEND": "core.storage.R2MediaStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

R2_PUBLIC_BASE_URL = config('R2_PUBLIC_BASE_URL', default='')
if AWS_S3_CUSTOM_DOMAIN:
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN.strip('/')}/"
elif R2_PUBLIC_BASE_URL:
    MEDIA_URL = R2_PUBLIC_BASE_URL.rstrip('/') + '/'
elif AWS_S3_ENDPOINT_URL and AWS_STORAGE_BUCKET_NAME:
    MEDIA_URL = AWS_S3_ENDPOINT_URL.rstrip('/') + '/' + AWS_STORAGE_BUCKET_NAME.strip('/') + '/'
else:
    MEDIA_URL = '/media/'

 

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

DELIVERY_FEE = Decimal('50.00')  # 50 SAR
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
