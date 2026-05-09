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