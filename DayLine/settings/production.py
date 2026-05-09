from .base import *
import os

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
    }
}

ALLOWED_HOSTS = [os.environ.get('ALLOWED_HOSTS')]

CSRF_TRUSTED_ORIGINS = [os.environ.get('CSRF_TRUSTED_ORIGINS')]