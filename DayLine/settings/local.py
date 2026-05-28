from .base import *

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'nongarrulous-antone-overrighteous.ngrok-free.dev',
]

CSRF_TRUSTED_ORIGINS = [
    'https://nongarrulous-antone-overrighteous.ngrok-free.dev',
]

# ローカルではS3を使わない
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'storages']

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'