"""Django settings for the Demo DJ project.

Generated by 'django-admin startproject' using Django 4.2.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from ast import literal_eval
from os import getenv
from pathlib import Path

ALLOWEDFLARE_ACCESS_URL = getenv('ALLOWEDFLARE_ACCESS_URL', 'off')
ALLOWEDFLARE_AUDIENCE = getenv('ALLOWEDFLARE_AUDIENCE', '')
ALLOWEDFLARE_PRIVATE_DOMAIN = getenv('ALLOWEDFLARE_PRIVATE_DOMAIN', '')

if ALLOWEDFLARE_PRIVATE_DOMAIN:
    ALLOWED_HOSTS = (f'.{ALLOWEDFLARE_PRIVATE_DOMAIN}', 'localhost')
    CSRF_TRUSTED_ORIGINS = (f'https://*.{ALLOWEDFLARE_PRIVATE_DOMAIN}',)

BASE_DIR = Path(__file__).resolve().parent.parent

# Use a real secret key and set DEBUG to False in production
DEBUG = bool(literal_eval(getenv('DEMODJ_DEBUG', 'True')))
SECRET_KEY = getenv(
    'DEMODJ_SECRET_KEY', 'django-insecure-+u()*ykdn+20wd88=-ou3)c7#h)-psb5w80)z=jr&&&wr)9)0z'
)
# "When DEBUG is True and ALLOWED_HOSTS is empty, the host is validated against
# ['.localhost', '127.0.0.1', '[::1]']."
# https://docs.djangoproject.com/en/4.2/ref/settings/#allowed-hosts

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'explorer',
    'health_check',
    'health_check.db',
    'health_check.contrib.migrations',
    'rest_framework',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allowedflare.django.Backend',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('allowedflare.django.Authentication',),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'PAGE_SIZE': 10,
}

ROOT_URLCONF = 'demodj.urls'

TEMPLATES = [
    {  # To avoid admin.E403, configure Django templates
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['allowedflare'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ]
        },
    }
]

WSGI_APPLICATION = 'demodj.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
EXPLORER_CONNECTIONS = {'Demo DJ': 'default'}
EXPLORER_DEFAULT_CONNECTION = 'default'
EXPLORER_NO_PERMISSION_VIEW = 'allowedflare.django.login_view_wrapper'


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOG_LEVEL = getenv('DEMODJ_LOG_LEVEL', 'DEBUG' if DEBUG else 'INFO')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': LOG_LEVEL},
}

SHELL_PLUS = 'lab'
SHELL_PLUS_PRINT_SQL = True
SHELL_PLUS_PRINT_SQL_TRUNCATE = 5000
