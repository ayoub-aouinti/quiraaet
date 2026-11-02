import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-only-change-me')
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'
ALLOWED_HOSTS = [h for h in os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h]
CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if o]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'qiraat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

# PostgreSQL uniquement (JSONB). DATABASE_URL=postgres://user:pass@host:5432/db
DATABASES = {'default': dj_database_url.config(
    default='postgres://qiraat:qiraat@localhost:5440/qiraat', conn_max_age=60)}  # = docker-compose.yml (db)

LANGUAGE_CODE = 'ar'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Sortie du pipeline Python (build_app_data.py & co) : data/** et fonts/*
DATA_DIR = Path(os.environ.get('QIRAAT_DATA_DIR', REPO_DIR / 'data'))
FONTS_DIR = Path(os.environ.get('QIRAAT_FONTS_DIR', REPO_DIR / 'fonts'))
# SPA React compilée (frontend/dist), servie par Django en production
FRONTEND_DIST = Path(os.environ.get('QIRAAT_FRONTEND_DIST', REPO_DIR / 'frontend' / 'dist'))
